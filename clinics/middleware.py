from django.shortcuts import redirect
from django.contrib import messages


class SubscriptionMiddleware:
    EXEMPT_URLS = [
        "/",
        "/accounts/login/",
        "/accounts/logout/",
        "/accounts/register/",
        "/subscription/",
        "/admin/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        for exempt in self.EXEMPT_URLS:
            if path.startswith(exempt):
                return self.get_response(request)

        if request.user.is_authenticated:
            clinic = getattr(request.user, "clinic", None)

            if clinic and hasattr(clinic, "subscription"):
                subscription = clinic.subscription

                if not subscription.is_active or subscription.is_expired:
                    messages.warning(
                        request,
                        "Your subscription has expired. Please renew to continue using the system.",
                    )
                    return redirect("clinics:subscription_expired")

                if not subscription.can_access_billing() and path.startswith(
                    "/billing/"
                ):
                    messages.warning(
                        request, "Billing features require a Pro or Enterprise plan."
                    )
                    return redirect("clinics:pricing")

                if not subscription.can_access_reports() and path.startswith(
                    "/reports/"
                ):
                    messages.warning(
                        request, "Reports require a Pro or Enterprise plan."
                    )
                    return redirect("clinics:pricing")

        return self.get_response(request)
