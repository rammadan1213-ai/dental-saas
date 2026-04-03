from django.urls import path, include
from rest_framework.routers import DefaultRouter
from patients.viewsets import PatientViewSet, PatientDocumentViewSet
from appointments.viewsets import AppointmentViewSet
from billing.viewsets import InvoiceViewSet, PaymentViewSet
from django.conf import settings

router = DefaultRouter()
router.register(r"patients", PatientViewSet)
router.register(r"patient-documents", PatientDocumentViewSet)
router.register(r"appointments", AppointmentViewSet)
router.register(r"invoices", InvoiceViewSet)
router.register(r"payments", PaymentViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
]

if hasattr(settings, "SEARCH_ENABLED") and settings.SEARCH_ENABLED:
    from rest_framework.decorators import api_view
    from rest_framework.response import Response
    from patients.models import Patient
    from billing.models import Invoice
    from clinics.models import Clinic

    @api_view(["GET"])
    def global_search(request):
        query = request.GET.get("q", "")
        if len(query) < 2:
            return Response({})

        patients = list(
            Patient.objects.filter(full_name__icontains=query)[:5].values(
                "id", "full_name"
            )
        )

        clinics = list(
            Clinic.objects.filter(name__icontains=query)[:5].values("id", "name")
        )

        invoices = list(
            Invoice.objects.filter(invoice_number__icontains=query)[:5].values(
                "id", "invoice_number"
            )
        )

        return Response(
            {
                "patients": patients,
                "clinics": clinics,
                "invoices": invoices,
            }
        )

    urlpatterns.append(path("api/search/", global_search, name="global_search"))
