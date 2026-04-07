from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    TemplateView,
)
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q, IntegerField
from datetime import datetime, timedelta
from .models import User, AuditLog
from .forms import (
    UserLoginForm,
    CustomUserCreationForm,
    CustomUserChangeForm,
    PasswordResetForm,
)
from clinics.models import Clinic, Subscription
from billing.models import Invoice


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        form = UserLoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.get_full_name()}!")
                    next_url = request.GET.get("next", "dashboard:home")
                    return redirect(next_url)
                else:
                    messages.error(request, "Your account is disabled.")
            else:
                messages.error(request, "Invalid username or password.")
        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("accounts:login")

    def get(self, request):
        return self.post(request)


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.is_admin_user or self.request.user.is_superuser


class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.is_superuser


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.is_staff or self.request.user.is_admin_user


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Super admin sees ALL users from ALL clinics
        if self.request.user.is_superuser:
            pass  # Show all users
        else:
            # Regular admin only sees users from their clinic
            queryset = queryset.filter(clinic=self.request.user.clinic)

        role = self.request.GET.get("role")
        search = self.request.GET.get("search")

        if role:
            queryset = queryset.filter(role=role)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
            )
        return queryset.select_related("clinic")


class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # If not super admin, restrict to own clinic
        if not self.request.user.is_superuser:
            kwargs["initial"]["clinic"] = self.request.user.clinic
        return kwargs

    def form_valid(self, form):
        # If not super admin, assign to their clinic
        if not self.request.user.is_superuser:
            form.instance.clinic = self.request.user.clinic
        messages.success(self.request, "User created successfully.")
        return super().form_valid(form)


class UserDetailView(AdminRequiredMixin, DetailView):
    model = User
    template_name = "accounts/user_detail.html"
    context_object_name = "user_obj"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset.select_related("clinic")
        return queryset.filter(clinic=self.request.user.clinic)


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def get_queryset(self):
        queryset = super().get_queryset()
        # Super admin can edit all users, regular admin only their clinic
        if not self.request.user.is_superuser:
            queryset = queryset.filter(clinic=self.request.user.clinic)
        return queryset

    def form_valid(self, form):
        messages.success(self.request, "User updated successfully.")
        return super().form_valid(form)


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:user_list")

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(clinic=self.request.user.clinic)
        return queryset

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Exception as e:
            messages.error(self.request, f"Error: {str(e)}")
            return None

    def form_valid(self, form):
        if self.get_object() is None:
            return redirect("accounts:user_list")
        messages.success(self.request, "User deleted successfully.")
        return super().form_valid(form)


class UserProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "accounts/profile.html"
    context_object_name = "user_profile"

    def get_object(self):
        return self.request.user


class ChangePasswordView(LoginRequiredMixin, View):
    template_name = "accounts/change_password.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords don't match.")
            return render(request, self.template_name)

        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, self.template_name)

        user = request.user
        user.set_password(password1)
        user.save()
        login(request, user)

        messages.success(request, "Password changed successfully!")
        return redirect("accounts:profile")


class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class CustomPasswordResetViewNoEmail(View):
    template_name = "accounts/password_reset.html"

    def get(self, request):
        form = PasswordResetForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        from django.contrib.auth import get_user_model
        from .models import PasswordReset
        from django.utils import timezone
        import secrets

        email = request.POST.get("email")
        User = get_user_model()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.success(
                request, "If that email exists, a reset link has been sent."
            )
            return redirect("accounts:password_reset_done")

        token = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(hours=24)

        PasswordReset.objects.create(user=user, token=token, expires_at=expires)

        messages.success(request, "If that email exists, a reset link has been sent.")
        return redirect("accounts:password_reset_done")


class CustomPasswordResetConfirmViewNoEmail(View):
    template_name = "accounts/password_reset_confirm.html"

    def get(self, request, token):
        from .models import PasswordReset

        try:
            reset = PasswordReset.objects.get(token=token)
            if not reset.is_valid():
                messages.error(request, "Reset link expired or already used.")
                return redirect("accounts:password_reset")
        except PasswordReset.DoesNotExist:
            messages.error(request, "Invalid reset link.")
            return redirect("accounts:password_reset")

        return render(request, self.template_name, {"token": token})

    def post(self, request, token):
        from .models import PasswordReset
        from django.contrib.auth import get_user_model

        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords don't match.")
            return render(request, self.template_name, {"token": token})

        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, self.template_name, {"token": token})

        try:
            reset = PasswordReset.objects.get(token=token)
            if not reset.is_valid():
                messages.error(request, "Reset link expired or already used.")
                return redirect("accounts:password_reset")

            user = reset.user
            user.set_password(password1)
            user.save()
            reset.used = True
            reset.save()

            messages.success(request, "Password reset successful! Please login.")
            return redirect("accounts:password_reset_complete")
        except PasswordReset.DoesNotExist:
            messages.error(request, "Invalid reset link.")
            return redirect("accounts:password_reset")


class CustomPasswordResetDoneViewNoEmail(TemplateView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetCompleteViewNoEmail(TemplateView):
    template_name = "accounts/password_reset_complete.html"


class AuditLogListView(SuperAdminRequiredMixin, ListView):
    model = AuditLog
    template_name = "accounts/audit_log_list.html"
    context_object_name = "logs"
    paginate_by = 20


class UserPasswordChangeView(LoginRequiredMixin, View):
    template_name = "accounts/user_password_change.html"

    def get(self, request, pk):
        return render(request, self.template_name, {"pk": pk})

    def post(self, request, pk):
        from django.contrib.auth.forms import PasswordChangeForm

        user = User.objects.get(pk=pk)
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password changed successfully!")
            return redirect("accounts:user_list")
        return render(request, self.template_name, {"pk": pk, "form": form})


class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return render(request, self.template_name)

    def post(self, request):
        clinic_name = request.POST.get("clinic_name")
        owner_name = request.POST.get("owner_name")
        owner_email = request.POST.get("email")
        owner_password = request.POST.get("password")
        plan = request.POST.get("plan", "basic")

        username = owner_email.split("@")[0]
        if User.objects.filter(username=username).exists():
            messages.error(request, "User already exists. Please login.")
            return redirect("accounts:login")

        from clinics.models import Subscription

        user = User.objects.create_user(
            username=username,
            email=owner_email,
            password=owner_password,
            first_name=owner_name,
            role="admin",
        )

        clinic = Clinic.objects.create(
            name=clinic_name,
            owner=user,
        )

        user.clinic = clinic
        user.save()

        subscription = Subscription.objects.create(
            clinic=clinic,
            plan=plan,
            is_active=True,
            expiry_date=datetime.now().date() + timedelta(days=3),  # 3-day trial
        )

        # Start the trial
        subscription.start_trial()

        user = authenticate(request, username=user.username, password=owner_password)
        if user:
            login(request, user)
            messages.success(
                request, f"Welcome! Your clinic '{clinic_name}' has been created!"
            )
            return redirect("dashboard:home")

        messages.success(request, "Account created! Please login.")
        return redirect("accounts:login")


class SuperAdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/superadmin_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Access denied. Superadmin only.")
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import date

        context["today"] = date.today()
        context["total_clinics"] = Clinic.objects.count()
        context["active_clinics"] = Clinic.objects.filter(is_active=True).count()
        context["total_subscriptions"] = Subscription.objects.filter(
            is_active=True
        ).count()

        context["expired_subscriptions"] = Subscription.objects.filter(
            expiry_date__lt=date.today()
        ).count()

        plan_counts = Subscription.objects.values("plan").annotate(count=Count("id"))
        context["basic_count"] = sum(
            s["count"] for s in plan_counts if s["plan"] == "basic"
        )
        context["pro_count"] = sum(
            s["count"] for s in plan_counts if s["plan"] == "pro"
        )
        context["enterprise_count"] = sum(
            s["count"] for s in plan_counts if s["plan"] == "enterprise"
        )

        plan_prices = {"basic": 10, "pro": 25, "enterprise": 50}
        monthly_revenue = 0
        for sub in Subscription.objects.filter(is_active=True):
            monthly_revenue += plan_prices.get(sub.plan, 0)
        context["monthly_revenue"] = monthly_revenue

        context["clinics"] = Clinic.objects.all().select_related("subscription")[:50]
        context["recent_signups"] = Clinic.objects.order_by("-created_at")[:10]

        # Recent user logins
        context["recent_logins"] = (
            User.objects.select_related("clinic").order_by("-last_login")[:20]
            if User.objects.exists()
            else []
        )

        return context


@login_required
def toggle_clinic_status(request, clinic_id):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Access denied"}, status=403)

    clinic = get_object_or_404(Clinic, id=clinic_id)
    clinic.is_active = not clinic.is_active
    clinic.save()
    return JsonResponse({"success": True, "is_active": clinic.is_active})


@login_required
def update_clinic_subscription(request, clinic_id):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Access denied"}, status=403)

    if request.method == "POST":
        import json

        data = json.loads(request.body)
        clinic = get_object_or_404(Clinic, id=clinic_id)

        plan = data.get("plan")
        days = data.get("days", 30)

        subscription = clinic.subscription
        subscription.plan = plan
        subscription.is_active = True
        subscription.expiry_date = datetime.now().date() + timedelta(days=int(days))
        subscription.save()

        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request"}, status=400)


class ClinicDetailView(LoginRequiredMixin, DetailView):
    model = Clinic
    template_name = "accounts/clinic_detail.html"
    context_object_name = "clinic"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Access denied.")
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = User.objects.filter(clinic=self.object)
        context["patient_count"] = self.object.patients.count()
        context["appointment_count"] = self.object.appointments.count()
        context["invoice_count"] = self.object.invoices.count()
        return context


class ClinicSettingsView(LoginRequiredMixin, View):
    template_name = "accounts/clinic_settings.html"

    def get(self, request):
        clinic = getattr(request.user, "clinic", None)
        if not clinic:
            messages.error(request, "No clinic associated with your account.")
            return redirect("dashboard:home")

        context = {
            "clinic": clinic,
            "patient_count": clinic.patients.count()
            if hasattr(clinic, "patients")
            else 0,
            "user_count": clinic.users.count(),
            "patient_percentage": min(
                100,
                (clinic.patients.count() / clinic.subscription.patient_limit * 100)
                if clinic.subscription
                else 0,
            ),
            "user_percentage": min(100, (clinic.users.count() / 5 * 100)),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        clinic = getattr(request.user, "clinic", None)
        if not clinic:
            return redirect("dashboard:home")

        clinic.name = request.POST.get("name", clinic.name)
        clinic.email = request.POST.get("email", clinic.email)
        clinic.phone = request.POST.get("phone", clinic.phone)
        clinic.address = request.POST.get("address", clinic.address)
        clinic.save()

        messages.success(request, "Clinic settings updated successfully!")
        return redirect("accounts:clinic_settings")


class SwitchToClinicView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_superuser:
            messages.error(request, "Access denied.")
            return redirect("dashboard:home")

        clinic_id = request.POST.get("clinic_id")
        if not clinic_id:
            return redirect("dashboard:home")

        from clinics.models import Clinic

        clinic = get_object_or_404(Clinic, id=clinic_id)

        request.session["selected_clinic_id"] = clinic.id
        messages.success(request, f"Switched to {clinic.name}")
        return redirect("dashboard:home")
