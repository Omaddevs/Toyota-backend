from django.db import transaction
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend

from .filters import CategoryFilter, VendorFilter
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Category, HomePlacement, PromoPost, Vendor, VendorReview
from .serializers import (
    CategoryPublicSerializer,
    PromoPostSerializer,
    RegisterSerializer,
    UserSerializer,
    VendorListSerializer,
    VendorSerializer,
)
from .jwt_serializers import ToyTokenObtainPairSerializer


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


class PromoPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PromoPost.objects.filter(is_active=True)
    serializer_class = PromoPostSerializer
    lookup_field = "slug"
    pagination_class = None

    @action(detail=True, methods=["post"], permission_classes=[])
    def record_view(self, request, slug=None):
        post = self.get_object()
        PromoPost.objects.filter(pk=post.pk).update(view_count=post.view_count + 1)
        post.refresh_from_db(fields=["view_count"])
        return Response(PromoPostSerializer(post).data)


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
                Vendor.objects.filter(
                    pk=hp.vendor_id, is_published=True, category_id="venue"
                )
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
            }
            for hp in placements
            if hp.vendor.is_published and hp.vendor.category_id == "venue"
        ]
        all_venues = Vendor.objects.filter(
            is_published=True, category_id="venue"
        ).order_by("name")
        venue_options = [{"code": v.code, "name": v.name} for v in all_venues]
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
                }
            )

        allowed = {
            v.code: v
            for v in Vendor.objects.filter(
                code__in=[it["vendor_code"] for it in normalized],
                is_published=True,
                category_id="venue",
            )
        }
        missing = [it["vendor_code"] for it in normalized if it["vendor_code"] not in allowed]
        if missing:
            return Response(
                {"detail": f"Topilmadi yoki venue emas: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for it in normalized:
                vendor = allowed[it["vendor_code"]]
                if vendor.story_video_url != it["story_video_url"]:
                    vendor.story_video_url = it["story_video_url"]
                    vendor.save(update_fields=["story_video_url", "updated_at"])

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
