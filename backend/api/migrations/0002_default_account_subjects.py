"""
Data migration: 建立系統預設會計科目
"""
from django.db import migrations


def create_default_account_subjects(apps, schema_editor):
    AccountSubject = apps.get_model('api', 'AccountSubject')
    defaults = [
        ('1001', '商品存貨', 'asset'),
        ('1002', '應收帳款', 'asset'),
        ('1003', '銀行存款', 'asset'),
        ('5001', '商品銷售收入', 'revenue'),
        ('6001', '商品成本', 'expense'),
    ]
    for code, name, category in defaults:
        AccountSubject.objects.get_or_create(
            code=code,
            defaults={'name': name, 'category': category},
        )


def remove_default_account_subjects(apps, schema_editor):
    AccountSubject = apps.get_model('api', 'AccountSubject')
    AccountSubject.objects.filter(code__in=['1001', '1002', '1003', '5001', '6001']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_default_account_subjects,
            remove_default_account_subjects,
        ),
    ]
