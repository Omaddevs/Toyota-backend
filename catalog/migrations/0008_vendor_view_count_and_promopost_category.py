from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0007_vendor_image_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendor",
            name="view_count",
            field=models.PositiveIntegerField(default=0, verbose_name="ko‘rishlar"),
        ),
        migrations.AddField(
            model_name="promopost",
            name="category",
            field=models.ForeignKey(
                default="venue",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="promo_posts",
                to="catalog.category",
                verbose_name="kategoriya",
            ),
            preserve_default=False,
        ),
    ]
