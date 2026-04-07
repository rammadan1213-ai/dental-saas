from accounts.models import AuditLog


def log_audit(
    user, action, description, model_name="", object_id=None, clinic=None, request=None
):
    """Helper function to create audit logs"""
    ip_address = None
    user_agent = ""

    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

    return AuditLog.objects.create(
        user=user,
        action=action,
        description=description,
        model_name=model_name,
        object_id=object_id,
        clinic=clinic or getattr(user, "clinic", None),
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_client_ip(request):
    """Get client IP from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def log_login(request, user):
    """Log user login"""
    return log_audit(
        user=user,
        action="login",
        description=f"User logged in",
        model_name="auth.User",
        request=request,
    )


def log_logout(request, user):
    """Log user logout"""
    return log_audit(
        user=user,
        action="logout",
        description=f"User logged out",
        model_name="auth.User",
        request=request,
    )


def log_payment(user, action, description, clinic=None, object_id=None):
    """Log payment actions"""
    return log_audit(
        user=user,
        action=action,
        description=description,
        model_name="billing.Payment",
        object_id=object_id,
        clinic=clinic,
    )


def log_subscription(user, action, description, clinic=None):
    """Log subscription actions"""
    return log_audit(
        user=user,
        action=action,
        description=description,
        model_name="clinics.Subscription",
        clinic=clinic,
    )


def log_model_change(user, action, model_name, object_id, description, clinic=None):
    """Log model create/update/delete"""
    return log_audit(
        user=user,
        action=action,
        description=description,
        model_name=model_name,
        object_id=object_id,
        clinic=clinic,
    )
