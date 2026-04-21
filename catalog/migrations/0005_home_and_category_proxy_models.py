from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_topvenueplacement_proxy"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecommendedPlacement",
            fields=[],
            options={
                "verbose_name": "Tavsiya",
                "verbose_name_plural": "Tavsiya qilamiz",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.homeplacement",),
        ),
        migrations.CreateModel(
            name="VenueVendor",
            fields=[],
            options={
                "verbose_name": "To‘yxona",
                "verbose_name_plural": "To‘yxona",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.vendor",),
        ),
        migrations.CreateModel(
            name="MediaVendor",
            fields=[],
            options={
                "verbose_name": "FotoStudio",
                "verbose_name_plural": "FotoStudio",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.vendor",),
        ),
        migrations.CreateModel(
            name="AttireVendor",
            fields=[],
            options={
                "verbose_name": "Kelin va kuyov liboslari",
                "verbose_name_plural": "Kelin va kuyov liboslari",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.vendor",),
        ),
        migrations.CreateModel(
            name="TransportVendor",
            fields=[],
            options={
                "verbose_name": "Kartej",
                "verbose_name_plural": "Kartej",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.vendor",),
        ),
        migrations.CreateModel(
            name="McVendor",
            fields=[],
            options={
                "verbose_name": "Honanda",
                "verbose_name_plural": "Honanda",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.vendor",),
        ),
        migrations.CreateModel(
            name="DecorVendor",
            fields=[],
            options={
                "verbose_name": "Dekor va zal bezatish",
                "verbose_name_plural": "Dekor va zal bezatish",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.vendor",),
        ),
        migrations.CreateModel(
            name="MarryMeVendor",
            fields=[],
            options={
                "verbose_name": "Marry me joy va taklif",
                "verbose_name_plural": "Marry me joy va taklif",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.vendor",),
        ),
    ]
