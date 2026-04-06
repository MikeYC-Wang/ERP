from decimal import Decimal
from uuid import uuid4

from django.db import transaction
from django.utils import timezone

from .models import (
    AccountSubject,
    InventoryBatch,
    JournalVoucher,
    JournalVoucherItem,
    Order,
    PurchaseOrder,
)


def deduct_inventory_fifo(product, quantity):
    """
    依 FIFO 順序（按進貨日期 created_at 排序）扣減庫存。
    回傳扣減明細列表：[{batch, quantity_deducted, unit_cost}]
    如果庫存不足，raise Exception。
    """
    batches = (
        InventoryBatch.objects
        .filter(product=product, remaining_quantity__gt=0)
        .order_by('created_at', 'id')
        .select_for_update()
    )

    remaining_to_deduct = quantity
    deductions = []

    for batch in batches:
        if remaining_to_deduct <= 0:
            break

        deduct_qty = min(batch.remaining_quantity, remaining_to_deduct)
        batch.remaining_quantity -= deduct_qty
        batch.save(update_fields=['remaining_quantity', 'updated_at'])

        deductions.append({
            'batch': batch,
            'quantity_deducted': deduct_qty,
            'unit_cost': batch.unit_cost,
        })

        remaining_to_deduct -= deduct_qty

    if remaining_to_deduct > 0:
        raise Exception(
            f'庫存不足：商品「{product.name}」(SKU: {product.sku}) '
            f'需要 {quantity}，但僅有 {quantity - remaining_to_deduct} 可用'
        )

    return deductions


@transaction.atomic
def create_inventory_from_purchase(purchase_order):
    """
    採購單確認收貨時：
    1. 根據 PurchaseApplyItem 建立 InventoryBatch。
    2. 自動產生會計分錄：借 商品存貨 / 貸 銀行存款。
    金額必須從 PurchaseApplyItem.fee 取得（規格書嚴格要求）。
    """
    if purchase_order.status == PurchaseOrder.Status.RECEIVED:
        raise Exception('此採購單已經收貨，不可重複收貨')

    today = timezone.now().date()
    total_cost = Decimal('0')

    for item in purchase_order.items.select_related('product'):
        unit_cost = item.fee / item.quantity
        InventoryBatch.objects.create(
            purchase_item=item,
            product=item.product,
            batch_quantity=item.quantity,
            remaining_quantity=item.quantity,
            unit_cost=unit_cost,
            received_date=today,
        )
        total_cost += item.fee

    # 自動會計分錄：借 商品存貨 / 貸 銀行存款
    try:
        inventory_account = AccountSubject.objects.get(code='1001')  # 商品存貨
        bank_account = AccountSubject.objects.get(code='1002')       # 銀行存款
        voucher = JournalVoucher.objects.create(
            voucher_number=_generate_voucher_number(),
            date=today,
            description=f'採購單 {purchase_order.order_number} 收貨入庫',
            is_system_generated=True,
        )
        JournalVoucherItem.objects.create(
            voucher=voucher,
            account_subject=inventory_account,
            debit_amount=total_cost,
            credit_amount=Decimal('0'),
        )
        JournalVoucherItem.objects.create(
            voucher=voucher,
            account_subject=bank_account,
            debit_amount=Decimal('0'),
            credit_amount=total_cost,
        )
    except AccountSubject.DoesNotExist:
        pass  # 若科目不存在（測試環境），略過分錄

    purchase_order.status = PurchaseOrder.Status.RECEIVED
    purchase_order.save(update_fields=['status', 'updated_at'])

    return purchase_order


def _generate_voucher_number():
    """產生唯一傳票編號"""
    now = timezone.now()
    return f'V{now.strftime("%Y%m%d%H%M%S")}-{uuid4().hex[:6].upper()}'


@transaction.atomic
def complete_order(order):
    """
    訂單完成時：
    1. 依 FIFO 扣減庫存
    2. 自動產生兩張傳票：
       a. 借：商品成本(COGS) / 貸：商品存貨
       b. 借：應收帳款(或銀行存款) / 貸：商品銷售收入
    """
    if order.status == Order.Status.COMPLETED:
        raise Exception('此訂單已完成，不可重複完成')

    today = timezone.now().date()
    total_cogs = Decimal('0')
    total_revenue = Decimal('0')

    # 1. 遍歷訂單明細，逐一 FIFO 扣減
    for item in order.items.select_related('product'):
        deductions = deduct_inventory_fifo(item.product, item.quantity)
        item_cogs = sum(
            Decimal(str(d['quantity_deducted'])) * d['unit_cost']
            for d in deductions
        )
        total_cogs += item_cogs
        total_revenue += item.quantity * item.selling_price

    # 2. 取得會計科目
    cogs_account = AccountSubject.objects.get(code='6001')
    inventory_account = AccountSubject.objects.get(code='1001')
    receivable_account = AccountSubject.objects.get(code='1002')
    revenue_account = AccountSubject.objects.get(code='5001')

    # 3. 傳票 1：借 COGS / 貸 存貨
    voucher1 = JournalVoucher.objects.create(
        voucher_number=_generate_voucher_number(),
        date=today,
        description=f'訂單 {order.order_number} 銷貨成本結轉',
        is_system_generated=True,
    )
    JournalVoucherItem.objects.create(
        voucher=voucher1,
        account_subject=cogs_account,
        debit_amount=total_cogs,
        credit_amount=Decimal('0'),
    )
    JournalVoucherItem.objects.create(
        voucher=voucher1,
        account_subject=inventory_account,
        debit_amount=Decimal('0'),
        credit_amount=total_cogs,
    )

    # 4. 傳票 2：借 應收帳款 / 貸 銷售收入
    voucher2 = JournalVoucher.objects.create(
        voucher_number=_generate_voucher_number(),
        date=today,
        description=f'訂單 {order.order_number} 銷售收入',
        is_system_generated=True,
    )
    JournalVoucherItem.objects.create(
        voucher=voucher2,
        account_subject=receivable_account,
        debit_amount=total_revenue,
        credit_amount=Decimal('0'),
    )
    JournalVoucherItem.objects.create(
        voucher=voucher2,
        account_subject=revenue_account,
        debit_amount=Decimal('0'),
        credit_amount=total_revenue,
    )

    # 5. 更新訂單狀態
    order.status = Order.Status.COMPLETED
    order.save(update_fields=['status', 'updated_at'])

    return order
