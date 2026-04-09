from django.db import migrations


def forwards(apps, schema_editor):
    Product = apps.get_model('api', 'Product')
    ProductPackaging = apps.get_model('api', 'ProductPackaging')
    PurchaseApplyItem = apps.get_model('api', 'PurchaseApplyItem')
    OrderItem = apps.get_model('api', 'OrderItem')

    for product in Product.objects.all():
        # Backfill base_unit from unit if empty
        if not product.base_unit:
            product.base_unit = product.unit or '個'
            product.save(update_fields=['base_unit'])

        pkgs = list(product.packagings.all().order_by('quantity', 'id'))

        if not pkgs:
            # 1) 無任何 packaging → 建立一筆預設
            ProductPackaging.objects.create(
                product=product,
                name=product.base_unit or product.unit or '單個',
                quantity=1,
                price=product.current_price or 0,
                cost=0,
                barcode='',
                is_default=True,
            )
        else:
            defaults = [p for p in pkgs if p.is_default]
            if len(defaults) == 0:
                # 2) 有 packaging 但無 default → 以 quantity=1 (或最小 quantity) 作為 default
                base_row = next((p for p in pkgs if p.quantity == 1), pkgs[0])
                base_row.is_default = True
                base_row.save(update_fields=['is_default'])
            elif len(defaults) > 1:
                # 3) 多個 default → 保留第一個
                for extra in defaults[1:]:
                    extra.is_default = False
                    extra.save(update_fields=['is_default'])

            # 4) 若無 quantity=1 列 → 建立一筆
            pkgs = list(product.packagings.all().order_by('quantity', 'id'))
            if not any(p.quantity == 1 for p in pkgs):
                has_default = any(p.is_default for p in pkgs)
                ProductPackaging.objects.create(
                    product=product,
                    name=product.base_unit or product.unit or '單個',
                    quantity=1,
                    price=product.current_price or 0,
                    cost=0,
                    barcode='',
                    is_default=not has_default,
                )

    # Backfill packaging FK on existing purchase/order items -> product default
    for product in Product.objects.all():
        default_pkg = product.packagings.filter(is_default=True).first() \
            or product.packagings.filter(quantity=1).first()
        if not default_pkg:
            continue
        PurchaseApplyItem.objects.filter(
            product=product, packaging__isnull=True
        ).update(packaging=default_pkg)
        OrderItem.objects.filter(
            product=product, packaging__isnull=True
        ).update(packaging=default_pkg)


def backwards(apps, schema_editor):
    # No-op: we don't want to delete packagings on reverse
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_product_base_unit_product_last_cost_product_supplier_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
