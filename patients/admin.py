from django.contrib import admin
from .models import Patient, PatientDocument


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "phone",
        "email",
        "date_of_birth",
        "gender",
        "is_active",
        "created_at",
    ]
    list_filter = ["gender", "is_active", "created_at"]
    search_fields = ["first_name", "last_name", "phone", "email"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = ["patient", "document_type", "title", "created_at"]
    list_filter = ["document_type", "created_at"]
    search_fields = ["patient__first_name", "patient__last_name", "title"]
    ordering = ["-created_at"]
