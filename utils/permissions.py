def get_clinic(user):
    """Get the clinic associated with a user"""
    return getattr(user, "clinic", None)


def get_subscription(user):
    """Get the subscription for a user's clinic"""
    clinic = get_clinic(user)
    if clinic:
        return getattr(clinic, "subscription", None)
    return None


def has_feature(user, feature):
    """
    Check if user has access to a specific feature based on their plan.

    Features:
        - patients: Patient management
        - billing: Billing & invoicing
        - reports: Basic reports
        - analytics: Advanced analytics
        - multi_user: Multiple user accounts
    """
    if not user.is_authenticated:
        return False

    clinic = get_clinic(user)
    if not clinic:
        return False

    subscription = get_subscription(user)
    if not subscription:
        return False

    plan = subscription.plan

    feature_rules = {
        "basic": ["patients"],
        "pro": ["patients", "billing", "reports"],
        "enterprise": ["patients", "billing", "reports", "analytics", "multi_user"],
    }

    return feature in feature_rules.get(plan, [])


def check_patient_limit(user):
    """
    Check if user can add more patients.
    Returns tuple: (can_add: bool, message: str, limit: int, current: int)
    """
    clinic = get_clinic(user)
    if not clinic:
        return False, "No clinic associated", 0, 0

    subscription = get_subscription(user)
    if not subscription:
        return False, "No subscription", 0, 0

    from patients.models import Patient

    current_count = Patient.objects.filter(clinic=clinic).count()
    limit = subscription.patient_limit

    if current_count >= limit:
        return (
            False,
            f"Patient limit reached ({limit}). Please upgrade your plan.",
            limit,
            current_count,
        )

    return True, "", limit, current_count


def get_plan_features(plan):
    """Get all features for a specific plan"""
    features = {
        "basic": {
            "name": "Basic",
            "price": 10,
            "features": ["patients", "appointments", "treatments"],
            "patient_limit": 500,
            "billing": False,
            "reports": False,
            "analytics": False,
            "multi_user": False,
        },
        "pro": {
            "name": "Pro",
            "price": 25,
            "features": [
                "patients",
                "appointments",
                "treatments",
                "billing",
                "reports",
            ],
            "patient_limit": 10000,
            "billing": True,
            "reports": True,
            "analytics": False,
            "multi_user": False,
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 50,
            "features": [
                "patients",
                "appointments",
                "treatments",
                "billing",
                "reports",
                "analytics",
            ],
            "patient_limit": 999999999,
            "billing": True,
            "reports": True,
            "analytics": True,
            "multi_user": True,
        },
    }
    return features.get(plan, features["basic"])


def check_plan(user):
    """Check if user's subscription is active"""
    if not user.is_authenticated:
        return False

    from billing.models import Subscription

    try:
        sub = Subscription.objects.get(user=user)
        return sub.active
    except Subscription.DoesNotExist:
        return False
