from django.db import models
from django.conf import settings


class Clinic(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_clinic"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    PLAN_CHOICES = [
        ("basic", "Basic - $10/month"),
        ("pro", "Pro - $25/month"),
        ("enterprise", "Enterprise - $50/month"),
    ]

    clinic = models.OneToOneField(
        Clinic, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="basic")
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    stripe_customer_id = models.CharField(max_length=100, blank=True)

    trial_end = models.DateTimeField(null=True, blank=True)
    is_on_trial = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.clinic.name} - {self.get_plan_display()}"

    @property
    def is_expired(self):
        from datetime import date

        return self.expiry_date < date.today()

    def is_trial_active(self):
        from django.utils import timezone
        from datetime import date

        if not self.trial_end:
            return False
        return self.trial_end >= date.today()

    def can_access_billing(self):
        return self.plan in ["pro", "enterprise"]

    def can_access_reports(self):
        return self.plan in ["pro", "enterprise"]

    def can_access_analytics(self):
        return self.plan == "enterprise"

    @property
    def patient_limit(self):
        limits = {
            "basic": 500,
            "pro": 10000,
            "enterprise": 999999999,
        }
        return limits.get(self.plan, 500)

    def can_add_patient(self):
        from patients.models import Patient

        current_count = Patient.objects.filter(clinic=self.clinic).count()
        return current_count < self.patient_limit
