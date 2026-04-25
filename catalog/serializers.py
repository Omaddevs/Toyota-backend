from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Category, PromoPost, UserProfile, Vendor, VendorReview


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
        )

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image_upload:
            url = obj.image_upload.url
            return request.build_absolute_uri(url) if request else url
        return obj.image


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

