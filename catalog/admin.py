from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    AttireVendor,
    Category,
    DecorVendor,
    HomePlacement,
    MarryMeVendor,
    McVendor,
    MediaVendor,
    PromoPost,
    RecommendedPlacement,
    TopVenuePlacement,
    TransportVendor,
    UserProfile,
    Vendor,
    VenueVendor,
    VendorReview,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "title",
        "short_label",
        "zone",
        "sort_order",
        "is_active",
        "vendor_count",
    )
    list_filter = ("zone", "is_active")
    search_fields = ("code", "title", "slug", "short_label")
    ordering = ("zone", "sort_order")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("code", "slug", "title", "short_label", "subtitle")}),
        ("Ko‘rinish", {"fields": ("icon", "search_hint", "zone", "sort_order", "is_active")}),
    )

    @admin.display(description="Vendorlar")
    def vendor_count(self, obj):
        return obj.vendors.count()


class VendorReviewInline(admin.TabularInline):
    model = VendorReview
    extra = 0
    fields = ("author", "rating", "text", "date")


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "category",
        "district",
        "is_published",
        "rating",
        "review_count_cached",
        "sort_order",
    )
    list_filter = ("category", "is_published", "district")
    search_fields = ("code", "name", "slug", "district", "phone", "telegram", "story_video_url")
    ordering = ("category", "sort_order", "name")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("review_count_cached", "id")
    inlines = [VendorReviewInline]
    fieldsets = (
        (
            "Asosiy",
            {
                "fields": (
                    "id",
                    "code",
                    "category",
                    "slug",
                    "name",
                    "is_published",
                    "sort_order",
                )
            },
        ),
        (
            "Media va narx",
            {
                "fields": (
                    "image",
                    "image_upload",
                    "story_video_url",
                    "gallery",
                    "price_label",
                    "price_note",
                    "badge",
                    "footer_line",
                    "footer_icon",
                )
            },
        ),
        (
            "Aloqa va joy",
            {"fields": ("district", "phone", "telegram", "location", "tagline", "description")},
        ),
        ("Reyting (sharhlar bilan yangilanadi)", {"fields": ("rating", "review_count_cached")}),
        ("Qo‘shimcha", {"fields": ("specs",)}),
    )
    actions = ["make_published", "make_unpublished", "recalculate_ratings"]

    @admin.action(description="Tanlanganlarni saytda ko‘rsatish")
    def make_published(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, f"{queryset.count()} ta vendor faollashtirildi.")

    @admin.action(description="Tanlanganlarni yashirish")
    def make_unpublished(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, f"{queryset.count()} ta vendor yashirildi.")

    @admin.action(description="Reyting va sharhlar sonini qayta hisoblash")
    def recalculate_ratings(self, request, queryset):
        for v in queryset:
            v.refresh_review_stats()
        self.message_user(request, "Yangilandi.", level=messages.SUCCESS)


@admin.register(VendorReview)
class VendorReviewAdmin(admin.ModelAdmin):
    list_display = ("author", "vendor", "rating", "date", "created_at")
    list_filter = ("rating",)
    search_fields = ("author", "text", "vendor__name")


@admin.register(PromoPost)
class PromoPostAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "badge", "sort_order", "view_count", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "slug", "path")
    ordering = ("sort_order",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(HomePlacement)
class HomePlacementAdmin(admin.ModelAdmin):
    list_display = ("section", "sort_order", "vendor", "vendor_category")
    list_filter = ("section",)
    search_fields = ("vendor__name", "vendor__code")
    ordering = ("section", "sort_order")

    @admin.display(description="Kategoriya")
    def vendor_category(self, obj):
        return obj.vendor.category_id


@admin.register(TopVenuePlacement)
class TopVenuePlacementAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "vendor", "vendor_category")
    search_fields = ("vendor__name", "vendor__code")
    ordering = ("sort_order",)
    fields = ("sort_order", "vendor")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(section=HomePlacement.SECTION_TOP_VENUES)

    def save_model(self, request, obj, form, change):
        obj.section = HomePlacement.SECTION_TOP_VENUES
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "vendor":
            kwargs["queryset"] = Vendor.objects.filter(category_id="venue").order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description="Kategoriya")
    def vendor_category(self, obj):
        return obj.vendor.category_id


@admin.register(RecommendedPlacement)
class RecommendedPlacementAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "vendor", "vendor_category")
    search_fields = ("vendor__name", "vendor__code")
    ordering = ("sort_order",)
    fields = ("sort_order", "vendor")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(section=HomePlacement.SECTION_RECOMMENDED)

    def save_model(self, request, obj, form, change):
        obj.section = HomePlacement.SECTION_RECOMMENDED
        super().save_model(request, obj, form, change)

    @admin.display(description="Kategoriya")
    def vendor_category(self, obj):
        return obj.vendor.category_id


class _CategoryVendorProxyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "district", "is_published", "sort_order")
    search_fields = ("code", "name", "district", "phone")
    ordering = ("sort_order", "name")

    category_code = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.category_code:
            qs = qs.filter(category_id=self.category_code)
        return qs


@admin.register(VenueVendor)
class VenueVendorAdmin(_CategoryVendorProxyAdmin):
    category_code = "venue"


@admin.register(MediaVendor)
class MediaVendorAdmin(_CategoryVendorProxyAdmin):
    category_code = "media"


@admin.register(AttireVendor)
class AttireVendorAdmin(_CategoryVendorProxyAdmin):
    category_code = "attire"


@admin.register(TransportVendor)
class TransportVendorAdmin(_CategoryVendorProxyAdmin):
    category_code = "transport"


@admin.register(McVendor)
class McVendorAdmin(_CategoryVendorProxyAdmin):
    category_code = "mc"


@admin.register(DecorVendor)
class DecorVendorAdmin(_CategoryVendorProxyAdmin):
    category_code = "decor"


@admin.register(MarryMeVendor)
class MarryMeVendorAdmin(_CategoryVendorProxyAdmin):
    category_code = "marryme"


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


def _custom_get_app_list(request, app_label=None):
    app_list = admin.AdminSite.get_app_list(admin.site, request, app_label)
    for app in app_list:
        if app.get("app_label") != "catalog":
            continue
        models = app.get("models", [])
        hidden_duplicates = {
            "vendor",
            "homeplacement",
        }
        models = [m for m in models if m.get("object_name", "").lower() not in hidden_duplicates]
        order = {
            "category": 0,
            "promopost": 1,
            "vendorreview": 2,
            "topvenueplacement": 100,  # Bosh sahifa joylashuvlaridan keyin
            "recommendedplacement": 101,
            "venuevendor": 102,
            "mediavendor": 103,
            "attirevendor": 104,
            "transportvendor": 105,
            "mcvendor": 106,
            "decorvendor": 107,
            "marrymevendor": 108,
        }
        app["models"] = sorted(
            models,
            key=lambda m: (order.get(m.get("object_name", "").lower(), 50), m.get("name", "")),
        )
    return app_list


admin.site.get_app_list = _custom_get_app_list

admin.site.site_header = "ToyMakon boshqaruvi"
admin.site.site_title = "ToyMakon"
admin.site.index_title = "Ma’lumotlar bazasi"
