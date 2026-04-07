from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from .models import Notification, create_notification


def clear_notification_cache(user):
    cache_key = f"notifications_count_{user.id}"
    cache.delete(cache_key)


@login_required
@require_http_methods(["GET"])
def notification_list(request):
    """Get all notifications for the current user"""
    notifications = Notification.objects.filter(user=request.user)[:50]

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(
        request,
        "notifications/notification_list.html",
        {"notifications": notifications, "unread_count": unread_count},
    )


@login_required
@require_http_methods(["POST"])
def mark_as_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        clear_notification_cache(request.user)
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Not found"})


@login_required
@require_http_methods(["POST"])
def mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    clear_notification_cache(request.user)
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    """Get count of unread notifications"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"count": count})


@login_required
@require_http_methods(["DELETE"])
def delete_notification(request, notification_id):
    """Delete a notification"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        clear_notification_cache(request.user)
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Not found"})


def notify_appointment_created(user, appointment):
    """Notify about new appointment"""
    notification = create_notification(
        user=user,
        title="New Appointment",
        message=f"Appointment scheduled for {appointment.patient.full_name} on {appointment.date}",
        notification_type="appointment",
        link=f"/appointments/{appointment.id}/",
    )
    clear_notification_cache(user)
    return notification


def notify_appointment_reminder(user, appointment):
    """Notify about upcoming appointment"""
    notification = create_notification(
        user=user,
        title="Appointment Reminder",
        message=f"Reminder: {appointment.patient.full_name} tomorrow at {appointment.start_time}",
        notification_type="appointment",
        link=f"/appointments/{appointment.id}/",
    )
    clear_notification_cache(user)
    return notification


def notify_payment_received(user, payment):
    """Notify about payment received"""
    notification = create_notification(
        user=user,
        title="Payment Received",
        message=f"Payment of ${payment.amount} received for Invoice {payment.invoice.invoice_number}",
        notification_type="payment",
        link=f"/billing/invoices/{payment.invoice.id}/",
    )
    clear_notification_cache(user)
    return notification


def notify_subscription_expiry(user, days_remaining):
    """Notify about subscription expiry"""
    notification = create_notification(
        user=user,
        title="Subscription Expiring",
        message=f"Your subscription expires in {days_remaining} days. Please renew.",
        notification_type="subscription",
        link="/subscription/manage/",
    )
    clear_notification_cache(user)
    return notification


def notify_new_patient(user, patient):
    """Notify about new patient"""
    notification = create_notification(
        user=user,
        title="New Patient",
        message=f"New patient registered: {patient.full_name}",
        notification_type="info",
        link=f"/patients/{patient.id}/",
    )
    clear_notification_cache(user)
    return notification
