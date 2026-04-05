from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


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

    TRIAL_DAYS = 3  # 3 days trial

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
    is_trial_expired = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.clinic.name} - {self.get_plan_display()}"

    def start_trial(self):
        """Start a 3-day trial period"""
        self.is_on_trial = True
        self.trial_end = timezone.now() + timedelta(days=self.TRIAL_DAYS)
        self.is_active = True
        self.save()

    @property
    def days_remaining(self):
        """Get remaining trial days"""
        if not self.is_on_trial or not self.trial_end:
            return 0
        remaining = self.trial_end - timezone.now()
        return max(0, remaining.days)

    @property
    def is_expired(self):
        from datetime import date

        return self.expiry_date < date.today()

    def is_trial_active(self):
        if not self.is_on_trial:
            return False
        if not self.trial_end:
            return False
        if self.is_trial_expired:
            return False
        return self.trial_end >= timezone.now()

    def check_trial_expired(self):
        """Check and update trial expiration status"""
        if self.is_on_trial and self.trial_end:
            if timezone.now() > self.trial_end:
                self.is_trial_expired = True
                self.is_active = False
                self.save()
                return True
        return False

    def can_access_billing(self):
        if self.is_trial_active():
            return True  # Trial users can access billing
        return self.plan in ["pro", "enterprise"] and self.is_active

    def can_access_reports(self):
        if self.is_trial_active():
            return True  # Trial users can access reports
        return self.plan in ["pro", "enterprise"] and self.is_active

    def can_access_analytics(self):
        if self.is_trial_active():
            return True  # Trial users can access analytics
        return self.plan == "enterprise" and self.is_active

    @property
    def patient_limit(self):
        if self.is_trial_active():
            return 50  # Limit during trial
        limits = {
            "basic": 500,
            "pro": 10000,
            "enterprise": 999999999,
        }
        return limits.get(self.plan, 500)

    def can_add_patient(self):
        from patients.models import Patient

        self.check_trial_expired()
        current_count = Patient.objects.filter(clinic=self.clinic).count()
        return current_count < self.patient_limit
