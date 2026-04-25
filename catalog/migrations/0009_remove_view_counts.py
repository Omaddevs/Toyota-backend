from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0008_vendor_view_count_and_promopost_category"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="vendor",
            name="view_count",
        ),
        migrations.RemoveField(
            model_name="promopost",
            name="view_count",
        ),
    ]
