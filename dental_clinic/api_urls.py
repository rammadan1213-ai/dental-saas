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
    from django.db.models import Q
    from patients.models import Patient
    from billing.models import Invoice
    from clinics.models import Clinic
    from treatments.models import Treatment
    from appointments.models import Appointment

    @api_view(["GET"])
    def global_search(request):
        query = request.GET.get("q", "")

        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized"}, status=401)

        if len(query) < 2:
            return Response({})

        clinic = getattr(request.user, "clinic", None)

        results = {
            "patients": [],
            "treatments": [],
            "invoices": [],
            "appointments": [],
            "clinics": [],
        }

        # Patients
        if clinic:
            patients = Patient.objects.filter(clinic=clinic)
        else:
            patients = Patient.objects.all()

        patients = (
            patients.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(phone__icontains=query)
                | Q(email__icontains=query)
                | Q(full_name__icontains=query)
            )
            .select_related("clinic")
            .only("id", "first_name", "last_name", "phone", "full_name")[:5]
        )

        results["patients"] = [
            {
                "id": p.id,
                "full_name": p.full_name,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "phone": p.phone,
            }
            for p in patients
        ]

        # Treatments
        if clinic:
            treatments = Treatment.objects.filter(clinic=clinic)
        else:
            treatments = Treatment.objects.all()

        treatments = (
            treatments.filter(
                Q(procedure__icontains=query) | Q(diagnosis__icontains=query)
            )
            .select_related("patient", "clinic")
            .only(
                "id",
                "procedure",
                "diagnosis",
                "patient__first_name",
                "patient__last_name",
            )[:5]
        )

        results["treatments"] = [
            {
                "id": t.id,
                "procedure": t.procedure[:50],
                "patient_name": t.patient.full_name if t.patient else None,
            }
            for t in treatments
        ]

        # Invoices
        if clinic:
            invoices = Invoice.objects.filter(clinic=clinic)
        else:
            invoices = Invoice.objects.all()

        invoices = (
            invoices.filter(
                Q(invoice_number__icontains=query)
                | Q(patient__first_name__icontains=query)
                | Q(patient__last_name__icontains=query)
            )
            .select_related("patient", "clinic")
            .only(
                "id",
                "invoice_number",
                "status",
                "total_amount",
                "patient__first_name",
                "patient__last_name",
            )[:5]
        )

        results["invoices"] = [
            {
                "id": i.id,
                "invoice_number": i.invoice_number,
                "status": i.status,
                "amount": str(i.total_amount),
                "patient_name": i.patient.full_name if i.patient else None,
            }
            for i in invoices
        ]

        # Appointments
        if clinic:
            appointments = Appointment.objects.filter(clinic=clinic)
        else:
            appointments = Appointment.objects.all()

        appointments = (
            appointments.filter(
                Q(patient__first_name__icontains=query)
                | Q(patient__last_name__icontains=query)
                | Q(reason__icontains=query)
            )
            .select_related("patient", "clinic")
            .only(
                "id",
                "status",
                "date",
                "reason",
                "patient__first_name",
                "patient__last_name",
            )[:5]
        )

        results["appointments"] = [
            {
                "id": a.id,
                "status": a.status,
                "date": str(a.date),
                "reason": a.reason[:30],
                "patient_name": a.patient.full_name if a.patient else None,
            }
            for a in appointments
        ]

        # Clinics (superuser only)
        if request.user.is_superuser:
            clinics = Clinic.objects.filter(
                Q(name__icontains=query) | Q(email__icontains=query)
            ).only("id", "name", "email")[:5]

            results["clinics"] = [
                {"id": c.id, "name": c.name, "email": c.email} for c in clinics
            ]

        return Response(results)

    urlpatterns.append(path("api/search/", global_search, name="global_search"))
