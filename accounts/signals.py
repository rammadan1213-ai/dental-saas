from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from notifications.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(user_logged_in)
def notify_superadmin_on_login(sender, request, user, **kwargs):
    """Notify superadmins when a user logs in"""
    if not user.is_authenticated:
        return
    clinic_name = (
        user.clinic.name if hasattr(user, "clinic") and user.clinic else "No Clinic"
    )
    message = f"{user.get_full_name() or user.username} logged into {clinic_name}"

    # Get all superadmins
    superadmins = User.objects.filter(is_superuser=True)

    for admin in superadmins:
        Notification.objects.create(
            user=admin,
            title=f"User Login: {user.username}",
            message=message,
            notification_type="info",
            link=f"/accounts/users/{user.id}/",
        )


@receiver(user_logged_out)
def notify_superadmin_on_logout(sender, request, user, **kwargs):
    """Notify superadmins when a user logs out"""
    if not user.is_authenticated:
        return
    clinic_name = (
        user.clinic.name if hasattr(user, "clinic") and user.clinic else "No Clinic"
    )
    message = f"{user.get_full_name() or user.username} logged out from {clinic_name}"

    # Get all superadmins
    superadmins = User.objects.filter(is_superuser=True)

    for admin in superadmins:
        Notification.objects.create(
            user=admin,
            title=f"User Logout: {user.username}",
            message=message,
            notification_type="info",
            link=f"/accounts/users/{user.id}/",
        )
