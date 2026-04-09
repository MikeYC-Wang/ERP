from django.contrib.auth.models import User
from rest_framework import serializers

from django.db import transaction

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
    ProductPackaging,
    PurchaseApplyItem,
    PurchaseOrder,
    Supplier,
)


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class AccountSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubject
        fields = '__all__'


class JournalVoucherItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalVoucherItem
        fields = '__all__'
        extra_kwargs = {
            'voucher': {'required': False},
        }


class JournalVoucherSerializer(serializers.ModelSerializer):
    items = JournalVoucherItemSerializer(many=True, required=False)
    voucher_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = JournalVoucher
        fields = '__all__'

    @staticmethod
    def _generate_voucher_number(date):
        """產生 JV-YYYYMM-NNN 格式編號，自動遞增"""
        prefix = f"JV-{date.strftime('%Y%m')}-"
        last = (
            JournalVoucher.objects
            .filter(voucher_number__startswith=prefix)
            .order_by('-voucher_number')
            .values_list('voucher_number', flat=True)
            .first()
        )
        seq = int(last.split('-')[-1]) + 1 if last else 1
        return f"{prefix}{str(seq).zfill(3)}"

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        if not validated_data.get('voucher_number'):
            date = validated_data.get('date')
            validated_data['voucher_number'] = self._generate_voucher_number(date)
        voucher = JournalVoucher.objects.create(**validated_data)
        for item_data in items_data:
            item_data.pop('voucher', None)
            JournalVoucherItem.objects.create(voucher=voucher, **item_data)
        return voucher

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                item_data.pop('voucher', None)
                JournalVoucherItem.objects.create(voucher=instance, **item_data)

        return instance


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'parent_name', 'full_name', 'children_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_children_count(self, obj):
        return obj.children.count()

    def validate(self, attrs):
        parent = attrs.get('parent') or (self.instance.parent if self.instance else None)
        if parent and parent.parent_id:
            raise serializers.ValidationError({'parent': '分類最多只能 2 層 (大類 → 子類)'})
        if self.instance and parent and parent.pk == self.instance.pk:
            raise serializers.ValidationError({'parent': '分類不可以自己為上層'})
        # If editing a top-level that has children, it cannot become a child
        if self.instance and parent and self.instance.children.exists():
            raise serializers.ValidationError({'parent': '此大類下已有子類，無法改為子類'})
        return attrs


class ProductPackagingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ProductPackaging
        fields = [
            'id', 'product', 'name', 'quantity', 'price', 'cost',
            'barcode', 'is_default', 'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'product': {'required': False},
        }
        read_only_fields = ['created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    packagings = ProductPackagingSerializer(many=True, required=False)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    category_name = serializers.SerializerMethodField()

    def get_category_name(self, obj):
        return obj.category.full_name if obj.category else ''

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['last_cost']

    def validate_packagings(self, value):
        if not value:
            raise serializers.ValidationError('至少需要一個包裝')
        defaults = [p for p in value if p.get('is_default')]
        if len(defaults) != 1:
            raise serializers.ValidationError('必須恰好一個預設包裝')
        has_base = any(int(p.get('quantity') or 0) == 1 for p in value)
        if not has_base:
            raise serializers.ValidationError('必須包含一個基本包裝 (quantity=1)')
        if sum(1 for p in value if int(p.get('quantity') or 0) == 1) > 1:
            raise serializers.ValidationError('僅能有一個基本單位 (數量=1) 的包裝')
        for p in value:
            if int(p.get('quantity') or 0) < 1:
                raise serializers.ValidationError('每個包裝的數量必須 >= 1')
        return value

    @transaction.atomic
    def _write_packagings(self, product, packagings_data):
        """就地調和 packaging 列：保留既有列的 id 以避免歷史 FK 失效。"""
        existing = {p.id: p for p in product.packagings.all()}
        incoming_ids = set()
        for pkg in packagings_data:
            pkg_data = {k: v for k, v in pkg.items() if k not in ('id', 'product')}
            pkg_id = pkg.get('id')
            if pkg_id and pkg_id in existing:
                obj = existing[pkg_id]
                for attr, val in pkg_data.items():
                    setattr(obj, attr, val)
                obj.save()
                incoming_ids.add(pkg_id)
            else:
                ProductPackaging.objects.create(product=product, **pkg_data)

        # 僅刪除：既有但未包含在 incoming 內的列；若已被 OrderItem/PurchaseApplyItem 引用則拒絕
        for old_id, old_obj in existing.items():
            if old_id in incoming_ids:
                continue
            if old_obj.order_items.exists() or old_obj.purchase_items.exists():
                raise serializers.ValidationError('此包裝已被訂單/採購單使用，無法刪除')
            old_obj.delete()

    @transaction.atomic
    def create(self, validated_data):
        packagings_data = validated_data.pop('packagings', None)
        product = Product.objects.create(**validated_data)
        if not packagings_data:
            # 未提供 packagings：合成一個預設列，並走同一個驗證/寫入路徑
            packagings_data = [{
                'name': product.base_unit or product.unit or '單個',
                'quantity': 1,
                'price': product.current_price,
                'cost': 0,
                'barcode': '',
                'is_default': True,
            }]
            self.validate_packagings(packagings_data)
        self._write_packagings(product, packagings_data)
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        packagings_data = validated_data.pop('packagings', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if packagings_data is not None:
            self._write_packagings(instance, packagings_data)
        return instance


class PurchaseApplyItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseApplyItem
        fields = '__all__'
        extra_kwargs = {
            'purchase_order': {'required': False},
        }


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseApplyItemSerializer(many=True, required=False)
    order_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = PurchaseOrder
        fields = '__all__'

    @staticmethod
    def _generate_order_number(date):
        prefix = f"PO-{date.strftime('%Y%m')}-"
        last = (
            PurchaseOrder.objects
            .filter(order_number__startswith=prefix)
            .order_by('-order_number')
            .values_list('order_number', flat=True)
            .first()
        )
        seq = int(last.split('-')[-1]) + 1 if last else 1
        return f"{prefix}{str(seq).zfill(3)}"

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        if not validated_data.get('order_number'):
            validated_data['order_number'] = self._generate_order_number(validated_data.get('date'))
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        for item_data in items_data:
            item_data.pop('purchase_order', None)
            PurchaseApplyItem.objects.create(purchase_order=purchase_order, **item_data)
        return purchase_order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                item_data.pop('purchase_order', None)
                PurchaseApplyItem.objects.create(purchase_order=instance, **item_data)

        return instance


class InventoryBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBatch
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        extra_kwargs = {
            'order': {'required': False},
        }


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    order_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = '__all__'

    @staticmethod
    def _generate_order_number(date):
        prefix = f"SO-{date.strftime('%Y%m')}-"
        last = (
            Order.objects
            .filter(order_number__startswith=prefix)
            .order_by('-order_number')
            .values_list('order_number', flat=True)
            .first()
        )
        seq = int(last.split('-')[-1]) + 1 if last else 1
        return f"{prefix}{str(seq).zfill(3)}"

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        if not validated_data.get('order_number'):
            validated_data['order_number'] = self._generate_order_number(validated_data.get('order_date'))
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            item_data.pop('order', None)
            OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                item_data.pop('order', None)
                OrderItem.objects.create(order=instance, **item_data)

        return instance
