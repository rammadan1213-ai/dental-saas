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
from django.http import HttpResponse
from django.db.models import Q, Sum
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from .models import Invoice, InvoiceItem, Payment
from .forms import InvoiceForm, InvoiceItemFormSet, PaymentForm, InvoiceFilterForm


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

        total_revenue = sum(inv.total_amount for inv in context["invoices"])
        total_paid = sum(inv.amount_paid for inv in context["invoices"])
        total_outstanding = total_revenue - total_paid

        context["total_revenue"] = total_revenue
        context["total_paid"] = total_paid
        context["total_outstanding"] = total_outstanding

        return context


class InvoiceCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "billing/invoice_form.html"
    success_url = reverse_lazy("billing:invoice_list")

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
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context["items_formset"]

        form.instance.invoice_number = Invoice.generate_invoice_number()
        form.instance.created_by = self.request.user
        clinic = getattr(self.request.user, "clinic", None)
        form.instance.clinic = clinic

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
