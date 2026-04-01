from django.contrib import admin
from .models import Treatment, TreatmentTemplate


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = [
        "patient",
        "dentist",
        "procedure",
        "tooth_number",
        "status",
        "cost",
        "treatment_date",
    ]
    list_filter = ["status", "treatment_date", "dentist"]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "procedure",
        "diagnosis",
    ]
    ordering = ["-treatment_date"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TreatmentTemplate)
class TreatmentTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "default_cost", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "description", "category"]
