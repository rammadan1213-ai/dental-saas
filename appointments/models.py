from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from patients.models import Patient


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")
        NO_SHOW = "no_show", _("No Show")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="appointments",
        null=True,
        blank=True,
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="appointments"
    )
    dentist = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="appointments"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    reason = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start_time"]
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")

    def __str__(self):
        return f"{self.patient.full_name} - {self.date} {self.start_time}"

    @property
    def duration(self):
        from datetime import datetime, timedelta

        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        return (end - start).seconds / 60


class AppointmentReminder(models.Model):
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="reminders"
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=[
            ("email", _("Email")),
            ("sms", _("SMS")),
        ],
    )
    scheduled_time = models.DateTimeField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scheduled_time"]
