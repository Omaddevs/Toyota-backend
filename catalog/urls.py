from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register("categories", views.CategoryViewSet, basename="category")
router.register("vendors", views.VendorViewSet, basename="vendor")
router.register("promo-posts", views.PromoPostViewSet, basename="promopost")

urlpatterns = [
    path("", include(router.urls)),
    path("home/", views.HomeView.as_view()),
    path("admin/top-venues/", views.TopVenuesManageView.as_view()),
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/token/", views.ToyTokenView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", views.MeView.as_view()),
    path("health/", views.health),
]
