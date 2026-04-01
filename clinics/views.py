import stripe
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.conf import settings
from .models import Clinic, Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY


class PricingView(TemplateView):
    template_name = "clinics/pricing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stripe_key"] = getattr(settings, "STRIPE_PUBLIC_KEY", "")
        context["stripe_prices"] = settings.STRIPE_PRICES
        return context


class SubscriptionExpiredView(LoginRequiredMixin, TemplateView):
    template_name = "clinics/subscription_expired.html"


class SubscriptionManageView(LoginRequiredMixin, View):
    template_name = "clinics/subscription_manage.html"

    def get(self, request):
        clinic = getattr(request.user, "clinic", None)
        if not clinic:
            messages.error(request, "No clinic associated with your account.")
            return redirect("dashboard:home")

        subscription = getattr(clinic, "subscription", None)

        success = request.GET.get("success")
        if success == "true":
            messages.success(
                request, "Payment successful! Your subscription is now active."
            )

        canceled = request.GET.get("canceled")
        if canceled == "true":
            messages.warning(request, "Payment was canceled.")

        context = {
            "clinic": clinic,
            "subscription": subscription,
            "stripe_key": getattr(settings, "STRIPE_PUBLIC_KEY", ""),
            "stripe_prices": settings.STRIPE_PRICES,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        clinic = getattr(request.user, "clinic", None)
        if not clinic:
            return redirect("clinics:subscription_manage")

        subscription = getattr(clinic, "subscription", None)
        action = request.POST.get("action")

        if action == "create_checkout":
            plan = request.POST.get("plan", "pro")
            try:
                price_data = settings.STRIPE_PRICES.get(
                    plan, settings.STRIPE_PRICES["pro"]
                )

                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[
                        {
                            "price_data": {
                                "currency": "usd",
                                "product_data": {
                                    "name": price_data["name"],
                                    "description": f"Subscription for {clinic.name}",
                                },
                                "unit_amount": price_data["amount"],
                                "recurring": {"interval": price_data["interval"]},
                            },
                            "quantity": 1,
                        }
                    ],
                    mode="subscription",
                    success_url=f"{request.build_absolute_uri('/subscription/manage/')}?success=true",
                    cancel_url=f"{request.build_absolute_uri('/subscription/manage/')}?canceled=true",
                    metadata={
                        "clinic_id": str(clinic.id),
                        "plan": plan,
                        "user_id": str(request.user.id),
                    },
                    customer_email=request.user.email,
                )
                return redirect(checkout_session.url)

            except stripe.error.StripeError as e:
                messages.error(request, f"Stripe error: {str(e)}")
                return redirect("clinics:subscription_manage")

        elif action == "cancel" and subscription:
            subscription.is_active = False
            subscription.save()
            messages.warning(request, "Subscription cancelled.")
            return redirect("clinics:subscription_manage")

        return redirect("clinics:subscription_manage")


class CheckoutView(LoginRequiredMixin, View):
    def post(self, request):
        plan = request.POST.get("plan", "pro")
        clinic = getattr(request.user, "clinic", None)

        if not clinic:
            messages.error(request, "No clinic associated with your account.")
            return redirect("dashboard:home")

        subscription, created = Subscription.objects.get_or_create(
            clinic=clinic, defaults={"plan": plan, "expiry_date": None}
        )

        if not created and subscription.plan != plan:
            subscription.plan = plan
            subscription.save()

        return redirect("clinics:subscription_manage")


def api_create_checkout(request):
    if request.method == "POST":
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
                                "description": f"Subscription for {clinic.name}",
                            },
                            "unit_amount": price_data["amount"],
                            "recurring": {"interval": price_data["interval"]},
                        },
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=f"{request.build_absolute_uri('/subscription/manage/')}?success=true",
                cancel_url=f"{request.build_absolute_uri('/subscription/manage/')}?canceled=true",
                metadata={
                    "clinic_id": str(clinic.id),
                    "plan": plan,
                },
                customer_email=request.user.email,
            )

            return JsonResponse({"url": checkout_session.url})

        except stripe.error.StripeError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
