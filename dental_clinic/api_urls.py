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
    from django.conf import settings
    from django.core.cache import cache
    import logging

    logger = logging.getLogger(__name__)

    def get_db_engine():
        if hasattr(settings, "DATABASE_URL"):
            return "postgres"
        return "sqlite"

    def is_elasticsearch_available():
        try:
            from elasticsearch import Elasticsearch

            host = settings.ELASTICSEARCH_DSL.get("default", {}).get(
                "hosts", "localhost:9200"
            )
            es = Elasticsearch(hosts=[host])
            return es.ping()
        except Exception:
            return False

    def search_with_elasticsearch(query, clinic_id=None):
        from patients.documents import PatientDocument
        from treatments.documents import TreatmentDocument
        from billing.documents import InvoiceDocument

        results = {
            "patients": [],
            "treatments": [],
            "invoices": [],
        }

        try:
            # Search patients
            patient_search = PatientDocument.search()
            if clinic_id:
                patient_search = patient_search.filter("term", clinic_id=clinic_id)

            patient_query = patient_search.query(
                "multi_match",
                query=query,
                fields=["first_name^2", "last_name^2", "full_name^2", "phone", "email"],
                fuzziness="AUTO",
            )

            for hit in patient_query[:10]:
                results["patients"].append(
                    {
                        "id": hit.id,
                        "full_name": hit.full_name,
                        "first_name": hit.first_name,
                        "last_name": hit.last_name,
                        "phone": hit.phone,
                    }
                )
        except Exception as e:
            logger.warning(f"Elasticsearch patient search failed: {e}")

        try:
            # Search treatments
            treatment_search = TreatmentDocument.search()
            if clinic_id:
                treatment_search = treatment_search.filter("term", clinic_id=clinic_id)

            treatment_query = treatment_search.query(
                "multi_match",
                query=query,
                fields=["procedure^2", "diagnosis", "patient_name"],
                fuzziness="AUTO",
            )

            for hit in treatment_query[:8]:
                results["treatments"].append(
                    {
                        "id": hit.id,
                        "procedure": hit.procedure[:50] if hit.procedure else "",
                        "patient_name": hit.patient_name,
                    }
                )
        except Exception as e:
            logger.warning(f"Elasticsearch treatment search failed: {e}")

        try:
            # Search invoices
            invoice_search = InvoiceDocument.search()
            if clinic_id:
                invoice_search = invoice_search.filter("term", clinic_id=clinic_id)

            invoice_query = invoice_search.query(
                "multi_match",
                query=query,
                fields=["invoice_number^2", "patient_name"],
                fuzziness="AUTO",
            )

            for hit in invoice_query[:8]:
                results["invoices"].append(
                    {
                        "id": hit.id,
                        "invoice_number": hit.invoice_number,
                        "status": hit.status,
                        "amount": str(hit.total_amount) if hit.total_amount else "0",
                        "patient_name": hit.patient_name,
                    }
                )
        except Exception as e:
            logger.warning(f"Elasticsearch invoice search failed: {e}")

        return results

    @api_view(["GET"])
    def global_search(request):
        query = request.GET.get("q", "")

        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized"}, status=401)

        if len(query) < 2:
            return Response({})

        clinic = getattr(request.user, "clinic", None)
        clinic_id = clinic.id if clinic else None

        # Try Elasticsearch first, fallback to Django ORM
        use_elasticsearch = cache.get("elasticsearch_available")
        if use_elasticsearch is None:
            use_elasticsearch = is_elasticsearch_available()
            cache.set("elasticsearch_available", use_elasticsearch, 60)

        if use_elasticsearch:
            try:
                results = search_with_elasticsearch(query, clinic_id)

                # Add search log
                try:
                    from search.models import SearchLog

                    total_results = (
                        len(results.get("patients", []))
                        + len(results.get("treatments", []))
                        + len(results.get("invoices", []))
                    )
                    SearchLog.objects.create(
                        query=query,
                        user=request.user,
                        clinic=clinic,
                        results_count=total_results,
                    )
                except Exception:
                    pass

                # Get appointments from Django (no ES document yet)
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
                else:
                    results["clinics"] = []

                return Response(results)
            except Exception as e:
                logger.error(f"Elasticsearch search error: {e}")
                cache.set("elasticsearch_available", False, 60)

        # Fallback to Django ORM with PostgreSQL full-text search
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
            except Exception:
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

        # Log search
        try:
            from search.models import SearchLog

            SearchLog.objects.create(
                query=query,
                user=request.user,
                clinic=clinic,
                results_count=len(results.get("patients", []))
                + len(results.get("treatments", []))
                + len(results.get("invoices", [])),
            )
        except Exception:
            pass

        return Response(results)

    urlpatterns.append(path("api/search/", global_search, name="global_search"))
