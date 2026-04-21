from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_seed_catalog"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendor",
            name="story_video_url",
            field=models.URLField(
                blank=True,
                help_text="Top to‘yxonalar story popup uchun YouTube link.",
                max_length=2048,
                verbose_name="story video URL (YouTube)",
            ),
        ),
    ]
