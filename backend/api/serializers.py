from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    AccountSubject,
    Customer,
    InventoryBatch,
    JournalVoucher,
    JournalVoucherItem,
    Order,
    OrderItem,
    Product,
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


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


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
