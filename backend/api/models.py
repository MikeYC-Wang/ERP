from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    """商品分類 (最多 2 層：大類 → 子類)"""

    name = models.CharField('分類名稱', max_length=80)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='children',
        verbose_name='上層分類',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '商品分類'
        verbose_name_plural = '商品分類'
        ordering = ['parent_id', 'name']
        unique_together = [('parent', 'name')]

    def clean(self):
        super().clean()
        if self.parent_id:
            parent = self.parent
            if parent and parent.parent_id:
                raise ValidationError('分類最多只能 2 層 (大類 → 子類)')
            if self.pk and parent and parent.pk == self.pk:
                raise ValidationError('分類不可以自己為上層')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        if self.parent_id and self.parent:
            return f'{self.parent.name} / {self.name}'
        return self.name

    def __str__(self):
        return self.full_name


class AccountSubject(models.Model):
    """會計科目"""

    class Category(models.TextChoices):
        ASSET = 'asset', '資產'
        LIABILITY = 'liability', '負債'
        EQUITY = 'equity', '投入'
        REVENUE = 'revenue', '收入'
        EXPENSE = 'expense', '營業費用'

    code = models.CharField('科目代碼', max_length=20, unique=True)
    name = models.CharField('科目名稱', max_length=100)
    category = models.CharField('類別', max_length=20, choices=Category.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '會計科目'
        verbose_name_plural = '會計科目'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} {self.name}'


class JournalVoucher(models.Model):
    """傳票/日記帳"""

    voucher_number = models.CharField('傳票編號', max_length=30, unique=True)
    date = models.DateField('日期')
    description = models.TextField('摘要', blank=True, default='')
    is_system_generated = models.BooleanField('系統自動產生', default=False)
    is_posted = models.BooleanField('已入帳', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '傳票'
        verbose_name_plural = '傳票'
        ordering = ['-date', '-voucher_number']

    def __str__(self):
        return self.voucher_number


class JournalVoucherItem(models.Model):
    """傳票明細"""

    voucher = models.ForeignKey(
        JournalVoucher,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='傳票',
    )
    account_subject = models.ForeignKey(
        AccountSubject,
        on_delete=models.PROTECT,
        related_name='voucher_items',
        verbose_name='會計科目',
    )
    debit_amount = models.DecimalField('借方金額', max_digits=14, decimal_places=2, default=0)
    credit_amount = models.DecimalField('貸方金額', max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '傳票明細'
        verbose_name_plural = '傳票明細'

    def __str__(self):
        return f'{self.voucher.voucher_number} - {self.account_subject.name}'


class Supplier(models.Model):
    """供應商"""

    name = models.CharField('供應商名稱', max_length=200)
    contact_name = models.CharField('聯絡人', max_length=100, blank=True, default='')
    phone = models.CharField('電話', max_length=50, blank=True, default='')
    email = models.EmailField('Email', blank=True, default='')
    address = models.TextField('地址', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '供應商'
        verbose_name_plural = '供應商'
        ordering = ['name']

    def __str__(self):
        return self.name


class Customer(models.Model):
    """客戶"""

    name = models.CharField('客戶名稱', max_length=200)
    contact_name = models.CharField('聯絡人', max_length=100, blank=True, default='')
    phone = models.CharField('電話', max_length=50, blank=True, default='')
    email = models.EmailField('Email', blank=True, default='')
    address = models.TextField('地址', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '客戶'
        verbose_name_plural = '客戶'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """商品/SKU"""

    name = models.CharField('商品名稱', max_length=200)
    sku = models.CharField('SKU 編號', max_length=50, unique=True)
    unit = models.CharField('單位', max_length=20, default='個')  # deprecated alias, kept for compat
    base_unit = models.CharField('基本單位', max_length=20, default='個')
    current_price = models.DecimalField('目前售價', max_digits=12, decimal_places=3, default=0)
    last_cost = models.DecimalField('最新成本', max_digits=12, decimal_places=3, default=0)
    safety_stock = models.PositiveIntegerField('安全庫存量', default=0)
    supplier = models.ForeignKey(
        'Supplier',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='products',
        verbose_name='供應商',
    )
    category = models.ForeignKey(
        'Category',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='products',
        verbose_name='分類',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'
        ordering = ['sku']

    def __str__(self):
        return f'{self.sku} {self.name}'


class ProductPackaging(models.Model):
    """商品包裝規格 — 一個商品可定義多種銷售/採購包裝"""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='packagings',
        verbose_name='商品',
    )
    name = models.CharField('包裝名稱', max_length=50)
    quantity = models.PositiveIntegerField('包含基本單位數量', default=1)
    price = models.DecimalField('包裝售價', max_digits=12, decimal_places=3, default=0)
    cost = models.DecimalField('包裝成本', max_digits=12, decimal_places=3, default=0)
    barcode = models.CharField('條碼', max_length=64, blank=True, default='')
    is_default = models.BooleanField('預設包裝', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '商品包裝'
        verbose_name_plural = '商品包裝'
        ordering = ['quantity', 'id']

    def __str__(self):
        return f'{self.product.sku} - {self.name} x{self.quantity}'


class PurchaseOrder(models.Model):
    """採購單/母單"""

    class Status(models.TextChoices):
        DRAFT = 'draft', '草稿'
        CONFIRMED = 'confirmed', '已確認'
        RECEIVED = 'received', '已到貨'
        CANCELLED = 'cancelled', '已取消'

    order_number = models.CharField('採購單號', max_length=30, unique=True)
    supplier = models.CharField('供應商', max_length=200)
    date = models.DateField('日期')
    status = models.CharField('狀態', max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '採購單'
        verbose_name_plural = '採購單'
        ordering = ['-date', '-order_number']

    def __str__(self):
        return self.order_number


class PurchaseApplyItem(models.Model):
    """採購明細 - 金額來源的唯一依據"""

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='採購單',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='purchase_items',
        verbose_name='商品',
    )
    packaging = models.ForeignKey(
        ProductPackaging,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='purchase_items',
        verbose_name='包裝',
    )
    quantity = models.PositiveIntegerField('數量')
    # fee = 每包裝單價 (per-packaging unit price)；line_total = fee * quantity
    fee = models.DecimalField('每包裝單價', max_digits=12, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '採購明細'
        verbose_name_plural = '採購明細'

    def __str__(self):
        return f'{self.purchase_order.order_number} - {self.product.name}'


class InventoryBatch(models.Model):
    """庫存批次 (FIFO 核心)"""

    purchase_item = models.ForeignKey(
        PurchaseApplyItem,
        on_delete=models.CASCADE,
        related_name='inventory_batches',
        verbose_name='採購明細',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='inventory_batches',
        verbose_name='商品',
    )
    batch_quantity = models.PositiveIntegerField('批次進貨數量')
    remaining_quantity = models.PositiveIntegerField('剩餘數量')
    unit_cost = models.DecimalField('單位成本', max_digits=12, decimal_places=3)
    received_date = models.DateField('進貨日期')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '庫存批次'
        verbose_name_plural = '庫存批次'
        ordering = ['received_date', 'id']

    def __str__(self):
        return f'{self.product.sku} - {self.received_date} (剩餘: {self.remaining_quantity})'


class Order(models.Model):
    """訂單"""

    class Status(models.TextChoices):
        PENDING = 'pending', '待出貨'
        SHIPPED = 'shipped', '已出貨'
        COMPLETED = 'completed', '已完成'

    order_number = models.CharField('訂單編號', max_length=30, unique=True)
    customer_name = models.CharField('客戶名稱', max_length=200)
    customer_ref = models.ForeignKey(
        'Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='客戶',
    )
    order_date = models.DateField('訂單日期')
    status = models.CharField('狀態', max_length=20, choices=Status.choices, default=Status.PENDING)
    total_amount = models.DecimalField('總金額', max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '訂單'
        verbose_name_plural = '訂單'
        ordering = ['-order_date', '-order_number']

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    """訂單明細"""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='訂單',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='商品',
    )
    packaging = models.ForeignKey(
        ProductPackaging,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='order_items',
        verbose_name='包裝',
    )
    quantity = models.PositiveIntegerField('數量')
    selling_price = models.DecimalField('售價', max_digits=12, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '訂單明細'
        verbose_name_plural = '訂單明細'

    def __str__(self):
        return f'{self.order.order_number} - {self.product.name}'
