from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import ProtectedError

from .models import (
    AccountSubject,
    Category,
    Customer,
    InventoryBatch,
    JournalVoucher,
    JournalVoucherItem,
    Order,
    OrderItem,
    Product,
    PurchaseApplyItem,
    PurchaseOrder,
    StocktakeCount,
    Supplier,
)
from .serializers import (
    AccountSubjectSerializer,
    CategorySerializer,
    CustomerSerializer,
    InventoryBatchSerializer,
    JournalVoucherItemSerializer,
    JournalVoucherSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ProductSerializer,
    PurchaseApplyItemSerializer,
    PurchaseOrderSerializer,
    StocktakeCountSerializer,
    SupplierSerializer,
    UserRegisterSerializer,
)
from django.contrib.auth.models import User
from django.db.models import IntegerField
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CustomerSerializer, SupplierSerializer, UserRegisterSerializer
from .services import complete_order, create_inventory_from_purchase


class AccountSubjectViewSet(viewsets.ModelViewSet):
    queryset = AccountSubject.objects.all()
    serializer_class = AccountSubjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']


class JournalVoucherViewSet(viewsets.ModelViewSet):
    queryset = JournalVoucher.objects.all()
    serializer_class = JournalVoucherSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'date': ['gte', 'lte', 'year'],
    }


class JournalVoucherItemViewSet(viewsets.ModelViewSet):
    queryset = JournalVoucherItem.objects.all()
    serializer_class = JournalVoucherItemSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().select_related('parent')
    serializer_class = CategorySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        parent_param = self.request.query_params.get('parent')
        if parent_param is not None:
            if parent_param in ('null', 'none', ''):
                qs = qs.filter(parent__isnull=True)
            else:
                try:
                    qs = qs.filter(parent_id=int(parent_param))
                except (TypeError, ValueError):
                    qs = qs.none()
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Reject if there are children
        if instance.children.exists():
            return Response({'error': '此分類下還有子類，無法刪除'}, status=status.HTTP_400_BAD_REQUEST)
        if instance.products.exists():
            return Response({'error': '此分類下還有商品,無法刪除'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response({'error': '此分類下還有商品,無法刪除'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """Flat tree in display order: top-level rows interleaved with their children."""
        result = []
        tops = Category.objects.filter(parent__isnull=True).order_by('name')
        for top in tops:
            result.append({
                'id': top.id,
                'name': top.name,
                'parent': None,
                'parent_name': '',
                'full_name': top.name,
                'depth': 0,
                'children_count': top.children.count(),
            })
            for child in top.children.all().order_by('name'):
                result.append({
                    'id': child.id,
                    'name': child.name,
                    'parent': top.id,
                    'parent_name': top.name,
                    'full_name': f'{top.name} / {child.name}',
                    'depth': 1,
                    'children_count': 0,
                })
        return Response(result)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        """批次新增商品。Body: {supplier, rows: [{sku, name, barcode, base_unit, safety_stock, packagings:[...]}]}"""
        from django.db import transaction as _tx
        supplier_id = request.data.get('supplier')
        category_id = request.data.get('category')
        rows = request.data.get('rows') or []
        if not isinstance(rows, list) or not rows:
            return Response({'error': 'rows is required'}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        skipped = []
        errors = []

        # Pre-check duplicate SKUs within the batch and against DB
        seen = set()
        existing_skus = set(
            Product.objects.filter(sku__in=[r.get('sku') for r in rows if r.get('sku')])
            .values_list('sku', flat=True)
        )

        try:
            with _tx.atomic():
                for idx, row in enumerate(rows):
                    sku = (row.get('sku') or '').strip()
                    if not sku:
                        skipped.append({'index': idx, 'sku': '', 'reason': 'SKU 為必填'})
                        continue
                    if sku in seen:
                        skipped.append({'index': idx, 'sku': sku, 'reason': '批次內 SKU 重複'})
                        continue
                    if sku in existing_skus:
                        skipped.append({'index': idx, 'sku': sku, 'reason': 'SKU 已存在於資料庫'})
                        continue
                    seen.add(sku)

                    def _r3(v):
                        try:
                            return round(float(v or 0), 3)
                        except (TypeError, ValueError):
                            return 0
                    raw_pkgs = row.get('packagings') or []
                    pkgs = []
                    for pkg in raw_pkgs:
                        pkgs.append({
                            **pkg,
                            'price': _r3(pkg.get('price')),
                            'cost': _r3(pkg.get('cost')),
                        })
                    payload = {
                        'sku': sku,
                        'name': row.get('name') or sku,
                        'base_unit': row.get('base_unit') or '個',
                        'unit': row.get('base_unit') or '個',
                        'safety_stock': row.get('safety_stock') or 0,
                        'current_price': 0,
                        'supplier': supplier_id,
                        'category': category_id,
                        'packagings': pkgs,
                    }
                    # Default current_price from default packaging if any
                    for pkg in pkgs:
                        if pkg.get('is_default'):
                            payload['current_price'] = _r3(pkg.get('price'))
                            break

                    serializer = ProductSerializer(data=payload)
                    if not serializer.is_valid():
                        skipped.append({'index': idx, 'sku': sku, 'reason': str(serializer.errors)})
                        continue
                    serializer.save()
                    created += 1
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'created': created, 'skipped': skipped, 'errors': errors})

    @action(detail=False, methods=['post'], url_path='parse-xlsx')
    def parse_xlsx(self, request):
        """解析 xlsx 檔案，回傳 rows + warnings。"""
        from .xlsx_parser import parse_workbook

        upload = request.FILES.get('file')
        if not upload:
            return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)
        if upload.size > 5 * 1024 * 1024:
            return Response({'error': '檔案過大 (>5MB)'}, status=status.HTTP_400_BAD_REQUEST)
        sheet = request.POST.get('sheet') or request.GET.get('sheet') or None
        try:
            rows, warnings, sheet_names = parse_workbook(upload, sheet=sheet)
        except Exception as e:
            return Response({'error': f'解析失敗: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'rows': rows, 'warnings': warnings, 'sheet_names': sheet_names, 'selected_sheet': sheet or (sheet_names[0] if sheet_names else None)})


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """採購單收貨：建立庫存批次"""
        purchase_order = self.get_object()
        try:
            create_inventory_from_purchase(purchase_order)
            serializer = self.get_serializer(purchase_order)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PurchaseApplyItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseApplyItem.objects.all()
    serializer_class = PurchaseApplyItemSerializer


class InventoryBatchViewSet(viewsets.ModelViewSet):
    queryset = InventoryBatch.objects.all()
    serializer_class = InventoryBatchSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

    def get_queryset(self):
        qs = super().get_queryset()
        # 支援 ?in_stock=true 只顯示有剩餘的批次
        if self.request.query_params.get('in_stock', '').lower() in ('true', '1'):
            qs = qs.filter(remaining_quantity__gt=0)
        return qs


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """訂單完成：FIFO 扣減庫存 + 自動產生會計分錄"""
        order = self.get_object()
        try:
            complete_order(order)
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer


# ---------------------------------------------------------------------------
# Auth Views
# ---------------------------------------------------------------------------

class RegisterView(APIView):
    """POST /api/auth/register/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'username': user.username,
                'email': user.email,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    """GET /api/auth/me/"""

    def get(self, request):
        user = request.user
        return Response({'id': user.id, 'username': user.username, 'email': user.email})


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')

        if not user.check_password(old_password):
            return Response({'error': '舊密碼不正確'}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 6:
            return Response({'error': '新密碼至少需要 6 個字元'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': '密碼已更新成功'})


# ---------------------------------------------------------------------------
# Supplier / Customer ViewSets
# ---------------------------------------------------------------------------

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('search', '')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('search', '')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


# ---------------------------------------------------------------------------
# Stocktake Counts (draft)
# ---------------------------------------------------------------------------

class StocktakeCountViewSet(viewsets.ModelViewSet):
    """庫存盤點草稿 — 使用者輸入的實盤數量，逐筆 autosave。"""

    queryset = StocktakeCount.objects.all()
    serializer_class = StocktakeCountSerializer

    @action(detail=False, methods=['post'], url_path='upsert')
    def upsert(self, request):
        product_id = request.data.get('product')
        count = request.data.get('count')
        if product_id is None:
            return Response({'error': 'product is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            count_int = int(count)
            if count_int < 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response({'error': 'count must be a non-negative integer'}, status=status.HTTP_400_BAD_REQUEST)

        obj, _ = StocktakeCount.objects.update_or_create(
            product_id=product_id,
            defaults={'count': count_int},
        )
        return Response(StocktakeCountSerializer(obj).data)

    @action(detail=False, methods=['delete'], url_path='clear')
    def clear(self, request):
        StocktakeCount.objects.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Inventory Stock Summary
# ---------------------------------------------------------------------------

class InventoryStockSummaryView(APIView):
    """GET /api/inventory/stock-summary/  — 每個商品的庫存總量 (用於盤點+安全庫存警示)"""

    def get(self, request):
        products = Product.objects.all()
        result = []
        for product in products:
            total_remaining = (
                InventoryBatch.objects
                .filter(product=product)
                .aggregate(total=Coalesce(Sum('remaining_quantity'), Value(0, output_field=IntegerField())))
            )['total']
            result.append({
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'unit': product.unit,
                'safety_stock': product.safety_stock,
                'total_remaining': total_remaining,
                'is_low': total_remaining < product.safety_stock,
            })
        return Response(result)


# ---------------------------------------------------------------------------
# Dashboard API Views
# ---------------------------------------------------------------------------

class DashboardMonthlyTrendView(APIView):
    """GET /api/dashboard/monthly-trend/  — 最近 12 個月營收與費用趨勢"""

    def get(self, request):
        now = timezone.now().date()
        twelve_months_ago = (now.replace(day=1) - timedelta(days=365)).replace(day=1)

        base_qs = JournalVoucherItem.objects.filter(
            voucher__date__gte=twelve_months_ago,
            voucher__is_posted=True,
        )

        # Revenue: 科目類別 REVENUE 的貸方金額
        revenue_qs = (
            base_qs
            .filter(account_subject__category=AccountSubject.Category.REVENUE)
            .annotate(month=TruncMonth('voucher__date'))
            .values('month')
            .annotate(total=Coalesce(Sum('credit_amount'), Value(Decimal('0'))))
            .order_by('month')
        )

        # Expenses: 科目類別 EXPENSE 的借方金額
        expense_qs = (
            base_qs
            .filter(account_subject__category=AccountSubject.Category.EXPENSE)
            .annotate(month=TruncMonth('voucher__date'))
            .values('month')
            .annotate(total=Coalesce(Sum('debit_amount'), Value(Decimal('0'))))
            .order_by('month')
        )

        revenue_map = {r['month'].strftime('%Y-%m'): float(r['total']) for r in revenue_qs}
        expense_map = {e['month'].strftime('%Y-%m'): float(e['total']) for e in expense_qs}

        # 產生完整 12 個月標籤
        labels = []
        current = twelve_months_ago
        while current <= now.replace(day=1):
            labels.append(current.strftime('%Y-%m'))
            # 移到下個月第一天
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return Response({
            'labels': labels,
            'revenue': [revenue_map.get(l, 0) for l in labels],
            'expenses': [expense_map.get(l, 0) for l in labels],
        })


class DashboardExpenseBreakdownView(APIView):
    """GET /api/dashboard/expense-breakdown/  — 營業費用結構（圓餅圖）"""

    def get(self, request):
        qs = (
            JournalVoucherItem.objects
            .filter(
                account_subject__category=AccountSubject.Category.EXPENSE,
                voucher__is_posted=True,
            )
            .values(name=F('account_subject__name'))
            .annotate(total=Coalesce(Sum('debit_amount'), Value(Decimal('0'))))
            .order_by('-total')
        )

        return Response({
            'labels': [row['name'] for row in qs],
            'values': [float(row['total']) for row in qs],
        })


class DashboardTopProductsView(APIView):
    """GET /api/dashboard/top-products/  — 熱銷商品毛利 Top 10"""

    def get(self, request):
        # 已完成訂單的商品銷售統計
        product_sales = (
            OrderItem.objects
            .filter(order__status=Order.Status.COMPLETED)
            .values('product')
            .annotate(
                name=F('product__name'),
                revenue=Sum(F('selling_price') * F('quantity')),
                quantity_sold=Sum('quantity'),
            )
            .order_by('-revenue')
        )

        products = []
        for row in product_sales[:10]:
            revenue = float(row['revenue'] or 0)
            quantity_sold = row['quantity_sold'] or 0

            # 用 InventoryBatch 的加權平均 unit_cost 估算成本
            avg_cost_data = (
                InventoryBatch.objects
                .filter(product_id=row['product'])
                .aggregate(
                    total_cost=Sum(F('unit_cost') * F('batch_quantity')),
                    total_qty=Sum('batch_quantity'),
                )
            )
            if avg_cost_data['total_qty'] and avg_cost_data['total_qty'] > 0:
                avg_unit_cost = float(avg_cost_data['total_cost']) / float(avg_cost_data['total_qty'])
            else:
                avg_unit_cost = 0

            cost = avg_unit_cost * quantity_sold
            gross_profit = revenue - cost

            products.append({
                'name': row['name'],
                'revenue': revenue,
                'cost': round(cost, 2),
                'gross_profit': round(gross_profit, 2),
                'quantity_sold': quantity_sold,
            })

        # 按 gross_profit 降序
        products.sort(key=lambda x: x['gross_profit'], reverse=True)

        return Response({'products': products})


class DashboardSummaryView(APIView):
    """GET /api/dashboard/summary/  — 頂部卡片數據"""

    def get(self, request):
        now = timezone.now().date()
        this_month_start = now.replace(day=1)
        if this_month_start.month == 1:
            last_month_start = this_month_start.replace(year=this_month_start.year - 1, month=12)
        else:
            last_month_start = this_month_start.replace(month=this_month_start.month - 1)

        def _get_revenue(start, end):
            result = (
                JournalVoucherItem.objects
                .filter(
                    account_subject__category=AccountSubject.Category.REVENUE,
                    voucher__date__gte=start,
                    voucher__date__lt=end,
                    voucher__is_posted=True,
                )
                .aggregate(total=Coalesce(Sum('credit_amount'), Value(Decimal('0'))))
            )
            return result['total']

        def _get_expenses(start, end):
            result = (
                JournalVoucherItem.objects
                .filter(
                    account_subject__category=AccountSubject.Category.EXPENSE,
                    voucher__date__gte=start,
                    voucher__date__lt=end,
                    voucher__is_posted=True,
                )
                .aggregate(total=Coalesce(Sum('debit_amount'), Value(Decimal('0'))))
            )
            return result['total']

        # 下個月第一天
        if now.month == 12:
            next_month_start = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month_start = now.replace(month=now.month + 1, day=1)

        current_revenue = _get_revenue(this_month_start, next_month_start)
        current_expenses = _get_expenses(this_month_start, next_month_start)
        last_revenue = _get_revenue(last_month_start, this_month_start)
        last_expenses = _get_expenses(last_month_start, this_month_start)

        def _pct_change(current, previous):
            if previous and previous != 0:
                return round(float((current - previous) / previous * 100), 1)
            return 0.0

        total_revenue = float(current_revenue)
        total_expenses = float(current_expenses)

        return Response({
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': round(total_revenue - total_expenses, 2),
            'revenue_change': _pct_change(current_revenue, last_revenue),
            'expense_change': _pct_change(current_expenses, last_expenses),
        })
