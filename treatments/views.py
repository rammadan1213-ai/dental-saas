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
from .models import Treatment, DentalService
from .forms import TreatmentForm, TreatmentFilterForm


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
            "dentist",
        ]


class TreatmentListView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, ListView
):
    model = Treatment
    template_name = "treatments/treatment_list.html"
    context_object_name = "treatments"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_dentist:
            queryset = queryset.filter(dentist=self.request.user)

        status = self.request.GET.get("status")
        dentist = self.request.GET.get("dentist")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        search = self.request.GET.get("search")

        if status:
            queryset = queryset.filter(status=status)
        if dentist:
            queryset = queryset.filter(dentist_id=dentist)
        if date_from:
            queryset = queryset.filter(treatment_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(treatment_date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search)
                | Q(patient__last_name__icontains=search)
                | Q(procedure__icontains=search)
                | Q(diagnosis__icontains=search)
            )

        return queryset.select_related(
            "patient", "dentist", "appointment", "dental_service"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = TreatmentFilterForm(self.request.GET)
        return context


class TreatmentCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Treatment
    form_class = TreatmentForm
    template_name = "treatments/treatment_form.html"
    success_url = reverse_lazy("treatments:treatment_list")

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_dentist:
            initial["dentist"] = self.request.user
        return initial

    def form_valid(self, form):
        clinic = getattr(self.request.user, "clinic", None)
        form.instance.clinic = clinic
        messages.success(self.request, "Treatment recorded successfully.")
        return super().form_valid(form)


class TreatmentUpdateView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, UpdateView
):
    model = Treatment
    form_class = TreatmentForm
    template_name = "treatments/treatment_form.html"
    success_url = reverse_lazy("treatments:treatment_list")

    def form_valid(self, form):
        messages.success(self.request, "Treatment updated successfully.")
        return super().form_valid(form)


class TreatmentDeleteView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, DeleteView
):
    model = Treatment
    template_name = "treatments/treatment_confirm_delete.html"
    success_url = reverse_lazy("treatments:treatment_list")

    def form_valid(self, form):
        messages.success(self.request, "Treatment deleted successfully.")
        return super().form_valid(form)


class TreatmentDetailView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, DetailView
):
    model = Treatment
    template_name = "treatments/treatment_detail.html"
    context_object_name = "treatment"


class DentalServiceListView(LoginRequiredMixin, ListView):
    model = DentalService
    template_name = "treatments/service_list.html"
    context_object_name = "services"
    paginate_by = 12

    def get_queryset(self):
        return DentalService.objects.filter(is_active=True).order_by("category", "name")


class DentalServiceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = DentalService
    fields = [
        "name",
        "description",
        "category",
        "default_price",
        "duration_minutes",
        "is_active",
        "requires_appointment",
    ]
    template_name = "treatments/service_form.html"
    success_url = reverse_lazy("treatments:service_list")

    def test_func(self):
        return self.request.user.is_admin_user

    def form_valid(self, form):
        messages.success(self.request, "Service created successfully.")
        return super().form_valid(form)


class DentalServiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DentalService
    fields = [
        "name",
        "description",
        "category",
        "default_price",
        "duration_minutes",
        "is_active",
        "requires_appointment",
    ]
    template_name = "treatments/service_form.html"
    success_url = reverse_lazy("treatments:service_list")

    def test_func(self):
        return self.request.user.is_admin_user

    def form_valid(self, form):
        messages.success(self.request, "Service updated successfully.")
        return super().form_valid(form)


class DentalServiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DentalService
    template_name = "treatments/service_confirm_delete.html"
    success_url = reverse_lazy("treatments:service_list")

    def test_func(self):
        return self.request.user.is_admin_user
