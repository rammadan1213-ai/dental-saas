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
    import logging

    logger = logging.getLogger(__name__)

    def get_db_engine():
        if hasattr(settings, "DATABASE_URL"):
            return "postgres"
        return "sqlite"

    @api_view(["GET"])
    def global_search(request):
        query = request.GET.get("q", "")

        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized"}, status=401)

        if len(query) < 2:
            return Response({})

        clinic = getattr(request.user, "clinic", None)
        clinic_id = clinic.id if clinic else None

        db_type = get_db_engine()

        results = {
            "patients": [],
            "treatments": [],
            "invoices": [],
            "appointments": [],
            "clinics": [],
        }

        # Patients - with smart ranking
        if clinic:
            patients_qs = Patient.objects.filter(clinic=clinic)
        else:
            patients_qs = Patient.objects.all()

        if db_type == "postgres":
            try:
                from django.contrib.postgres.search import (
                    SearchVector,
                    SearchQuery,
                    SearchRank,
                    TrigramSimilarity,
                )

                search_vector = SearchVector(
                    "first_name", "last_name", "phone", "email", "full_name"
                )
                search_query = SearchQuery(query)

                patients = (
                    patients_qs.annotate(
                        rank=SearchRank(search_vector, search_query),
                        similarity=TrigramSimilarity("first_name", query),
                    )
                    .filter(Q(rank__gte=0.01) | Q(similarity__gt=0.3))
                    .order_by("-rank", "-similarity")
                    .select_related("clinic")
                    .only("id", "first_name", "last_name", "phone", "full_name")[:10]
                )
            except Exception as e:
                logger.warning(f"PostgreSQL search failed: {e}")
                patients = (
                    patients_qs.filter(
                        Q(first_name__icontains=query)
                        | Q(last_name__icontains=query)
                        | Q(phone__icontains=query)
                        | Q(email__icontains=query)
                        | Q(full_name__icontains=query)
                    )
                    .select_related("clinic")
                    .only("id", "first_name", "last_name", "phone", "full_name")[:10]
                )
        else:
            patients = (
                patients_qs.filter(
                    Q(first_name__icontains=query)
                    | Q(last_name__icontains=query)
                    | Q(phone__icontains=query)
                    | Q(email__icontains=query)
                    | Q(full_name__icontains=query)
                )
                .select_related("clinic")
                .only("id", "first_name", "last_name", "phone", "full_name")[:10]
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
            treatments_qs = Treatment.objects.filter(clinic=clinic)
        else:
            treatments_qs = Treatment.objects.all()

        if db_type == "postgres":
            try:
                from django.contrib.postgres.search import (
                    SearchVector,
                    SearchQuery,
                    SearchRank,
                )

                search_vector = SearchVector("procedure", "diagnosis")
                search_query = SearchQuery(query)

                treatments = (
                    treatments_qs.annotate(rank=SearchRank(search_vector, search_query))
                    .filter(rank__gte=0.01)
                    .order_by("-rank")
                    .select_related("patient", "clinic")
                    .only(
                        "id",
                        "procedure",
                        "diagnosis",
                        "patient__first_name",
                        "patient__last_name",
                    )[:8]
                )
            except Exception:
                treatments = (
                    treatments_qs.filter(
                        Q(procedure__icontains=query) | Q(diagnosis__icontains=query)
                    )
                    .select_related("patient", "clinic")
                    .only(
                        "id",
                        "procedure",
                        "diagnosis",
                        "patient__first_name",
                        "patient__last_name",
                    )[:8]
                )
        else:
            treatments = (
                treatments_qs.filter(
                    Q(procedure__icontains=query) | Q(diagnosis__icontains=query)
                )
                .select_related("patient", "clinic")
                .only(
                    "id",
                    "procedure",
                    "diagnosis",
                    "patient__first_name",
                    "patient__last_name",
                )[:8]
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
            invoices_qs = Invoice.objects.filter(clinic=clinic)
        else:
            invoices_qs = Invoice.objects.all()

        if db_type == "postgres":
            try:
                from django.contrib.postgres.search import (
                    SearchVector,
                    SearchQuery,
                    SearchRank,
                )

                search_vector = SearchVector("invoice_number")
                search_query = SearchQuery(query)

                invoices = (
                    invoices_qs.annotate(rank=SearchRank(search_vector, search_query))
                    .filter(
                        Q(rank__gte=0.01)
                        | Q(patient__first_name__icontains=query)
                        | Q(patient__last_name__icontains=query)
                    )
                    .order_by("-rank")
                    .select_related("patient", "clinic")
                    .only(
                        "id",
                        "invoice_number",
                        "status",
                        "total_amount",
                        "patient__first_name",
                        "patient__last_name",
                    )[:8]
                )
            except Exception:
                invoices = (
                    invoices_qs.filter(
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
                    )[:8]
                )
        else:
            invoices = (
                invoices_qs.filter(
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
                )[:8]
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
            appointments_qs = Appointment.objects.filter(clinic=clinic)
        else:
            appointments_qs = Appointment.objects.all()

        appointments = (
            appointments_qs.filter(
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
            )[:8]
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
