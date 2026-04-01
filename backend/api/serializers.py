from rest_framework import serializers

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


class AccountSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubject
        fields = '__all__'


class JournalVoucherItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalVoucherItem
        fields = '__all__'


class JournalVoucherSerializer(serializers.ModelSerializer):
    items = JournalVoucherItemSerializer(many=True, read_only=True)

    class Meta:
        model = JournalVoucher
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class PurchaseApplyItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseApplyItem
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseApplyItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = '__all__'


class InventoryBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBatch
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
