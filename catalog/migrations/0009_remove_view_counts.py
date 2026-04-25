from django.db import migrations, models


def remove_promopost_view_count_if_exists(apps, schema_editor):
    PromoPost = apps.get_model("catalog", "PromoPost")
    with schema_editor.connection.cursor() as cursor:
        columns = {
            col.name
            for col in schema_editor.connection.introspection.get_table_description(
                cursor, PromoPost._meta.db_table
            )
        }
    if "view_count" in columns:
        field = models.PositiveIntegerField(default=0, verbose_name="ko‘rishlar")
        field.set_attributes_from_name("view_count")
        schema_editor.remove_field(PromoPost, field)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0008_vendor_view_count_and_promopost_category"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    remove_promopost_view_count_if_exists, migrations.RunPython.noop
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="promopost",
                    name="view_count",
                ),
            ],
        ),
    ]
