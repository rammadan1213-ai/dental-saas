from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AuditLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "created_at",
    ]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-created_at"]

    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Info",
            {"fields": ("role", "phone", "address", "specialty", "license_number")},
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("role", "email", "phone", "address")}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "model_name", "timestamp", "ip_address"]
    list_filter = ["action", "model_name", "timestamp"]
    search_fields = ["user__username", "description"]
    readonly_fields = [
        "user",
        "action",
        "model_name",
        "object_id",
        "description",
        "ip_address",
        "timestamp",
    ]
    ordering = ["-timestamp"]
