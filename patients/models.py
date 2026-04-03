from django.db import models
from django.utils.translation import gettext_lazy as _


class Patient(models.Model):
    GENDER_CHOICES = [
        ("male", _("Male")),
        ("female", _("Female")),
        ("other", _("Other")),
    ]

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="patients",
        null=True,
        blank=True,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    age = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("Age in years")
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    blood_type = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True, help_text=_("List any known allergies"))
    medical_history = models.TextField(
        blank=True, help_text=_("Past medical conditions")
    )
    medications = models.TextField(blank=True, help_text=_("Current medications"))
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Patient")
        verbose_name_plural = _("Patients")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def calculate_age(self):
        if self.age:
            return self.age
        if not self.date_of_birth:
            return None
        from datetime import date

        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )


class PatientDocument(models.Model):
    DOCUMENT_TYPES = [
        ("xray", _("X-Ray")),
        ("report", _("Medical Report")),
        ("prescription", _("Prescription")),
        ("other", _("Other")),
    ]

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="patient_documents",
        null=True,
        blank=True,
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="patient_documents/")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Patient Document")
        verbose_name_plural = _("Patient Documents")

    def __str__(self):
        return f"{self.patient} - {self.title}"
