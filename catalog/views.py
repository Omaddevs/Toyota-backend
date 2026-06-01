import os
import random
import string
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Exists, F, OuterRef, Prefetch
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend

from .filters import CategoryFilter, VendorFilter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Category, HomePlacement, PhoneOTP, PromoPost, Vendor, VendorReview
from .serializers import (
    CategoryPublicSerializer,
    CategoryWriteSerializer,
    CompleteRegistrationSerializer,
    PromoPostSerializer,
    PromoPostWriteSerializer,
    RegisterSerializer,
    SendOTPSerializer,
    UserAdminSerializer,
    UserSerializer,
    VendorListSerializer,
    VendorSerializer,
    VendorWriteSerializer,
    VerifyOTPSerializer,
)
from .jwt_serializers import ToyTokenObtainPairSerializer


def _send_telegram_message(chat_id, text):
    """Telegram bot orqali xabar yuborish."""
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        return False
    import urllib.request
    import json
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode()
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False


def _generate_otp_code():
    return "".join(random.choices(string.digits, k=6))


class ToyTokenView(TokenObtainPairView):
    serializer_class = ToyTokenObtainPairSerializer


class RegisterView(APIView):
    permission_classes = []

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Barcha kategoriyalar (asosiy + qo‘shimcha)."""

    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategoryPublicSerializer
    lookup_field = "slug"
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Vendor.objects.filter(is_published=True)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "reviews",
                queryset=VendorReview.objects.order_by("-created_at"),
            )
        )
    )
    lookup_field = "code"
    pagination_class = None
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VendorFilter
    search_fields = ["name", "district", "tagline", "description"]
    ordering_fields = ["name", "rating", "sort_order", "review_count_cached"]
    ordering = ["sort_order", "name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return VendorSerializer
        return VendorListSerializer

    @action(detail=True, methods=["post"], url_path="view", permission_classes=[])
    def record_view(self, request, code=None):
        """Sahifa ochilganda ko'rishlar sonini +1 qiladi va yangi sonni qaytaradi."""
        updated = Vendor.objects.filter(
            code=code, is_published=True
        ).update(view_count=F("view_count") + 1)
        if not updated:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        new_count = Vendor.objects.filter(code=code).values_list("view_count", flat=True).first() or 0
        return Response({"view_count": new_count})

class PromoPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PromoPost.objects.filter(is_active=True)
    serializer_class = PromoPostSerializer
    lookup_field = "slug"
    pagination_class = None

class HomeView(APIView):
    """Bosh sahifa bloklari: kategoriyalar, top to‘yxonalar, tavsiya."""

    permission_classes = []

    def get(self, request):
        primary = Category.objects.filter(is_active=True, zone=Category.ZONE_PRIMARY)
        extra = Category.objects.filter(is_active=True, zone=Category.ZONE_EXTRA)
        top_ids = HomePlacement.objects.filter(
            section=HomePlacement.SECTION_TOP_VENUES
        ).order_by("sort_order")
        rec_ids = HomePlacement.objects.filter(
            section=HomePlacement.SECTION_RECOMMENDED
        ).order_by("sort_order")

        top_vendors = []
        for hp in top_ids:
            v = (
                Vendor.objects.filter(pk=hp.vendor_id, is_published=True)
                .select_related("category")
                .first()
            )
            if v:
                top_vendors.append(v)

        rec_vendors = []
        for hp in rec_ids:
            v = (
                Vendor.objects.filter(pk=hp.vendor_id, is_published=True)
                .select_related("category")
                .first()
            )
            if v:
                rec_vendors.append(v)

        return Response(
            {
                "categories_primary": CategoryPublicSerializer(primary, many=True).data,
                "categories_extra": CategoryPublicSerializer(extra, many=True).data,
                "top_venues": VendorListSerializer(top_vendors, many=True).data,
                "recommended": VendorListSerializer(rec_vendors, many=True).data,
            }
        )


class TopVenuesManageView(APIView):
    """Top to‘yxonalarni boshqarish (faqat admin/staff)."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    @staticmethod
    def _vendor_image(request, vendor):
        """Story doirasida ko'rinadigan rasmning to'liq URL manzili."""
        if vendor.image_upload:
            url = vendor.image_upload.url
            return request.build_absolute_uri(url) if request else url
        return vendor.image or ""

    def get(self, request):
        placements = HomePlacement.objects.filter(
            section=HomePlacement.SECTION_TOP_VENUES
        ).select_related("vendor", "vendor__category").order_by("sort_order")
        items = [
            {
                "vendor_code": hp.vendor.code,
                "vendor_name": hp.vendor.name,
                "sort_order": hp.sort_order,
                "story_video_url": hp.vendor.story_video_url or "",
                "image": self._vendor_image(request, hp.vendor),
            }
            for hp in placements
            if hp.vendor.is_published
        ]
        all_venues = Vendor.objects.filter(
            is_published=True
        ).select_related("category").order_by("name")
        venue_options = [
            {
                "code": v.code,
                "name": v.name,
                "category": v.category.title if v.category_id else "",
                "image": self._vendor_image(request, v),
            }
            for v in all_venues
        ]
        return Response({"items": items, "venue_options": venue_options})

    def put(self, request):
        payload = request.data.get("items", [])
        if not isinstance(payload, list):
            return Response(
                {"detail": "`items` list bo‘lishi kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        normalized = []
        seen = set()
        for idx, raw in enumerate(payload):
            if not isinstance(raw, dict):
                return Response(
                    {"detail": f"{idx + 1}-element noto‘g‘ri formatda."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            code = str(raw.get("vendor_code", "")).strip()
            if not code:
                return Response(
                    {"detail": f"{idx + 1}-elementda vendor_code yo‘q."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if code in seen:
                return Response(
                    {"detail": f"Vendor takrorlangan: {code}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            seen.add(code)
            normalized.append(
                {
                    "vendor_code": code,
                    "sort_order": idx,
                    "story_video_url": str(raw.get("story_video_url", "")).strip(),
                    "image": str(raw.get("image", "")).strip(),
                }
            )

        allowed = {
            v.code: v
            for v in Vendor.objects.filter(
                code__in=[it["vendor_code"] for it in normalized],
                is_published=True,
            )
        }
        missing = [it["vendor_code"] for it in normalized if it["vendor_code"] not in allowed]
        if missing:
            return Response(
                {"detail": f"Topilmadi yoki e'lon qilinmagan: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for it in normalized:
                vendor = allowed[it["vendor_code"]]
                update_fields = []
                if vendor.story_video_url != it["story_video_url"]:
                    vendor.story_video_url = it["story_video_url"]
                    update_fields.append("story_video_url")
                # Story doirasi rasmi: admin yangi rasm bersa va u hozirgisidan farq qilsa,
                # uni vendor.image ga yozamiz (image_upload ustun bo'lmasligi uchun tozalaymiz).
                new_image = it["image"]
                if new_image and new_image != self._vendor_image(request, vendor):
                    vendor.image = new_image
                    update_fields.append("image")
                    if vendor.image_upload:
                        vendor.image_upload = None
                        update_fields.append("image_upload")
                if update_fields:
                    update_fields.append("updated_at")
                    vendor.save(update_fields=update_fields)

            HomePlacement.objects.filter(section=HomePlacement.SECTION_TOP_VENUES).delete()
            HomePlacement.objects.bulk_create(
                [
                    HomePlacement(
                        section=HomePlacement.SECTION_TOP_VENUES,
                        sort_order=it["sort_order"],
                        vendor=allowed[it["vendor_code"]],
                    )
                    for it in normalized
                ]
            )

        return self.get(request)


@api_view(["GET"])
@permission_classes([])
def health(request):
    return Response({"status": "ok", "service": "toymakon-backend"})


class IsStaffOrAdmin(IsAdminUser):
    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))


class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def get(self, request):
        vendor_total = Vendor.objects.count()
        vendor_published = Vendor.objects.filter(is_published=True).count()
        category_total = Category.objects.count()
        promo_total = PromoPost.objects.filter(is_active=True).count()
        user_total = User.objects.count()
        review_total = VendorReview.objects.count()

        by_category = (
            Category.objects.annotate(cnt=Count("vendors"))
            .values("code", "title", "short_label", "cnt")
            .order_by("sort_order")
        )

        return Response({
            "vendor_total": vendor_total,
            "vendor_published": vendor_published,
            "category_total": category_total,
            "promo_total": promo_total,
            "user_total": user_total,
            "review_total": review_total,
            "by_category": list(by_category),
        })


class VendorAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    lookup_field = "code"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VendorFilter
    search_fields = ["name", "district", "code", "phone"]
    ordering_fields = ["name", "sort_order", "created_at", "category"]
    ordering = ["category", "sort_order", "name"]
    pagination_class = None

    def get_queryset(self):
        return (
            Vendor.objects
            .select_related("category")
            .prefetch_related("reviews")
            .annotate(
                is_top_venue=Exists(HomePlacement.objects.filter(
                    vendor_id=OuterRef("pk"), section=HomePlacement.SECTION_TOP_VENUES
                )),
                is_recommended=Exists(HomePlacement.objects.filter(
                    vendor_id=OuterRef("pk"), section=HomePlacement.SECTION_RECOMMENDED
                )),
            )
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return VendorWriteSerializer
        return VendorSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class CategoryAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    queryset = Category.objects.annotate(vendor_count=Count("vendors")).order_by("zone", "sort_order")
    lookup_field = "code"
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CategoryWriteSerializer
        return CategoryPublicSerializer


class PromoPostAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    queryset = PromoPost.objects.select_related("category").order_by("sort_order")
    lookup_field = "slug"
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PromoPostWriteSerializer
        return PromoPostSerializer


class ImageUploadView(APIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "Fayl yuklanmadi."}, status=status.HTTP_400_BAD_REQUEST)

        allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if file.content_type not in allowed:
            return Response(
                {"detail": "Faqat JPG, PNG, WebP va GIF formatlar qabul qilinadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile

        ext = os.path.splitext(file.name)[1].lower() or ".jpg"
        import uuid as uuid_mod
        fname = f"vendors/{uuid_mod.uuid4().hex}{ext}"
        path = default_storage.save(fname, ContentFile(file.read()))
        url = request.build_absolute_uri(f"/media/{path}")
        return Response({"url": url}, status=status.HTTP_201_CREATED)


class UserAdminView(APIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def get(self, request):
        users = User.objects.select_related("profile").order_by("-date_joined")
        data = UserAdminSerializer(users, many=True).data
        return Response(data)

    def patch(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        is_staff = request.data.get("is_staff")
        is_active = request.data.get("is_active")
        if is_staff is not None:
            user.is_staff = bool(is_staff)
        if is_active is not None:
            user.is_active = bool(is_active)
        user.save(update_fields=["is_staff", "is_active"])
        return Response(UserAdminSerializer(user).data)


# ─────────────────── OTP VIEWS ───────────────────

class SendOTPView(APIView):
    permission_classes = []

    def post(self, request):
        ser = SendOTPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone"]

        # Avvalgi ishlatilmagan OTPlarni bekor qilamiz
        PhoneOTP.objects.filter(phone=phone, is_used=False).update(is_used=True)

        code = _generate_otp_code()
        expires_at = timezone.now() + timedelta(minutes=10)
        otp = PhoneOTP.objects.create(phone=phone, code=code, expires_at=expires_at)

        bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "ToyMakonBot")

        # Deep link: foydalanuvchi bosib Telegramda "Start" tugmasini bosganda
        # bot /start otp{id} buyrug'ini qabul qiladi va kodni yuboradi
        bot_link = f"https://t.me/{bot_username}?start=otp{otp.id}"

        resp = {
            "phone": phone,
            "bot_link": bot_link,
            "bot_username": bot_username,
            "expires_in": 600,
        }
        if settings.DEBUG:
            resp["debug_code"] = code
        return Response(resp, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = []

    def post(self, request):
        ser = VerifyOTPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone"]
        code = ser.validated_data["code"]

        otp = (
            PhoneOTP.objects.filter(phone=phone, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if not otp:
            return Response(
                {"detail": "Tasdiqlash kodi topilmadi. Qayta so'rang."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if otp.is_expired():
            return Response(
                {"detail": "Tasdiqlash kodi muddati tugagan. Qayta so'rang."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if otp.code != code:
            return Response(
                {"detail": "Tasdiqlash kodi noto'g'ri."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reg_token = uuid.uuid4().hex
        otp.reg_token = reg_token
        otp.save(update_fields=["reg_token"])

        return Response({"phone": phone, "reg_token": reg_token})


class CompleteRegistrationView(APIView):
    permission_classes = []

    def post(self, request):
        ser = CompleteRegistrationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        phone = ser.validated_data["phone"]
        reg_token = ser.validated_data["reg_token"]

        otp = PhoneOTP.objects.filter(
            phone=phone, reg_token=reg_token, is_used=False
        ).first()

        if not otp or otp.is_expired():
            return Response(
                {"detail": "Tasdiqlash sessiyasi yaroqsiz. Qayta boshlang."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = ser.validated_data["username"]
        password = ser.validated_data["password"]
        full_name = ser.validated_data.get("full_name", "")

        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password)
            from .models import UserProfile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"full_name": full_name.strip(), "phone": phone},
            )
            otp.is_used = True
            otp.save(update_fields=["is_used"])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TelegramWebhookView(APIView):
    """Telegram bot webhook — foydalanuvchidan /verify {phone} buyrug'ini qabul qiladi."""

    permission_classes = []

    def post(self, request):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            return Response({"ok": True})

        update = request.data
        message = update.get("message") or update.get("edited_message")
        if not message:
            return Response({"ok": True})

        chat_id = message.get("chat", {}).get("id")
        text = (message.get("text") or "").strip()

        if not chat_id:
            return Response({"ok": True})

        if text.startswith("/start"):
            # Deep link: /start otp{id}
            parts = text.split(maxsplit=1)
            param = parts[1].strip() if len(parts) > 1 else ""
            if param.startswith("otp"):
                try:
                    otp_id = int(param[3:])
                    otp = PhoneOTP.objects.get(id=otp_id, is_used=False)
                except (ValueError, PhoneOTP.DoesNotExist):
                    _send_telegram_message(
                        chat_id,
                        "❌ Tasdiqlash kodi topilmadi yoki muddati o'tgan. Qaytadan ro'yxatdan o'ting."
                    )
                    return Response({"ok": True})

                if otp.is_expired():
                    _send_telegram_message(
                        chat_id,
                        "⏰ Tasdiqlash kodining muddati o'tib ketdi. Qaytadan ro'yxatdan o'ting."
                    )
                    return Response({"ok": True})

                otp.telegram_chat_id = chat_id
                otp.save(update_fields=["telegram_chat_id"])

                _send_telegram_message(
                    chat_id,
                    f"🔐 Sizning tasdiqlash kodingiz:\n\n"
                    f"<b>{otp.code}</b>\n\n"
                    f"Bu kodni ToyMakon saytiga kiriting.\n"
                    f"Kod 10 daqiqa amal qiladi."
                )
            else:
                welcome = (
                    f"👋 Assalomu alaykum! <b>ToyMakon</b> botiga xush kelibsiz!\n\n"
                    f"Bu bot orqali ro'yxatdan o'tish uchun tasdiqlash kodini olasiz.\n"
                    f"ToyMakon saytiga o'ting va ro'yxatdan o'tish tugmasini bosing."
                )
                _send_telegram_message(chat_id, welcome)
            return Response({"ok": True})

        _send_telegram_message(
            chat_id,
            "❓ Buyruq tanilmadi. ToyMakon saytidan ro'yxatdan o'ting."
        )

        return Response({"ok": True})


# ─────────────────── RECOMMENDED MANAGE ───────────────────

class RecommendedManageView(APIView):
    """Tavsiya qilamiz vendorlarni boshqarish (faqat admin/staff)."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        placements = HomePlacement.objects.filter(
            section=HomePlacement.SECTION_RECOMMENDED
        ).select_related("vendor", "vendor__category").order_by("sort_order")
        items = [
            {
                "vendor_code": hp.vendor.code,
                "vendor_name": hp.vendor.name,
                "vendor_image": hp.vendor.image or "",
                "vendor_category": hp.vendor.category.title if hp.vendor.category else "",
                "sort_order": hp.sort_order,
            }
            for hp in placements
            if hp.vendor.is_published
        ]
        all_vendors = Vendor.objects.filter(is_published=True).order_by("category", "name")
        vendor_options = [
            {
                "code": v.code,
                "name": v.name,
                "category": v.category.title if v.category else "",
            }
            for v in all_vendors
        ]
        return Response({"items": items, "vendor_options": vendor_options})

    def put(self, request):
        payload = request.data.get("items", [])
        if not isinstance(payload, list):
            return Response({"detail": "`items` list bo'lishi kerak."}, status=status.HTTP_400_BAD_REQUEST)

        normalized = []
        seen = set()
        for idx, raw in enumerate(payload):
            if not isinstance(raw, dict):
                return Response({"detail": f"{idx + 1}-element noto'g'ri."}, status=status.HTTP_400_BAD_REQUEST)
            code = str(raw.get("vendor_code", "")).strip()
            if not code:
                return Response({"detail": f"{idx + 1}-elementda vendor_code yo'q."}, status=status.HTTP_400_BAD_REQUEST)
            if code in seen:
                return Response({"detail": f"Vendor takrorlangan: {code}"}, status=status.HTTP_400_BAD_REQUEST)
            seen.add(code)
            normalized.append({"vendor_code": code, "sort_order": idx})

        allowed = {
            v.code: v
            for v in Vendor.objects.filter(
                code__in=[it["vendor_code"] for it in normalized],
                is_published=True,
            )
        }
        missing = [it["vendor_code"] for it in normalized if it["vendor_code"] not in allowed]
        if missing:
            return Response({"detail": f"Topilmadi: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            HomePlacement.objects.filter(section=HomePlacement.SECTION_RECOMMENDED).delete()
            HomePlacement.objects.bulk_create([
                HomePlacement(
                    section=HomePlacement.SECTION_RECOMMENDED,
                    sort_order=it["sort_order"],
                    vendor=allowed[it["vendor_code"]],
                )
                for it in normalized
            ])

        return self.get(request)
