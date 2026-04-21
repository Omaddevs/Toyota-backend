from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0006_vendor_image_upload"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vendor",
            name="image",
            field=models.URLField(
                blank=True,
                max_length=2048,
                verbose_name="asosiy rasm URL",
            ),
        ),
    ]
