from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    AccountSubject,
    InventoryBatch,
    JournalVoucher,
    JournalVoucherItem,
    Order,
    OrderItem,
    Product,
    PurchaseApplyItem,
    PurchaseOrder,
)
from .serializers import (
    AccountSubjectSerializer,
    InventoryBatchSerializer,
    JournalVoucherItemSerializer,
    JournalVoucherSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ProductSerializer,
    PurchaseApplyItemSerializer,
    PurchaseOrderSerializer,
)
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


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


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
