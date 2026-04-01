from django.contrib import admin
from .models import Invoice, InvoiceItem, Payment


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "patient",
        "issue_date",
        "due_date",
        "total_amount",
        "amount_paid",
        "status",
    ]
    list_filter = ["status", "issue_date", "due_date"]
    search_fields = ["invoice_number", "patient__first_name", "patient__last_name"]
    ordering = ["-created_at"]
    readonly_fields = [
        "invoice_number",
        "created_at",
        "updated_at",
        "subtotal",
        "total_amount",
        "amount_paid",
    ]
    inlines = [InvoiceItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "invoice",
        "amount",
        "payment_date",
        "payment_method",
        "recorded_by",
    ]
    list_filter = ["payment_method", "payment_date"]
    search_fields = [
        "invoice__invoice_number",
        "invoice__patient__first_name",
        "invoice__patient__last_name",
    ]
    ordering = ["-payment_date"]
    readonly_fields = ["created_at"]
