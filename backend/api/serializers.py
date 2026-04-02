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
        extra_kwargs = {
            'voucher': {'required': False},
        }


class JournalVoucherSerializer(serializers.ModelSerializer):
    items = JournalVoucherItemSerializer(many=True, required=False)

    class Meta:
        model = JournalVoucher
        fields = '__all__'

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
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

    class Meta:
        model = PurchaseOrder
        fields = '__all__'

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
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

    class Meta:
        model = Order
        fields = '__all__'

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
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
