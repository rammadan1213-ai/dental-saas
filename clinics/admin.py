from django.contrib import admin
from .models import Clinic, Subscription


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "owner__username", "email"]
    raw_id_fields = ["owner"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "clinic",
        "plan",
        "is_active",
        "start_date",
        "expiry_date",
        "is_expired",
    ]
    list_filter = ["plan", "is_active", "start_date", "expiry_date"]
    search_fields = ["clinic__name", "stripe_customer_id"]
    raw_id_fields = ["clinic"]
