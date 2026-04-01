from django.contrib import admin
from .models import PaymentRecord


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ["id", "subscription", "plan", "amount", "status", "created_at"]
    list_filter = ["status", "plan", "created_at"]
    search_fields = ["stripe_session_id", "stripe_payment_intent_id"]
    readonly_fields = [
        "stripe_session_id",
        "stripe_payment_intent_id",
        "created_at",
        "updated_at",
    ]
