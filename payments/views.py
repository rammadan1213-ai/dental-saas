import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from datetime import datetime, timedelta
import json
import logging

from clinics.models import Clinic, Subscription
from .models import PaymentRecord

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


@login_required
@require_http_methods(["POST"])
def create_checkout_session(request):
    try:
        data = json.loads(request.body)
        plan = data.get("plan", "pro")

        clinic = getattr(request.user, "clinic", None)
        if not clinic:
            return JsonResponse({"error": "No clinic associated"}, status=400)

        price_data = settings.STRIPE_PRICES.get(plan, settings.STRIPE_PRICES["pro"])

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": price_data["name"],
                            "description": f"Monthly subscription for {clinic.name}",
                        },
                        "unit_amount": price_data["amount"],
                        "recurring": {"interval": price_data["interval"]},
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{settings.ALLOWED_HOSTS[0]}/subscription/manage/?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.ALLOWED_HOSTS[0]}/subscription/manage/?canceled=true",
            metadata={
                "clinic_id": str(clinic.id),
                "plan": plan,
                "user_id": str(request.user.id),
            },
            customer_email=request.user.email,
        )

        PaymentRecord.objects.create(
            subscription=clinic.subscription,
            stripe_session_id=checkout_session.id,
            amount=price_data["amount"] / 100,
            currency="usd",
            status="pending",
            plan=plan,
        )

        return JsonResponse(
            {"session_id": checkout_session.id, "url": checkout_session.url}
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return JsonResponse({"error": "Failed to create checkout session"}, status=500)


@login_required
@require_http_methods(["POST"])
def create_one_time_payment(request):
    try:
        data = json.loads(request.body)
        plan = data.get("plan", "pro")
        billing_period = data.get("billing_period", "month")

        clinic = getattr(request.user, "clinic", None)
        if not clinic:
            return JsonResponse({"error": "No clinic associated"}, status=400)

        price_data = settings.STRIPE_PRICES.get(plan, settings.STRIPE_PRICES["pro"])

        if billing_period == "year":
            amount = price_data["amount"] * 10
        else:
            amount = price_data["amount"]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{price_data['name']} - {billing_period.title()}",
                            "description": f"One-time payment for {clinic.name}",
                        },
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.ALLOWED_HOSTS[0]}/subscription/manage/?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.ALLOWED_HOSTS[0]}/subscription/manage/?canceled=true",
            metadata={
                "clinic_id": str(clinic.id),
                "plan": plan,
                "billing_period": billing_period,
                "user_id": str(request.user.id),
                "payment_type": "one_time",
            },
            customer_email=request.user.email,
        )

        PaymentRecord.objects.create(
            subscription=clinic.subscription,
            stripe_session_id=checkout_session.id,
            amount=amount / 100,
            currency="usd",
            status="pending",
            plan=plan,
        )

        return JsonResponse(
            {"session_id": checkout_session.id, "url": checkout_session.url}
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}")
        return JsonResponse({"error": "Failed to create payment"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return HttpResponse(status=400)

    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            handle_successful_payment(session)

        elif event["type"] == "invoice.paid":
            invoice = event["data"]["object"]
            handle_renewal_payment(invoice)

        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            handle_subscription_cancelled(subscription)

        elif event["type"] == "invoice.payment_failed":
            invoice = event["data"]["object"]
            handle_payment_failed(invoice)

        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return HttpResponse(status=500)


def handle_successful_payment(session):
    metadata = session.get("metadata", {})
    clinic_id = metadata.get("clinic_id")
    plan = metadata.get("plan", "pro")
    payment_type = metadata.get("payment_type", "subscription")

    if not clinic_id:
        logger.error("No clinic_id in payment metadata")
        return

    try:
        clinic = Clinic.objects.get(id=clinic_id)
        subscription = clinic.subscription

        if payment_type == "one_time":
            billing_period = metadata.get("billing_period", "month")
            if billing_period == "year":
                expiry_days = 365
            else:
                expiry_days = 30
        else:
            expiry_days = 30

        if subscription:
            subscription.plan = plan
            subscription.is_active = True
            subscription.expiry_date = datetime.now().date() + timedelta(
                days=expiry_days
            )
            subscription.save()

        PaymentRecord.objects.filter(stripe_session_id=session["id"]).update(
            status="completed",
            stripe_payment_intent_id=session.get("payment_intent", ""),
        )

        logger.info(f"Payment completed for clinic {clinic.name}, plan: {plan}")

    except Clinic.DoesNotExist:
        logger.error(f"Clinic {clinic_id} not found")
    except Exception as e:
        logger.error(f"Error handling successful payment: {str(e)}")


def handle_renewal_payment(invoice):
    try:
        subscription_id = invoice.get("subscription")
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            customer_id = subscription.get("customer")

            if customer_id:
                clinic = Clinic.objects.filter(
                    subscription__stripe_customer_id=customer_id
                ).first()
                if clinic and clinic.subscription:
                    clinic.subscription.expiry_date = datetime.now().date() + timedelta(
                        days=30
                    )
                    clinic.subscription.save()
                    logger.info(f"Subscription renewed for clinic {clinic.name}")

    except Exception as e:
        logger.error(f"Error handling renewal: {str(e)}")


def handle_subscription_cancelled(stripe_subscription):
    try:
        customer_id = stripe_subscription.get("customer")
        if customer_id:
            clinic = Clinic.objects.filter(
                subscription__stripe_customer_id=customer_id
            ).first()
            if clinic and clinic.subscription:
                clinic.subscription.is_active = False
                clinic.subscription.save()
                logger.info(f"Subscription cancelled for clinic {clinic.name}")

    except Exception as e:
        logger.error(f"Error handling cancellation: {str(e)}")


def handle_payment_failed(invoice):
    try:
        subscription_id = invoice.get("subscription")
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            customer_id = subscription.get("customer")

            if customer_id:
                clinic = Clinic.objects.filter(
                    subscription__stripe_customer_id=customer_id
                ).first()
                if clinic and clinic.subscription:
                    logger.warning(f"Payment failed for clinic {clinic.name}")

    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")


@login_required
def get_payment_history(request):
    clinic = getattr(request.user, "clinic", None)
    if not clinic or not hasattr(clinic, "subscription"):
        return JsonResponse({"error": "No subscription found"}, status=400)

    payments = PaymentRecord.objects.filter(subscription=clinic.subscription)[:20]
    data = [
        {
            "id": p.id,
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "plan": p.plan,
            "created_at": p.created_at.isoformat(),
        }
        for p in payments
    ]
    return JsonResponse({"payments": data})


@login_required
def cancel_subscription(request):
    if request.method == "POST":
        clinic = getattr(request.user, "clinic", None)
        if not clinic or not hasattr(clinic, "subscription"):
            return JsonResponse({"error": "No subscription found"}, status=400)

        subscription = clinic.subscription
        stripe_customer_id = subscription.stripe_customer_id

        if stripe_customer_id:
            try:
                customers = stripe.Customer.list(email=request.user.email).data
                if customers:
                    customer = customers[0]
                    subscriptions = stripe.Subscription.list(customer=customer.id).data
                    for sub in subscriptions:
                        stripe.Subscription.delete(sub.id)
            except Exception as e:
                logger.error(f"Error cancelling Stripe subscription: {str(e)}")

        subscription.is_active = False
        subscription.save()

        return JsonResponse({"success": True, "message": "Subscription cancelled"})

    return JsonResponse({"error": "Invalid request"}, status=400)
