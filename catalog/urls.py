from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register("categories", views.CategoryViewSet, basename="category")
router.register("vendors", views.VendorViewSet, basename="vendor")
router.register("promo-posts", views.PromoPostViewSet, basename="promopost")

# Admin CRUD routers
router.register("admin/vendors", views.VendorAdminViewSet, basename="admin-vendor")
router.register("admin/categories", views.CategoryAdminViewSet, basename="admin-category")
router.register("admin/promo-posts", views.PromoPostAdminViewSet, basename="admin-promopost")

urlpatterns = [
    path("", include(router.urls)),
    path("home/", views.HomeView.as_view()),
    path("admin/top-venues/", views.TopVenuesManageView.as_view()),
    path("admin/stats/", views.AdminStatsView.as_view()),
    path("admin/upload/", views.ImageUploadView.as_view()),
    path("admin/users/", views.UserAdminView.as_view()),
    path("admin/users/<int:user_id>/", views.UserAdminView.as_view()),
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/token/", views.ToyTokenView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", views.MeView.as_view()),
    path("health/", views.health),
]
