from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.urls import path

from .models import UserNotification

User = get_user_model()


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    change_list_template = "admin/notifications/usernotification/change_list.html"
    list_display = ("title", "user", "read_at", "created_at", "created_by")
    list_filter = ("created_at",)
    search_fields = ("title", "body", "user__username")
    readonly_fields = ("created_at",)
    # raw_id_fields o‘rniga oddiy tanlov: foydalanuvchilar ro‘yxati username bo‘yicha ko‘rinadi
    autocomplete_fields = ("created_by",)

    fieldsets = (
        (None, {"fields": ("user", "title", "body", "read_at")}),
        ("Meta", {"fields": ("created_by", "created_at"), "classes": ("collapse",)}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(is_active=True).order_by("username")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        opts = self.model._meta
        custom = [
            path(
                "broadcast/",
                self.admin_site.admin_view(self.broadcast_view),
                name=f"{opts.app_label}_{opts.model_name}_broadcast",
            ),
        ]
        return custom + urls

    def broadcast_view(self, request):
        if request.method == "POST":
            title = (request.POST.get("title") or "").strip()
            body = (request.POST.get("body") or "").strip()
            raw_ids = request.POST.getlist("users")
            user_ids = []
            seen = set()
            for x in raw_ids:
                s = (x or "").strip()
                if s.isdigit():
                    pk = int(s)
                    if pk not in seen:
                        seen.add(pk)
                        user_ids.append(pk)
            if not title or not body:
                messages.error(request, "Sarlavha va matn majburiy.")
            elif not user_ids:
                messages.error(request, "Kamida bitta foydalanuvchi tanlang.")
            else:
                valid_set = set(
                    User.objects.filter(is_active=True, pk__in=user_ids).values_list("pk", flat=True)
                )
                ordered_ids = [uid for uid in user_ids if uid in valid_set]
                if not ordered_ids:
                    messages.error(request, "Tanlangan foydalanuvchilar topilmadi.")
                else:
                    rows = [
                        UserNotification(
                            user_id=uid,
                            title=title,
                            body=body,
                            created_by=request.user if request.user.is_authenticated else None,
                        )
                        for uid in ordered_ids
                    ]
                    UserNotification.objects.bulk_create(rows)
                    messages.success(request, f"{len(rows)} ta bildirishnoma yuborildi.")
                    return redirect("admin:notifications_usernotification_changelist")

        users = User.objects.filter(is_active=True).order_by("username")
        context = {
            **self.admin_site.each_context(request),
            "title": "Bildirishnomani yuborish",
            "users": users,
            "opts": self.model._meta,
        }
        return render(request, "admin/notifications/broadcast.html", context)
