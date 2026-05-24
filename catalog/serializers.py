from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Category, PhoneOTP, PromoPost, UserProfile, Vendor, VendorReview





class CategoryPublicSerializer(serializers.ModelSerializer):
    """Frontend `catalog.js` bilan mos kalitlar."""

    id = serializers.CharField(source="code", read_only=True)
    shortLabel = serializers.CharField(source="short_label")
    searchHint = serializers.CharField(source="search_hint", allow_blank=True)

    class Meta:
        model = Category
        fields = (
            "id",
            "slug",
            "title",
            "shortLabel",
            "subtitle",
            "icon",
            "searchHint",
            "zone",
            "sort_order",
        )


class VendorReviewPublicSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = VendorReview
        fields = ("id", "author", "rating", "text", "date")


class VendorSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    categoryId = serializers.CharField(source="category_id", read_only=True)
    priceLabel = serializers.CharField(source="price_label")
    priceNote = serializers.CharField(source="price_note", allow_blank=True)
    footerLine = serializers.CharField(source="footer_line", allow_blank=True)
    footerIcon = serializers.CharField(source="footer_icon", allow_blank=True)
    reviewCount = serializers.IntegerField(source="review_count_cached", read_only=True)
    storyVideoUrl = serializers.CharField(source="story_video_url", allow_blank=True)
    rating = serializers.FloatField()
    reviews = VendorReviewPublicSerializer(many=True, read_only=True)
    id = serializers.CharField(source="code", read_only=True)
    is_top_venue = serializers.SerializerMethodField()
    is_recommended = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = (
            "id",
            "categoryId",
            "slug",
            "name",
            "district",
            "image",
            "storyVideoUrl",
            "gallery",
            "priceLabel",
            "priceNote",
            "badge",
            "footerLine",
            "footerIcon",
            "phone",
            "rating",
            "reviewCount",
            "tagline",
            "location",
            "telegram",
            "reviews",
            "description",
            "specs",
            "view_count",
            "is_published",
            "sort_order",
            "lat",
            "lng",
            "map_link",
            "is_top_venue",
            "is_recommended",
        )

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image_upload:
            url = obj.image_upload.url
            return request.build_absolute_uri(url) if request else url
        return obj.image

    def get_is_top_venue(self, obj):
        return getattr(obj, "is_top_venue", False)

    def get_is_recommended(self, obj):
        return getattr(obj, "is_recommended", False)


class VendorListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    categoryId = serializers.CharField(source="category_id", read_only=True)
    priceLabel = serializers.CharField(source="price_label")
    priceNote = serializers.CharField(source="price_note", allow_blank=True)
    footerLine = serializers.CharField(source="footer_line", allow_blank=True)
    footerIcon = serializers.CharField(source="footer_icon", allow_blank=True)
    reviewCount = serializers.IntegerField(source="review_count_cached", read_only=True)
    storyVideoUrl = serializers.CharField(source="story_video_url", allow_blank=True)
    rating = serializers.FloatField()
    id = serializers.CharField(source="code", read_only=True)

    class Meta:
        model = Vendor
        fields = (
            "id",
            "categoryId",
            "slug",
            "name",
            "district",
            "image",
            "storyVideoUrl",
            "gallery",
            "priceLabel",
            "priceNote",
            "badge",
            "footerLine",
            "footerIcon",
            "phone",
            "rating",
            "reviewCount",
            "tagline",
            "location",
            "telegram",
            "description",
            "specs",
            "view_count",
            "lat",
            "lng",
            "map_link",
        )

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image_upload:
            url = obj.image_upload.url
            return request.build_absolute_uri(url) if request else url
        return obj.image


class PromoPostSerializer(serializers.ModelSerializer):
    categoryId = serializers.CharField(source="category_id", read_only=True)

    class Meta:
        model = PromoPost
        fields = (
            "slug",
            "categoryId",
            "badge",
            "title",
            "path",
            "background_url",
            "sort_order",
        )


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "is_staff",
        )

    def get_full_name(self, obj):
        p = getattr(obj, "profile", None)
        return (getattr(p, "full_name", None) or "").strip()

    def get_phone(self, obj):
        p = getattr(obj, "profile", None)
        return (getattr(p, "phone", None) or "").strip()


class VendorWriteSerializer(serializers.ModelSerializer):
    """Admin: vendor yaratish va tahrirlash."""

    gallery = serializers.JSONField(required=False, default=list)
    specs = serializers.JSONField(required=False, default=list)

    class Meta:
        model = Vendor
        fields = (
            "code", "category", "slug", "name", "district",
            "image", "story_video_url", "gallery",
            "price_label", "price_note", "badge",
            "footer_line", "footer_icon", "phone", "telegram",
            "tagline", "location", "description", "specs",
            "is_published", "sort_order",
            "lat", "lng", "map_link",
        )
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
            "district": {"required": False, "allow_blank": True},
            "image": {"required": False, "allow_blank": True},
            "story_video_url": {"required": False, "allow_blank": True},
            "price_label": {"required": False, "allow_blank": True},
            "price_note": {"required": False, "allow_blank": True},
            "badge": {"required": False, "allow_blank": True, "allow_null": True},
            "footer_line": {"required": False, "allow_blank": True},
            "footer_icon": {"required": False, "allow_blank": True},
            "phone": {"required": False, "allow_blank": True},
            "telegram": {"required": False, "allow_blank": True},
            "tagline": {"required": False, "allow_blank": True},
            "location": {"required": False, "allow_blank": True},
            "description": {"required": False, "allow_blank": True},
            "map_link": {"required": False, "allow_blank": True},
            "lat": {"required": False, "allow_null": True},
            "lng": {"required": False, "allow_null": True},
        }

    def validate_code(self, value):
        instance = getattr(self, "instance", None)
        qs = Vendor.objects.filter(code=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu kod allaqachon mavjud.")
        return value


class CategoryWriteSerializer(serializers.ModelSerializer):
    """Admin: kategoriya yaratish va tahrirlash."""

    class Meta:
        model = Category
        fields = (
            "code", "slug", "title", "short_label", "subtitle",
            "icon", "search_hint", "zone", "sort_order", "is_active",
        )
        extra_kwargs = {
            "subtitle": {"required": False, "allow_blank": True},
            "icon": {"required": False, "allow_blank": True},
            "search_hint": {"required": False, "allow_blank": True},
        }


class PromoPostWriteSerializer(serializers.ModelSerializer):
    """Admin: promo post yaratish va tahrirlash."""

    class Meta:
        model = PromoPost
        fields = (
            "slug", "category", "badge", "title", "path",
            "background_url", "sort_order", "is_active",
        )
        extra_kwargs = {
            "badge": {"required": False, "allow_blank": True},
        }


class UserAdminSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name",
                  "full_name", "phone", "is_staff", "is_active", "date_joined")

    def get_full_name(self, obj):
        p = getattr(obj, "profile", None)
        return (getattr(p, "full_name", None) or "").strip()

    def get_phone(self, obj):
        p = getattr(obj, "profile", None)
        return (getattr(p, "phone", None) or "").strip()


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)

    def validate_phone(self, value):
        import re
        clean = re.sub(r"[\s\-\(\)]", "", value)
        if not re.match(r"^\+?[0-9]{9,15}$", clean):
            raise serializers.ValidationError("Telefon raqam noto'g'ri formatda.")
        return clean


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    code = serializers.CharField(max_length=6, min_length=4)


class CompleteRegistrationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    reg_token = serializers.CharField(max_length=64)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6, max_length=128)
    password_confirm = serializers.CharField(write_only=True, min_length=6, max_length=128)
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu foydalanuvchi nomi band.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Parollar mos emas."})
        return attrs


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6, max_length=128)
    password_confirm = serializers.CharField(write_only=True, min_length=6, max_length=128)
    email = serializers.EmailField(required=False, allow_blank=True)
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=32)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu foydalanuvchi nomi band.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Parollar mos emas."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        full_name = validated_data.pop("full_name", "") or ""
        phone = validated_data.pop("phone", "") or ""
        email = validated_data.pop("email", "") or ""
        user = User.objects.create_user(
            username=validated_data["username"],
            password=password,
            email=email,
        )
        UserProfile.objects.update_or_create(
            user=user,
            defaults={"full_name": full_name.strip(), "phone": phone.strip()},
        )
        return user

