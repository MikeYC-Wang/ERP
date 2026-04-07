from django.db import migrations


def set_existing_posted(apps, schema_editor):
    JournalVoucher = apps.get_model('api', 'JournalVoucher')
    JournalVoucher.objects.all().update(is_posted=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_journalvoucher_is_posted'),
    ]

    operations = [
        migrations.RunPython(set_existing_posted, noop_reverse),
    ]
