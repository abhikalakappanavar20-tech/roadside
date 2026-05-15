from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, ServiceRequest, ServiceHistory, ProviderLocation


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_role",
        "is_staff",
    )
    list_filter = BaseUserAdmin.list_filter + ("profile__role",)

    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, "profile") else "N/A"

    get_role.short_description = "Role"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone_number", "service_type", "is_available")
    list_filter = ["role", "service_type", "is_available"]
    search_fields = ["user__username", "user__email", "phone_number"]


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "request_id",
        "user",
        "service_type",
        "status",
        "assigned_provider",
        "created_at",
    )
    list_filter = ["status", "service_type", "created_at"]
    search_fields = ["request_id", "user__username", "location_address"]
    readonly_fields = ["request_id", "created_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("request_id", "user", "service_type", "status")},
        ),
        (
            "Location Details",
            {"fields": ("location_lat", "location_long", "location_address")},
        ),
        ("Provider Assignment", {"fields": ("assigned_provider",)}),
        ("Issue Details", {"fields": ("issue_description",)}),
        ("Photos", {"fields": ("customer_photo",)}),
        ("Payment", {"fields": ("estimated_cost", "final_cost")}),
        (
            "Timestamps",
            {
                "fields": ("created_at", "accepted_at", "started_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ServiceHistory)
class ServiceHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "service_request",
        "provider",
        "amount",
        "payment_status",
        "rating",
        "paid_at",
    )
    list_filter = ["payment_status", "rating", "paid_at"]
    search_fields = ["service_request__request_id", "provider__username"]


@admin.register(ProviderLocation)
class ProviderLocationAdmin(admin.ModelAdmin):
    list_display = ("provider", "latitude", "longitude", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ["provider__username"]


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
