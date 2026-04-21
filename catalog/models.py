import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, Count


class Category(models.Model):
    """To‘yxona, FotoStudio, Dekor, … — barcha yo‘nalishlar."""

    ZONE_PRIMARY = "primary"
    ZONE_EXTRA = "extra"
    ZONE_CHOICES = [
        (ZONE_PRIMARY, "Asosiy qator (bosh sahifa 1-qator)"),
        (ZONE_EXTRA, "Qo‘shimcha qator (2-qator)"),
    ]

    code = models.CharField(
        "kod (id)",
        max_length=32,
        primary_key=True,
        help_text="Masalan: venue, media, decor — frontend categoryId bilan mos.",
    )
    slug = models.SlugField("URL slug", max_length=64, unique=True)
    title = models.CharField("sarlavha", max_length=255)
    short_label = models.CharField("qisqa nom", max_length=64)
    subtitle = models.TextField("tagline", blank=True)
    icon = models.CharField(
        "ikonka (masalan ph-buildings)",
        max_length=64,
        blank=True,
    )
    search_hint = models.CharField("qidiruv yordami", max_length=255, blank=True)
    zone = models.CharField(
        "joylashuv",
        max_length=16,
        choices=ZONE_CHOICES,
        default=ZONE_PRIMARY,
    )
    sort_order = models.PositiveSmallIntegerField("tartib", default=0)
    is_active = models.BooleanField("faol", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["zone", "sort_order", "title"]
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.title


class Vendor(models.Model):
    """Xizmat ko‘rsatuvchi (to‘yxona, studio, …)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        "tashqi id (masalan v-versal)",
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Frontend va URL uchun barqaror identifikator.",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="vendors",
        verbose_name="kategoriya",
    )
    slug = models.SlugField("URL slug", max_length=128)
    name = models.CharField("nom", max_length=255)
    district = models.CharField("tuman", max_length=128, blank=True)
    image = models.URLField("asosiy rasm URL", max_length=2048, blank=True)
    image_upload = models.ImageField(
        "asosiy rasm fayl (upload)",
        upload_to="vendors/",
        blank=True,
        null=True,
    )
    story_video_url = models.URLField(
        "story video URL (YouTube)",
        max_length=2048,
        blank=True,
        help_text="Top to‘yxonalar story popup uchun YouTube link.",
    )
    gallery = models.JSONField(
        "galereya (URL ro‘yxati)",
        default=list,
        blank=True,
    )
    price_label = models.CharField("narx", max_length=64, blank=True)
    price_note = models.CharField("narx izohi", max_length=64, blank=True)
    badge = models.CharField("badge (Top, Yangi…)", max_length=32, blank=True, null=True)
    footer_line = models.CharField("pastki qator", max_length=128, blank=True)
    footer_icon = models.CharField("ikonka klass", max_length=64, blank=True)
    phone = models.CharField("telefon", max_length=64, blank=True)
    telegram = models.CharField("telegram", max_length=64, blank=True)
    rating = models.DecimalField(
        "reyting",
        max_digits=2,
        decimal_places=1,
        default=4.5,
    )
    review_count_cached = models.PositiveIntegerField(
        "sharhlar soni (cache)",
        default=0,
        help_text="Avtomatik yangilanadi (sharhlar qo‘shilganda).",
    )
    tagline = models.CharField("tagline", max_length=512, blank=True)
    location = models.CharField("manzil", max_length=512, blank=True)
    description = models.TextField("tavsif", blank=True)
    specs = models.JSONField(
        "texnik jadval [{label, value}]",
        default=list,
        blank=True,
    )
    is_published = models.BooleanField("saytda ko‘rinsin", default=True)
    sort_order = models.PositiveIntegerField("ichki tartib", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "sort_order", "name"]
        verbose_name = "Vendor"
        verbose_name_plural = "Vendorlar"
        indexes = [
            models.Index(fields=["category", "is_published"]),
        ]

    def __str__(self):
        return self.name

    def refresh_review_stats(self):
        agg = self.reviews.aggregate(c=Count("id"), avg=Avg("rating"))
        count = agg["c"] or 0
        self.review_count_cached = count
        if count and agg["avg"] is not None:
            self.rating = round(agg["avg"], 1)
        self.save(update_fields=["review_count_cached", "rating", "updated_at"])


class VendorReview(models.Model):
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="vendor",
    )
    author = models.CharField("muallif", max_length=128)
    rating = models.PositiveSmallIntegerField("baho (1–5)", default=5)
    text = models.TextField("matn")
    date = models.DateField("sana", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"

    def __str__(self):
        return f"{self.author} — {self.vendor.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.vendor.refresh_review_stats()

    def delete(self, *args, **kwargs):
        vendor = self.vendor
        super().delete(*args, **kwargs)
        vendor.refresh_review_stats()


class PromoPost(models.Model):
    """Bosh sahifa karuseli — reklama / banner."""

    slug = models.SlugField(unique=True, max_length=64)
    badge = models.CharField("badge", max_length=64, blank=True)
    title = models.CharField("sarlavha", max_length=255)
    path = models.CharField("yo‘nalish (masalan /category/toyxona)", max_length=255)
    background_url = models.URLField("fon rasm URL", max_length=2048)
    sort_order = models.PositiveSmallIntegerField("tartib", default=0)
    view_count = models.PositiveIntegerField("ko‘rishlar", default=0)
    is_active = models.BooleanField("faol", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "Promo post"
        verbose_name_plural = "Promo postlar"

    def __str__(self):
        return self.title


class HomePlacement(models.Model):
    """Top to‘yxonalar va Tavsiya qilamiz — tartibli vendor tanlovi."""

    SECTION_TOP_VENUES = "top_venues"
    SECTION_RECOMMENDED = "recommended"
    SECTION_CHOICES = [
        (SECTION_TOP_VENUES, "Top to‘yxonalar"),
        (SECTION_RECOMMENDED, "Tavsiya qilamiz"),
    ]

    section = models.CharField("bo‘lim", max_length=32, choices=SECTION_CHOICES)
    sort_order = models.PositiveSmallIntegerField("tartib", default=0)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="home_placements",
        verbose_name="vendor",
    )

    class Meta:
        ordering = ["section", "sort_order"]
        verbose_name = "Bosh sahifa joylashuvi"
        verbose_name_plural = "Bosh sahifa joylashuvlari"
        constraints = [
            models.UniqueConstraint(
                fields=["section", "vendor"],
                name="uniq_home_section_vendor",
            ),
        ]

    def __str__(self):
        return f"{self.get_section_display()} — {self.vendor.name}"

    def clean(self):
        super().clean()
        if self.section == self.SECTION_TOP_VENUES:
            if self.vendor.category_id != "venue":
                raise ValidationError(
                    {
                        "vendor": "Top to‘yxonalar faqat «To‘yxona» (venue) kategoriyasidagi vendorlar uchun."
                    }
                )


class TopVenuePlacement(HomePlacement):
    """Admin uchun alohida Top to‘yxonalar bo‘limi (proxy)."""

    class Meta:
        proxy = True
        verbose_name = "Top to‘yxona"
        verbose_name_plural = "Top to‘yxonalar"


class RecommendedPlacement(HomePlacement):
    """Admin uchun alohida Tavsiya qilamiz bo‘limi (proxy)."""

    class Meta:
        proxy = True
        verbose_name = "Tavsiya"
        verbose_name_plural = "Tavsiya qilamiz"


class VenueVendor(Vendor):
    class Meta:
        proxy = True
        verbose_name = "To‘yxona"
        verbose_name_plural = "To‘yxona"


class MediaVendor(Vendor):
    class Meta:
        proxy = True
        verbose_name = "FotoStudio"
        verbose_name_plural = "FotoStudio"


class AttireVendor(Vendor):
    class Meta:
        proxy = True
        verbose_name = "Kelin va kuyov liboslari"
        verbose_name_plural = "Kelin va kuyov liboslari"


class TransportVendor(Vendor):
    class Meta:
        proxy = True
        verbose_name = "Kartej"
        verbose_name_plural = "Kartej"


class McVendor(Vendor):
    class Meta:
        proxy = True
        verbose_name = "Honanda"
        verbose_name_plural = "Honanda"


class DecorVendor(Vendor):
    class Meta:
        proxy = True
        verbose_name = "Dekor va zal bezatish"
        verbose_name_plural = "Dekor va zal bezatish"


class MarryMeVendor(Vendor):
    class Meta:
        proxy = True
        verbose_name = "Marry me joy va taklif"
        verbose_name_plural = "Marry me joy va taklif"


class UserProfile(models.Model):
    """Qo‘shimcha profil — telefon va ism."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField("to‘liq ism", max_length=255, blank=True)
    phone = models.CharField("telefon", max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Foydalanuvchi profili"
        verbose_name_plural = "Foydalanuvchi profillari"

    def __str__(self):
        return self.user.get_username()
