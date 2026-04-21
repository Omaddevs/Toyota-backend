from django.db import migrations


def seed(apps, schema_editor):
    """Boshlang‘ich demo ma’lumotlar olib tashlandi — faqat admin panel orqali kiritiladi."""


def unseed(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
