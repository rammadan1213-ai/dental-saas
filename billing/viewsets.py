from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
import csv
from django.http import HttpResponse

from .models import Invoice, Payment
from .serializers import (
    InvoiceSerializer,
    InvoiceCreateSerializer,
    PaymentSerializer,
    AddPaymentSerializer,
)


class ClinicFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        clinic = getattr(self.request.user, "clinic", None)
        if clinic and not self.request.user.is_superuser:
            queryset = queryset.filter(clinic=clinic)
        return queryset


class InvoiceViewSet(ClinicFilterMixin, viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        filters.BaseFilterBackend,
    ]
    search_fields = [
        "invoice_number",
        "patient__first_name",
        "patient__last_name",
        "patient__phone",
    ]
    ordering_fields = ["issue_date", "total_amount", "created_at", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return InvoiceCreateSerializer
        return InvoiceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        status_filter = self.request.query_params.get("status")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        patient_id = self.request.query_params.get("patient")

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset.select_related("patient", "created_by", "treatment")

    @action(detail=True, methods=["post"])
    def add_payment(self, request, pk=None):
        invoice = self.get_object()
        serializer = AddPaymentSerializer(data=request.data)

        if serializer.is_valid():
            payment = Payment.objects.create(
                invoice=invoice,
                amount=serializer.validated_data["amount"],
                payment_date=serializer.validated_data["payment_date"],
                payment_method=serializer.validated_data["payment_method"],
                reference_number=serializer.validated_data.get("reference_number", ""),
                notes=serializer.validated_data.get("notes", ""),
                recorded_by=request.user,
                clinic=invoice.clinic,
            )
            return Response(
                PaymentSerializer(payment).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        queryset = self.get_queryset()

        total_invoiced = (
            queryset.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        )
        total_paid = queryset.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        total_pending = total_invoiced - total_paid

        by_status = queryset.values("status").annotate(
            count=Count("id"), total=Sum("total_amount")
        )

        by_method = (
            Payment.objects.filter(invoice__in=queryset)
            .values("payment_method")
            .annotate(total=Sum("amount"), count=Count("id"))
        )

        return Response(
            {
                "total_invoiced": float(total_invoiced),
                "total_paid": float(total_paid),
                "total_pending": float(total_pending),
                "by_status": list(by_status),
                "by_payment_method": list(by_method),
            }
        )

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        queryset = self.get_queryset()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="invoices.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Invoice Number",
                "Patient",
                "Issue Date",
                "Due Date",
                "Total Amount",
                "Amount Paid",
                "Remaining",
                "Status",
            ]
        )

        for invoice in queryset:
            writer.writerow(
                [
                    invoice.invoice_number,
                    invoice.patient.full_name,
                    invoice.issue_date,
                    invoice.due_date,
                    float(invoice.total_amount),
                    float(invoice.amount_paid),
                    float(invoice.remaining_amount),
                    invoice.status,
                ]
            )

        return response

    @action(detail=True, methods=["get"])
    def print_invoice(self, request, pk=None):
        invoice = self.get_object()
        from django.shortcuts import render

        return render(request, "billing/invoice_print.html", {"invoice": invoice})


class PaymentViewSet(ClinicFilterMixin, viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "invoice__invoice_number",
        "invoice__patient__first_name",
        "invoice__patient__last_name",
    ]
    ordering_fields = ["payment_date", "amount", "created_at"]
    ordering = ["-payment_date"]

    def get_queryset(self):
        queryset = super().get_queryset()

        invoice_id = self.request.query_params.get("invoice")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        method = self.request.query_params.get("payment_method")

        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)
        if method:
            queryset = queryset.filter(payment_method=method)

        return queryset.select_related("invoice", "invoice__patient", "recorded_by")
