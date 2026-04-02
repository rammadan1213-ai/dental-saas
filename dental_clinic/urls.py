from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import JsonResponse
from .api_urls import urlpatterns as api_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("patients/", include("patients.urls")),
    path("appointments/", include("appointments.urls")),
    path("treatments/", include("treatments.urls")),
    path("billing/", include("billing.urls")),
    path("subscription/", include("clinics.urls")),
    path("api/payments/", include("payments.urls")),
    path("setup/", include("setup.urls")),
    path("notifications/", include("notifications.urls")),
    path(
        "pricing/",
        lambda request: render(
            request, "pricing.html", {"stripe_key": settings.STRIPE_PUBLIC_KEY}
        ),
        name="pricing",
    ),
    path(
        "payment-success/",
        lambda request: render(request, "payment_success.html"),
        name="payment_success",
    ),
    path(
        "payment-cancel/",
        lambda request: render(request, "payment_cancel.html"),
        name="payment_cancel",
    ),
    path("", include("dashboard.urls")),
]

urlpatterns += api_urls

urlpatterns += api_urls

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
