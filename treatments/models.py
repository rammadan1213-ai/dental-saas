from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from patients.models import Patient
from appointments.models import Appointment
from billing.models import Invoice


class DentalService(models.Model):
    class Category(models.TextChoices):
        PREVENTIVE = "preventive", _("Preventive")
        RESTORATIVE = "restorative", _("Restorative")
        ENDODONTICS = "endodontics", _("Endodontics (RCT)")
        PERIODONTICS = "periodontics", _("Periodontics")
        PROSTHODONTICS = "prosthodontics", _("Prosthodontics")
        ORAL_SURGERY = "oral_surgery", _("Oral Surgery")
        ORTHODONTICS = "orthodontics", _("Orthodontics")
        COSMETIC = "cosmetic", _("Cosmetic")
        EMERGENCY = "emergency", _("Emergency")
        OTHER = "other", _("Other")

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=Category.choices)
    default_price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    requires_appointment = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]
        verbose_name = _("Dental Service")
        verbose_name_plural = _("Dental Services")

    def __str__(self):
        return f"{self.name} - ${self.default_price}"


class Treatment(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", _("Planned")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="treatments",
        null=True,
        blank=True,
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="treatments"
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="treatments",
    )
    dental_service = models.ForeignKey(
        DentalService,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="treatments",
    )
    dentist = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="treatments"
    )
    diagnosis = models.TextField()
    procedure = models.TextField()
    tooth_number = models.CharField(
        max_length=50, blank=True, help_text=_("Affected tooth/teeth")
    )
    anesthesia_used = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNED
    )
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    treatment_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-treatment_date"]
        verbose_name = _("Treatment")
        verbose_name_plural = _("Treatments")

    def __str__(self):
        return f"{self.patient.full_name} - {self.procedure[:50]}"

    def save(self, *args, **kwargs):
        if self.dental_service and not self.cost:
            self.cost = self.dental_service.default_price
        super().save(*args, **kwargs)
