from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_home_and_category_proxy_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendor",
            name="image_upload",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="vendors/",
                verbose_name="asosiy rasm fayl (upload)",
            ),
        ),
    ]
