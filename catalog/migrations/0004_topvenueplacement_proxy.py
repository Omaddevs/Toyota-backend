from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_vendor_story_video_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="TopVenuePlacement",
            fields=[],
            options={
                "verbose_name": "Top to‘yxona",
                "verbose_name_plural": "Top to‘yxonalar",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.homeplacement",),
        ),
    ]
