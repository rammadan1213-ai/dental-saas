from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        DENTIST = "dentist", _("Dentist")
        RECEPTIONIST = "receptionist", _("Receptionist")

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.RECEPTIONIST
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN

    @property
    def is_dentist(self):
        return self.role == self.Role.DENTIST

    @property
    def is_receptionist(self):
        return self.role == self.Role.RECEPTIONIST

    @property
    def is_superadmin(self):
        return self.is_superuser

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        null=True,
        related_name="audit_logs",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        null=True,
        related_name="audit_logs",
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"


class PasswordReset(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_resets"
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Password reset for {self.user.email}"

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at
