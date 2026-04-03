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
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Sum
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from xhtml2pdf import pisa
from io import BytesIO
import stripe
import json
from .models import Invoice, InvoiceItem, Payment
from .forms import InvoiceForm, InvoiceItemFormSet, PaymentForm, InvoiceFilterForm
from utils.permissions import has_feature, get_plan_features
from clinics.models import Subscription


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


class InvoiceListView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, ListView
):
    model = Invoice
    template_name = "billing/invoice_list.html"
    context_object_name = "invoices"
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        if not has_feature(request.user, "billing"):
            clinic = getattr(request.user, "clinic", None)
            current_plan = "basic"
            if clinic and hasattr(clinic, "subscription"):
                current_plan = clinic.subscription.plan
            return render(
                request,
                "upgrade_required.html",
                {
                    "title": "Billing Not Available",
                    "message": "Billing and invoicing features are available on Pro and Enterprise plans.",
                    "current_plan": current_plan,
                    "target_plan": "Pro",
                    "feature_name": "Billing & Invoicing",
                    "features": [
                        "Unlimited Invoices",
                        "Payment Tracking",
                        "Revenue Reports",
                        "PDF Export",
                    ],
                },
            )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        status = self.request.GET.get("status")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        search = self.request.GET.get("search")

        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search)
                | Q(patient__first_name__icontains=search)
                | Q(patient__last_name__icontains=search)
            )

        return queryset.select_related("patient", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = InvoiceFilterForm(self.request.GET)

        invoices = context["invoices"]

        total_revenue = sum(inv.total_amount for inv in invoices)
        total_paid = sum(inv.amount_paid for inv in invoices)
        total_outstanding = total_revenue - total_paid

        context["total_revenue"] = total_revenue
        context["total_paid"] = total_paid
        context["total_outstanding"] = total_outstanding

        base_qs = Invoice.objects.filter(
            clinic=getattr(self.request.user, "clinic", None)
        )
        if self.request.user.is_superuser:
            base_qs = Invoice.objects.all()

        context["total_count"] = base_qs.count()
        context["paid_count"] = base_qs.filter(status="paid").count()
        context["partial_count"] = base_qs.filter(status="partial").count()
        context["pending_count"] = base_qs.filter(status="sent").count()
        context["overdue_count"] = base_qs.filter(status="overdue").count()

        return context


class InvoiceCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "billing/invoice_form.html"
    success_url = reverse_lazy("billing:invoice_list")

    def get(self, request, *args, **kwargs):
        if not has_feature(request.user, "billing"):
            clinic = getattr(request.user, "clinic", None)
            current_plan = "basic"
            if clinic and hasattr(clinic, "subscription"):
                current_plan = clinic.subscription.plan
            return render(
                request,
                "upgrade_required.html",
                {
                    "title": "Billing Not Available",
                    "message": "Create invoices with the Pro or Enterprise plan.",
                    "current_plan": current_plan,
                    "target_plan": "Pro",
                    "feature_name": "Billing & Invoicing",
                    "features": [
                        "Unlimited Invoices",
                        "Payment Tracking",
                        "Revenue Reports",
                    ],
                },
            )
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["issue_date"] = self.request.GET.get("issue_date", "")
        initial["due_date"] = self.request.GET.get("due_date", "")
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["items_formset"] = InvoiceItemFormSet(self.request.POST)
        else:
            context["items_formset"] = InvoiceItemFormSet()

        from treatments.models import Treatment

        treatments = Treatment.objects.all()
        if hasattr(self.request.user, "clinic") and self.request.user.clinic:
            treatments = treatments.filter(clinic=self.request.user.clinic)
        context["treatments"] = treatments

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context["items_formset"]

        form.instance.invoice_number = Invoice.generate_invoice_number()
        form.instance.created_by = self.request.user
        clinic = getattr(self.request.user, "clinic", None)
        form.instance.clinic = clinic

        treatment = form.cleaned_data.get("treatment")
        if treatment and not items_formset.initial:
            form.instance.patient = treatment.patient
            items_data = [
                {
                    "description": treatment.procedure,
                    "quantity": 1,
                    "unit_price": treatment.cost,
                }
            ]
            items_formset = InvoiceItemFormSet(initial=items_data)

        if items_formset.is_valid():
            saved_items = items_formset.save(commit=False)
            subtotal = sum((item.total_price or 0) for item in saved_items)
            form.instance.subtotal = subtotal
            tax_amount = float(form.instance.tax_amount or 0)
            discount_amount = float(form.instance.discount_amount or 0)
            form.instance.total_amount = subtotal + tax_amount - discount_amount

            response = super().form_valid(form)

            items_formset.instance = self.object
            items_formset.save()

            messages.success(self.request, "Invoice created successfully.")
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))


class InvoiceUpdateView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, UpdateView
):
    model = Invoice
    form_class = InvoiceForm
    template_name = "billing/invoice_form.html"

    def get_success_url(self):
        return reverse_lazy("billing:invoice_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["items_formset"] = InvoiceItemFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["items_formset"] = InvoiceItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context["items_formset"]

        if items_formset.is_valid():
            saved_items = items_formset.save(commit=False)
            subtotal = sum((item.total_price or 0) for item in saved_items)
            form.instance.subtotal = subtotal
            tax_amount = float(form.instance.tax_amount or 0)
            discount_amount = float(form.instance.discount_amount or 0)
            form.instance.total_amount = subtotal + tax_amount - discount_amount

            response = super().form_valid(form)
            items_formset.save()

            messages.success(self.request, "Invoice updated successfully.")
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))


class InvoiceDeleteView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, DeleteView
):
    model = Invoice
    template_name = "billing/invoice_confirm_delete.html"
    success_url = reverse_lazy("billing:invoice_list")

    def form_valid(self, form):
        messages.success(self.request, "Invoice deleted successfully.")
        return super().form_valid(form)


class InvoiceDetailView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, DetailView
):
    model = Invoice
    template_name = "billing/invoice_detail.html"
    context_object_name = "invoice"


class PaymentCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = "billing/payment_form.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["payment_date"] = self.request.GET.get("payment_date", "")
        return initial

    def get_success_url(self):
        return reverse_lazy(
            "billing:invoice_detail", kwargs={"pk": self.object.invoice.pk}
        )

    def form_valid(self, form):
        invoice = get_object_or_404(Invoice, pk=self.kwargs["pk"])
        clinic = getattr(self.request.user, "clinic", None)
        form.instance.clinic = clinic
        form.instance.invoice = invoice
        form.instance.recorded_by = self.request.user
        messages.success(self.request, "Payment recorded successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invoice"] = get_object_or_404(Invoice, pk=self.kwargs["pk"])
        return context


class PaymentListView(
    LoginRequiredMixin, StaffRequiredMixin, ClinicFilterMixin, ListView
):
    model = Payment
    template_name = "billing/payment_list.html"
    context_object_name = "payments"
    paginate_by = 10

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("invoice", "invoice__patient", "recorded_by")
        )


def export_invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    clinic = getattr(request.user, "clinic", None)
    if clinic and invoice.clinic != clinic:
        return HttpResponse("Unauthorized", status=403)
    template_path = "billing/invoice_pdf.html"

    invoice.subtotal = float(invoice.subtotal) if invoice.subtotal else 0
    invoice.tax_amount = float(invoice.tax_amount) if invoice.tax_amount else 0
    invoice.discount_amount = (
        float(invoice.discount_amount) if invoice.discount_amount else 0
    )
    invoice.total_amount = float(invoice.total_amount) if invoice.total_amount else 0
    invoice.amount_paid = float(invoice.amount_paid) if invoice.amount_paid else 0

    context = {"invoice": invoice}

    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    )

    pisa_status = pisa.CreatePDF(
        BytesIO(html.encode("UTF-8")), dest=response, encoding="UTF-8"
    )

    if pisa_status.err:
        return HttpResponse("PDF generation error")
    return response


from django.conf import settings

stripe.api_key = (
    settings.STRIPE_SECRET_KEY if hasattr(settings, "STRIPE_SECRET_KEY") else None
)


def create_checkout_session(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    clinic = getattr(request.user, "clinic", None)
    if not clinic:
        return JsonResponse({"error": "No clinic found"}, status=400)

    try:
        subscription = Subscription.objects.get(clinic=clinic)
        plan_prices = {
            "starter": 1000,
            "pro": 2500,
            "enterprise": 5000,
        }
        plan_names = {
            "starter": "Starter Plan",
            "pro": "Pro Plan",
            "enterprise": "Enterprise Plan",
        }

        amount = plan_prices.get(subscription.plan, 1000)
        plan_name = plan_names.get(subscription.plan, "Starter Plan")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": plan_name},
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=request.build_absolute_uri("/dashboard/") + "?payment=success",
            cancel_url=request.build_absolute_uri("/dashboard/") + "?payment=cancel",
            metadata={
                "clinic_id": clinic.id,
                "plan": subscription.plan,
            },
        )

        return JsonResponse({"id": session.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        from django.conf import settings

        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return HttpResponse(status=400)

    from clinics.models import Clinic

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        clinic_id = session.get("metadata", {}).get("clinic_id")
        plan = session.get("metadata", {}).get("plan", "starter")

        if clinic_id:
            try:
                clinic = Clinic.objects.get(id=clinic_id)
                sub, created = Subscription.objects.get_or_create(clinic=clinic)
                sub.status = Subscription.Status.ACTIVE
                sub.plan = plan
                sub.stripe_subscription_id = session.get("subscription") or session.get(
                    "id"
                )
                sub.save()
            except Exception:
                pass

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")

        if subscription_id:
            try:
                sub = Subscription.objects.get(stripe_subscription_id=subscription_id)
                sub.status = Subscription.Status.INACTIVE
                sub.save()
            except Exception:
                pass

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]

        try:
            sub = Subscription.objects.get(stripe_subscription_id=subscription["id"])
            sub.status = Subscription.Status.CANCELED
            sub.save()
        except Exception:
            pass

    return HttpResponse(status=200)


def subscription_view(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    clinic = getattr(request.user, "clinic", None)
    if not clinic:
        return redirect("dashboard:home")

    subscription, created = Subscription.objects.get_or_create(clinic=clinic)

    plan_info = {
        "starter": {
            "name": "Starter",
            "price": 10,
            "features": ["Up to 100 patients", "Basic billing"],
        },
        "pro": {
            "name": "Pro",
            "price": 25,
            "features": ["Up to 500 patients", "Advanced billing", "Priority support"],
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 50,
            "features": ["Unlimited patients", "All features", "Dedicated support"],
        },
    }

    return render(
        request,
        "billing/subscription.html",
        {
            "subscription": subscription,
            "plan_info": plan_info,
        },
    )


def cancel_subscription(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    clinic = getattr(request.user, "clinic", None)
    if clinic:
        try:
            sub = Subscription.objects.get(clinic=clinic)
            sub.status = Subscription.Status.CANCELED
            sub.save()
            messages.success(request, "Subscription canceled successfully.")
        except Subscription.DoesNotExist:
            messages.error(request, "No subscription found.")

    return redirect("billing:subscription")
