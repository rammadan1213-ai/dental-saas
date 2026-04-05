from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import PaymentRequest
from clinics.models import Subscription
from datetime import timedelta
from django.utils import timezone


PLAN_PRICES = {
    "basic": 10,
    "pro": 25,
    "enterprise": 50,
}


@login_required
def submit_payment_request(request):
    if request.method == "POST":
        plan = request.POST.get("plan")
        merchant_number = request.POST.get("merchant_number")
        transaction_id = request.POST.get("transaction_id", "")
        notes = request.POST.get("notes", "")

        clinic = getattr(request.user, "clinic", None)
        if not clinic:
            messages.error(request, "No clinic associated with your account")
            return redirect("dashboard:home")

        amount = PLAN_PRICES.get(plan, 10)

        payment_request = PaymentRequest.objects.create(
            clinic=clinic,
            plan=plan,
            amount=amount,
            merchant_number=merchant_number,
            transaction_id=transaction_id,
            notes=notes,
        )

        # Notify superadmins
        from notifications.models import create_notification
        from django.contrib.auth import get_user_model

        User = get_user_model()
        superadmins = User.objects.filter(is_superuser=True)

        for admin in superadmins:
            create_notification(
                user=admin,
                title=f"New Payment Request from {clinic.name}",
                message=f"Plan: {plan}, Amount: ${amount}, Merchant: {merchant_number}",
                notification_type="payment",
                link=f"/admin/payment-request/{payment_request.id}/",
            )

        messages.success(
            request,
            "Payment request submitted! We will verify and activate your plan within 24 hours.",
        )
        return redirect("dashboard:home")

    # Show pricing page
    return render(request, "billing/payment_request.html", {"plan_prices": PLAN_PRICES})


@login_required
def my_payment_requests(request):
    clinic = getattr(request.user, "clinic", None)
    if not clinic:
        return redirect("dashboard:home")

    requests = PaymentRequest.objects.filter(clinic=clinic)
    return render(request, "billing/my_payment_requests.html", {"requests": requests})


# Admin views for reviewing payments
@login_required
def admin_payment_requests(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Access denied"}, status=403)

    pending_requests = PaymentRequest.objects.filter(status="pending").select_related(
        "clinic"
    )
    return render(
        request, "billing/admin_payment_requests.html", {"requests": pending_requests}
    )


@login_required
def approve_payment_request(request, request_id):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Access denied"}, status=403)

    payment_request = get_object_or_404(PaymentRequest, id=request_id)

    # Update payment request
    payment_request.status = "approved"
    payment_request.reviewed_by = request.user
    payment_request.save()

    # Update clinic subscription
    subscription = getattr(payment_request.clinic, "subscription", None)
    if subscription:
        subscription.plan = payment_request.plan
        subscription.is_active = True
        subscription.expiry_date = timezone.now().date() + timedelta(days=30)
        subscription.save()

    # Notify clinic
    from notifications.models import create_notification

    owner = payment_request.clinic.owner
    if owner:
        create_notification(
            user=owner,
            title="Payment Approved!",
            message=f"Your {payment_request.get_plan_display()} plan has been activated!",
            notification_type="success",
        )

    messages.success(request, f"Payment approved for {payment_request.clinic.name}")
    return redirect("billing:admin_payment_requests")


@login_required
def reject_payment_request(request, request_id):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Access denied"}, status=403)

    payment_request = get_object_or_404(PaymentRequest, id=request_id)
    payment_request.status = "rejected"
    payment_request.reviewed_by = request.user
    payment_request.save()

    messages.success(request, f"Payment rejected for {payment_request.clinic.name}")
    return redirect("billing:admin_payment_requests")
