from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
import json
from .models import Appointment
from .forms import AppointmentForm, AppointmentFilterForm
from notifications.views import notify_appointment_created


class ClinicFilterMixin:
    def get_clinic(self):
        return getattr(self.request.user, "clinic", None)

    def get_queryset(self):
        queryset = super().get_queryset()
        clinic = self.get_clinic()
        if clinic:
            queryset = queryset.filter(clinic=clinic)
        return queryset


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role in [
            "admin",
            "receptionist",
            "dentist",
        ]


class AppointmentListView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, ListView
):
    model = Appointment
    template_name = "appointments/appointment_list.html"
    context_object_name = "appointments"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_dentist:
            queryset = queryset.filter(dentist=self.request.user)

        status = self.request.GET.get("status")
        priority = self.request.GET.get("priority")
        dentist = self.request.GET.get("dentist")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        search = self.request.GET.get("search")

        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if dentist:
            queryset = queryset.filter(dentist_id=dentist)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search)
                | Q(patient__last_name__icontains=search)
                | Q(patient__phone__icontains=search)
            )

        return queryset.select_related("patient", "dentist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = AppointmentFilterForm(self.request.GET)
        return context


class AppointmentCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = "appointments/appointment_form.html"
    success_url = reverse_lazy("appointments:appointment_list")

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_dentist:
            initial["dentist"] = self.request.user
        return initial

    def form_valid(self, form):
        clinic = getattr(self.request.user, "clinic", None)
        form.instance.clinic = clinic
        response = super().form_valid(form)
        if clinic:
            notify_appointment_created(self.request.user, form.instance)
        messages.success(self.request, "Appointment scheduled successfully.")
        return response


class AppointmentUpdateView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, UpdateView
):
    model = Appointment
    form_class = AppointmentForm
    template_name = "appointments/appointment_form.html"
    success_url = reverse_lazy("appointments:appointment_list")

    def form_valid(self, form):
        messages.success(self.request, "Appointment updated successfully.")
        return super().form_valid(form)


class AppointmentDeleteView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, DeleteView
):
    model = Appointment
    template_name = "appointments/appointment_confirm_delete.html"
    success_url = reverse_lazy("appointments:appointment_list")

    def form_valid(self, form):
        messages.success(self.request, "Appointment deleted successfully.")
        return super().form_valid(form)


class AppointmentDetailView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, DetailView
):
    model = Appointment
    template_name = "appointments/appointment_detail.html"
    context_object_name = "appointment"


class AppointmentCalendarView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, ListView
):
    model = Appointment
    template_name = "appointments/appointment_calendar.html"
    context_object_name = "appointments"

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_dentist:
            queryset = queryset.filter(dentist=self.request.user)

        date = self.request.GET.get("date")
        month = self.request.GET.get("month")
        year = self.request.GET.get("year")

        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif date:
            queryset = queryset.filter(date=date)
        else:
            today = datetime.now().date()
            queryset = queryset.filter(date=today)

        return queryset.select_related("patient", "dentist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        appointments_json = []
        for apt in context["appointments"]:
            appointments_json.append(
                {
                    "id": apt.id,
                    "title": f"{apt.patient.full_name} - {apt.reason[:30]}",
                    "start": f"{apt.date.isoformat()}T{apt.start_time.isoformat()}",
                    "end": f"{apt.date.isoformat()}T{apt.end_time.isoformat()}",
                    "color": self.get_color_by_status(apt.status),
                    "url": reverse_lazy(
                        "appointments:appointment_detail", kwargs={"pk": apt.id}
                    ),
                }
            )

        context["appointments_json"] = json.dumps(
            appointments_json, cls=DjangoJSONEncoder
        )
        return context

    def get_color_by_status(self, status):
        colors = {
            "pending": "#ffc107",
            "confirmed": "#17a2b8",
            "completed": "#28a745",
            "cancelled": "#dc3545",
            "no_show": "#6c757d",
        }
        return colors.get(status, "#007bff")


def update_appointment_status(request, pk):
    if request.method == "POST":
        appointment = get_object_or_404(Appointment, pk=pk)
        clinic = getattr(request.user, "clinic", None)
        if clinic and appointment.clinic != clinic:
            return JsonResponse({"success": False, "error": "Unauthorized"})
        new_status = request.POST.get("status")
        if new_status in dict(Appointment.Status.choices):
            appointment.status = new_status
            appointment.save()
            return JsonResponse({"success": True, "status": new_status})
    return JsonResponse({"success": False})


def get_appointments_json(request):
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    dentist_id = request.GET.get("dentist")

    queryset = Appointment.objects.select_related("patient", "dentist")
    clinic = getattr(request.user, "clinic", None)
    if clinic:
        queryset = queryset.filter(clinic=clinic)

    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)
    if dentist_id:
        queryset = queryset.filter(dentist_id=dentist_id)

    appointments = [
        {
            "id": apt.id,
            "title": apt.patient.full_name,
            "start": f"{apt.date.isoformat()}T{apt.start_time.isoformat()}",
            "end": f"{apt.date.isoformat()}T{apt.end_time.isoformat()}",
            "status": apt.status,
            "patient_name": apt.patient.full_name,
            "dentist_name": apt.dentist.get_full_name()
            if apt.dentist
            else "Unassigned",
        }
        for apt in queryset
    ]

    return JsonResponse(appointments, safe=False)
