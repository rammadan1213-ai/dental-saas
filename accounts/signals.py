from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from notifications.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(user_logged_in)
def notify_superadmin_on_login(sender, request, user, **kwargs):
    """Notify superadmins when a user logs in"""
    from django.contrib.auth import get_user_model

    # Get all superadmins
    superadmins = User.objects.filter(is_superuser=True)

    # Create notification message
    clinic_name = (
        user.clinic.name if hasattr(user, "clinic") and user.clinic else "No Clinic"
    )
    message = f"{user.get_full_name or user.username} logged into {clinic_name}"

    for admin in superadmins:
        Notification.objects.create(
            user=admin,
            title=f"User Login: {user.username}",
            message=message,
            notification_type="info",
            link=f"/accounts/users/{user.id}/",
        )
    message = f"{user.get_full_name or user.username} logged into {clinic_name}"

    for admin in superadmins:
        Notification.objects.create(
            user=admin,
            title=f"User Login: {user.username}",
            message=message,
            notification_type="info",
            link=f"/accounts/admin/clinic/{user.clinic.id}/"
            if user.clinic
            else "/accounts/admin/dashboard/",
        )
    message = f"{user.get_full_name or user.username} logged into {clinic_name}"

    for admin in superadmins:
        Notification.objects.create(
            user=admin,
            title=f"User Login: {user.username}",
            message=message,
            notification_type="info",
            link=f"/accounts/user/{user.id}/",
        )
