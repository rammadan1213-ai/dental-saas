from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth, TruncDay, TruncWeek
from django.http import JsonResponse
from datetime import datetime, timedelta
import json
from accounts.models import User as DjangoUser
from patients.models import Patient
from appointments.models import Appointment
from treatments.models import Treatment
from billing.models import Invoice, Payment


class ClinicFilterMixin:
    def get_clinic(self):
        user = self.request.user

        if user.is_superuser:
            selected_id = self.request.session.get("selected_clinic_id")
            if selected_id:
                from clinics.models import Clinic

                return Clinic.objects.filter(id=selected_id).first()
            return None

        return getattr(user, "clinic", None)

    def get_queryset_filtered(self, queryset):
        clinic = self.get_clinic()
        if clinic:
            return queryset.filter(clinic=clinic)
        return queryset


class DashboardView(LoginRequiredMixin, ClinicFilterMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_superuser:
            return self.get_superadmin_context(context)

        clinic = self.get_clinic()
        return self.get_clinic_context(context, clinic)

    def get_superadmin_context(self, context):
        from clinics.models import Clinic, Subscription

        today = datetime.now().date()
        month_start = today.replace(day=1)

        context["total_clinics"] = Clinic.objects.count()
        context["active_clinics"] = Clinic.objects.filter(is_active=True).count()
        context["total_patients"] = Patient.objects.filter(is_active=True).count()
        context["total_users"] = DjangoUser.objects.count()
        context["pending_appointments"] = Appointment.objects.filter(
            date=today, status__in=["pending", "confirmed"]
        ).count()
        context["revenue_this_month"] = (
            Invoice.objects.filter(issue_date__gte=month_start).aggregate(
                Sum("amount_paid")
            )["amount_paid__sum"]
            or 0
        )
        context["is_superadmin"] = True
        context["all_clinics"] = Clinic.objects.all()[:20]
        return context

    def get_clinic_context(self, context, clinic):
        today = datetime.now().date()
        month_start = today.replace(day=1)

        base_patients = Patient.objects.all()
        base_appointments = Appointment.objects.all()
        base_invoices = Invoice.objects.all()
        base_treatments = Treatment.objects.all()

        if clinic:
            base_patients = base_patients.filter(clinic=clinic)
            base_appointments = base_appointments.filter(clinic=clinic)
            base_invoices = base_invoices.filter(clinic=clinic)
            base_treatments = base_treatments.filter(clinic=clinic)

        context["total_patients"] = base_patients.filter(is_active=True).count()
        context["total_patients_this_month"] = base_patients.filter(
            created_at__gte=month_start, is_active=True
        ).count()

        context["total_appointments"] = base_appointments.filter(date=today).count()
        context["appointments_this_week"] = base_appointments.filter(
            date__gte=today - timedelta(days=7)
        ).count()

        pending_appointments = base_appointments.filter(
            date=today, status__in=["pending", "confirmed"]
        ).count()
        context["pending_appointments"] = pending_appointments

        context["total_revenue"] = (
            base_invoices.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        )
        context["revenue_this_month"] = (
            base_invoices.filter(issue_date__gte=month_start).aggregate(
                Sum("amount_paid")
            )["amount_paid__sum"]
            or 0
        )

        context["outstanding_amount"] = (
            base_invoices.filter(status__in=["sent", "partial", "overdue"]).aggregate(
                Sum("total_amount")
            )["total_amount__sum"]
            or 0
        )

        context["total_treatments"] = base_treatments.count()
        context["treatments_this_month"] = base_treatments.filter(
            treatment_date__gte=month_start
        ).count()

        upcoming_appointments = base_appointments.filter(
            date=today, status__in=["pending", "confirmed"]
        ).select_related("patient", "dentist")[:5]
        context["upcoming_appointments"] = upcoming_appointments

        recent_patients = base_patients.filter(is_active=True).order_by("-created_at")[
            :5
        ]
        context["recent_patients"] = recent_patients

        return context


class AnalyticsView(LoginRequiredMixin, ClinicFilterMixin, TemplateView):
    template_name = "dashboard/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clinic = self.get_clinic()

        today = datetime.now().date()
        last_30_days = today - timedelta(days=30)
        last_12_months = today - timedelta(days=365)

        base_appointments = Appointment.objects.all()
        base_invoices = Invoice.objects.all()
        base_treatments = Treatment.objects.all()

        if clinic:
            base_appointments = base_appointments.filter(clinic=clinic)
            base_invoices = base_invoices.filter(clinic=clinic)
            base_treatments = base_treatments.filter(clinic=clinic)

        appointment_stats = (
            base_appointments.filter(date__gte=last_30_days)
            .annotate(day=TruncDay("date"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        appointment_data = {
            "labels": [stat["day"].strftime("%Y-%m-%d") for stat in appointment_stats],
            "values": [stat["count"] for stat in appointment_stats],
        }
        context["appointment_stats"] = json.dumps(appointment_data)

        status_distribution = (
            base_appointments.filter(date__gte=last_30_days)
            .values("status")
            .annotate(count=Count("id"))
        )
        status_data = {
            "labels": [
                str(
                    dict(Appointment.Status.choices).get(stat["status"], stat["status"])
                )
                for stat in status_distribution
            ],
            "values": [stat["count"] for stat in status_distribution],
        }
        context["status_distribution"] = json.dumps(status_data)

        revenue_by_month = (
            base_invoices.filter(issue_date__gte=last_12_months)
            .annotate(month=TruncMonth("issue_date"))
            .values("month")
            .annotate(total=Sum("amount_paid"))
            .order_by("month")
        )

        revenue_data = {
            "labels": [stat["month"].strftime("%Y-%m") for stat in revenue_by_month],
            "values": [float(stat["total"] or 0) for stat in revenue_by_month],
        }
        context["revenue_by_month"] = json.dumps(revenue_data)

        dentist_performance = (
            base_treatments.filter(treatment_date__gte=last_30_days)
            .values("dentist__first_name", "dentist__last_name")
            .annotate(count=Count("id"), revenue=Sum("cost"))
            .order_by("-count")
        )

        dentist_data = {
            "labels": [
                f"{stat['dentist__first_name']} {stat['dentist__last_name']}"
                for stat in dentist_performance
            ],
            "treatment_counts": [stat["count"] for stat in dentist_performance],
            "revenues": [float(stat["revenue"] or 0) for stat in dentist_performance],
        }
        context["dentist_performance"] = json.dumps(dentist_data)

        return context


class ReportView(LoginRequiredMixin, ClinicFilterMixin, View):
    template_name = "dashboard/reports.html"

    def get(self, request):
        clinic = self.get_clinic()
        report_type = request.GET.get("type", "overview")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if not date_from:
            date_from = datetime.now().date().replace(day=1)
        else:
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()

        if not date_to:
            date_to = datetime.now().date()
        else:
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

        base_filter = {}
        if clinic:
            base_filter["clinic"] = clinic

        appointments = Appointment.objects.filter(
            date__gte=date_from, date__lte=date_to, **base_filter
        )

        invoices = Invoice.objects.filter(
            issue_date__gte=date_from, issue_date__lte=date_to, **base_filter
        )

        treatments = Treatment.objects.filter(
            treatment_date__gte=date_from, treatment_date__lte=date_to, **base_filter
        )

        context = {
            "report_type": report_type,
            "date_from": date_from,
            "date_to": date_to,
            "total_appointments": appointments.count(),
            "completed_appointments": appointments.filter(status="completed").count(),
            "cancelled_appointments": appointments.filter(status="cancelled").count(),
            "total_invoices": invoices.count(),
            "total_revenue": invoices.aggregate(Sum("amount_paid"))["amount_paid__sum"]
            or 0,
            "total_outstanding": invoices.aggregate(Sum("total_amount"))[
                "total_amount__sum"
            ]
            or 0,
            "total_treatments": treatments.count(),
            "treatment_revenue": treatments.aggregate(Sum("cost"))["cost__sum"] or 0,
        }

        return render(request, self.template_name, context)


def get_dashboard_stats(request):
    today = datetime.now().date()
    month_start = today.replace(day=1)
    clinic = getattr(request.user, "clinic", None)

    base_filter = {}
    if clinic:
        base_filter["clinic"] = clinic

    stats = {
        "total_patients": Patient.objects.filter(is_active=True, **base_filter).count(),
        "patients_this_month": Patient.objects.filter(
            created_at__gte=month_start, is_active=True, **base_filter
        ).count(),
        "total_appointments": Appointment.objects.filter(
            date=today, **base_filter
        ).count(),
        "pending_appointments": Appointment.objects.filter(
            date=today, status__in=["pending", "confirmed"], **base_filter
        ).count(),
        "revenue_this_month": float(
            Invoice.objects.filter(
                issue_date__gte=month_start, **base_filter
            ).aggregate(Sum("amount_paid"))["amount_paid__sum"]
            or 0
        ),
        "outstanding_amount": float(
            Invoice.objects.filter(
                status__in=["sent", "partial", "overdue"], **base_filter
            ).aggregate(Sum("total_amount"))["total_amount__sum"]
            or 0
        ),
    }

    return JsonResponse(stats)


def smart_insights(request):
    clinic = getattr(request.user, "clinic", None)

    if not clinic:
        return render(request, "dashboard/insights.html", {})

    top_treatments = (
        Treatment.objects.filter(clinic=clinic)
        .values("dental_service__name", "procedure")
        .annotate(total_count=Count("id"))
        .annotate(total_revenue=Sum("cost"))
        .order_by("-total_count")[:5]
    )

    revenue = (
        Invoice.objects.filter(clinic=clinic, status="paid").aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    completed_treatments = Treatment.objects.filter(
        clinic=clinic, status="completed"
    ).count()

    total_appointments = Appointment.objects.filter(clinic=clinic).count()
    completed_appointments = Appointment.objects.filter(
        clinic=clinic, status="completed"
    ).count()

    context = {
        "top_treatments": top_treatments,
        "revenue": revenue,
        "completed_treatments": completed_treatments,
        "total_appointments": total_appointments,
        "completed_appointments": completed_appointments,
        "completion_rate": round(
            (completed_appointments / total_appointments * 100)
            if total_appointments > 0
            else 0,
            1,
        ),
    }

    return render(request, "dashboard/insights.html", context)
