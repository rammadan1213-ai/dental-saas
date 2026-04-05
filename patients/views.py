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
from django.core.paginator import Paginator
from .models import Patient, PatientDocument
from .forms import PatientForm, PatientDocumentForm, PatientSearchForm
from notifications.views import notify_new_patient
from utils.permissions import check_patient_limit, get_plan_features


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
        ]


class PatientListView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, ListView
):
    model = Patient
    template_name = "patients/patient_list.html"
    context_object_name = "patients"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        search = self.request.GET.get("search")
        gender = self.request.GET.get("gender")

        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
            )
        if gender:
            queryset = queryset.filter(gender=gender)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = PatientSearchForm(self.request.GET)
        clinic = getattr(self.request.user, "clinic", None)
        if clinic:
            can_add, _, limit, current = check_patient_limit(self.request.user)
            context["patient_limit"] = limit
            context["patient_count"] = current
        return context


class PatientCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    success_url = reverse_lazy("patients:patient_list")

    def get(self, request, *args, **kwargs):
        can_add, message, limit, current = check_patient_limit(request.user)
        if not can_add:
            clinic = getattr(request.user, "clinic", None)
            current_plan = "basic"
            if clinic and hasattr(clinic, "subscription"):
                current_plan = clinic.subscription.plan
            return render(
                request,
                "upgrade_required.html",
                {
                    "title": "Patient Limit Reached",
                    "message": message,
                    "current_plan": current_plan,
                    "target_plan": "Pro",
                    "feature_name": "More Patients",
                    "features": [
                        f"{limit}+ Patients",
                        "Priority Support",
                        "Advanced Features",
                    ],
                },
            )
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        clinic = getattr(self.request.user, "clinic", None)
        form.instance.clinic = clinic
        response = super().form_valid(form)
        notify_new_patient(self.request.user, form.instance)
        messages.success(self.request, "Patient created successfully.")
        return response


class PatientUpdateView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, UpdateView
):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    success_url = reverse_lazy("patients:patient_list")

    def form_valid(self, form):
        messages.success(self.request, "Patient updated successfully.")
        return super().form_valid(form)


class PatientDeleteView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, DeleteView
):
    model = Patient
    template_name = "patients/patient_confirm_delete.html"
    success_url = reverse_lazy("patients:patient_list")

    def form_valid(self, form):
        patient = self.get_object()
        patient.is_active = False
        patient.save()
        messages.success(self.request, "Patient deactivated successfully.")
        return JsonResponse({"success": True})


class PatientDetailView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, DetailView
):
    model = Patient
    template_name = "patients/patient_detail.html"
    context_object_name = "patient"


class PatientDocumentUploadView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = PatientDocument
    form_class = PatientDocumentForm
    template_name = "patients/document_form.html"

    def get_success_url(self):
        return reverse_lazy("patients:patient_detail", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        patient = get_object_or_404(Patient, pk=self.kwargs["pk"])
        clinic = getattr(self.request.user, "clinic", None)
        form.instance.clinic = clinic
        form.instance.patient = patient
        messages.success(self.request, "Document uploaded successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient"] = get_object_or_404(Patient, pk=self.kwargs["pk"])
        return context


def get_patients_json(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    search = request.GET.get("q", request.GET.get("search", ""))
    status = request.GET.get("status")
    gender = request.GET.get("gender")
    page = request.GET.get("page", 1)
    limit = min(int(request.GET.get("limit", 20)), 50)

    clinic = getattr(request.user, "clinic", None)

    if request.user.is_superuser:
        patients = Patient.objects.all()
    elif clinic:
        patients = Patient.objects.filter(clinic=clinic)
    else:
        return JsonResponse({"error": "No clinic found"}, status=400)

    if search:
        patients = patients.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(phone__icontains=search)
            | Q(email__icontains=search)
            | Q(full_name__icontains=search)
        )

    if status:
        patients = patients.filter(is_active=(status == "active"))

    if gender:
        patients = patients.filter(gender=gender)

    patients = patients.select_related("clinic").only(
        "id",
        "first_name",
        "last_name",
        "phone",
        "email",
        "gender",
        "is_active",
        "date_of_birth",
    )

    paginator = Paginator(patients, limit)
    patients_page = paginator.get_page(page)

    data = [
        {
            "id": p.id,
            "full_name": p.full_name,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "phone": p.phone,
            "email": p.email,
            "gender": p.gender,
            "is_active": p.is_active,
            "age": p.age,
        }
        for p in patients_page
    ]

    return JsonResponse(
        {
            "results": data,
            "count": paginator.count,
            "pages": paginator.num_pages,
            "current_page": int(page),
        },
        safe=False,
    )
