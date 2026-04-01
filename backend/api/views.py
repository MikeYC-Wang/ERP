from rest_framework import viewsets

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


class AccountSubjectViewSet(viewsets.ModelViewSet):
    queryset = AccountSubject.objects.all()
    serializer_class = AccountSubjectSerializer


class JournalVoucherViewSet(viewsets.ModelViewSet):
    queryset = JournalVoucher.objects.all()
    serializer_class = JournalVoucherSerializer


class JournalVoucherItemViewSet(viewsets.ModelViewSet):
    queryset = JournalVoucherItem.objects.all()
    serializer_class = JournalVoucherItemSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer


class PurchaseApplyItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseApplyItem.objects.all()
    serializer_class = PurchaseApplyItemSerializer


class InventoryBatchViewSet(viewsets.ModelViewSet):
    queryset = InventoryBatch.objects.all()
    serializer_class = InventoryBatchSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
