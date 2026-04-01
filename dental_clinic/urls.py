from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
    path("", include("dashboard.urls")),
]

urlpatterns += api_urls

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
