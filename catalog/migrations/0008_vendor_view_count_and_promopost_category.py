from django.db import migrations, models
import django.db.models.deletion


def add_category_to_promopost_if_missing(apps, schema_editor):
    PromoPost = apps.get_model("catalog", "PromoPost")
    Category = apps.get_model("catalog", "Category")
    
    with schema_editor.connection.cursor() as cursor:
        columns = {
            col.name
            for col in schema_editor.connection.introspection.get_table_description(
                cursor, PromoPost._meta.db_table
            )
        }
    
    if "category_id" not in columns:
        field = models.ForeignKey(
            to=Category,
            on_delete=django.db.models.deletion.PROTECT,
            related_name="promo_posts",
            verbose_name="kategoriya",
            default="venue",
        )
        field.set_attributes_from_name("category")
        schema_editor.add_field(PromoPost, field)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0007_vendor_image_optional"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_category_to_promopost_if_missing, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="promopost",
                    name="category",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="promo_posts",
                        to="catalog.Category",
                        verbose_name="kategoriya",
                    ),
                ),
            ],
        ),
    ]
