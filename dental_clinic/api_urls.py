from django.urls import path, include
from rest_framework.routers import DefaultRouter
from patients.viewsets import PatientViewSet, PatientDocumentViewSet
from appointments.viewsets import AppointmentViewSet
from billing.viewsets import InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r"patients", PatientViewSet)
router.register(r"patient-documents", PatientDocumentViewSet)
router.register(r"appointments", AppointmentViewSet)
router.register(r"invoices", InvoiceViewSet)
router.register(r"payments", PaymentViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
]
