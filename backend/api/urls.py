from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountSubjectViewSet,
    InventoryBatchViewSet,
    JournalVoucherItemViewSet,
    JournalVoucherViewSet,
    OrderItemViewSet,
    OrderViewSet,
    ProductViewSet,
    PurchaseApplyItemViewSet,
    PurchaseOrderViewSet,
)

router = DefaultRouter()
router.register(r'account-subjects', AccountSubjectViewSet)
router.register(r'journal-vouchers', JournalVoucherViewSet)
router.register(r'journal-voucher-items', JournalVoucherItemViewSet)
router.register(r'products', ProductViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'purchase-apply-items', PurchaseApplyItemViewSet)
router.register(r'inventory-batches', InventoryBatchViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
