from django.contrib import admin
from .models import Appointment, AppointmentReminder


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "patient",
        "dentist",
        "date",
        "start_time",
        "status",
        "priority",
        "created_at",
    ]
    list_filter = ["status", "priority", "date", "dentist"]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__phone",
        "reason",
    ]
    ordering = ["-date", "-start_time"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "date"


@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = ["appointment", "reminder_type", "scheduled_time", "sent"]
    list_filter = ["reminder_type", "sent", "scheduled_time"]
    search_fields = [
        "appointment__patient__first_name",
        "appointment__patient__last_name",
    ]
