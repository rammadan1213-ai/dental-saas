def subscription_context(request):
    from django.conf import settings

    context = {}
    if request.user.is_authenticated:
        clinic = getattr(request.user, "clinic", None)
        if clinic and hasattr(clinic, "subscription"):
            context = {
                "user_subscription": clinic.subscription,
                "user_plan": clinic.subscription.plan,
                "plan_features": {
                    "can_billing": clinic.subscription.can_access_billing,
                    "can_reports": clinic.subscription.can_access_reports,
                    "can_analytics": clinic.subscription.can_access_analytics,
                    "patient_limit": clinic.subscription.patient_limit,
                },
            }
    context["STRIPE_PUBLIC_KEY"] = getattr(settings, "STRIPE_PUBLIC_KEY", "")
    return context
