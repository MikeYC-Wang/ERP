from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    AccountSubjectViewSet,
    CustomerViewSet,
    DashboardExpenseBreakdownView,
    DashboardMonthlyTrendView,
    DashboardSummaryView,
    DashboardTopProductsView,
    InventoryBatchViewSet,
    InventoryStockSummaryView,
    JournalVoucherItemViewSet,
    JournalVoucherViewSet,
    MeView,
    OrderItemViewSet,
    OrderViewSet,
    ProductViewSet,
    PurchaseApplyItemViewSet,
    PurchaseOrderViewSet,
    RegisterView,
    SupplierViewSet,
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
router.register(r'suppliers', SupplierViewSet)
router.register(r'customers', CustomerViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Auth
    path('auth/login/', TokenObtainPairView.as_view(), name='auth-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    # Inventory Stock Summary
    path('inventory/stock-summary/', InventoryStockSummaryView.as_view(), name='inventory-stock-summary'),
    # Dashboard APIs
    path('dashboard/monthly-trend/', DashboardMonthlyTrendView.as_view(), name='dashboard-monthly-trend'),
    path('dashboard/expense-breakdown/', DashboardExpenseBreakdownView.as_view(), name='dashboard-expense-breakdown'),
    path('dashboard/top-products/', DashboardTopProductsView.as_view(), name='dashboard-top-products'),
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
]
