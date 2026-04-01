from rest_framework import viewsets, permissions, filters
from .models import Invoice, Payment
from .serializers import InvoiceSerializer, PaymentSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["invoice_number", "patient__first_name", "patient__last_name"]
    ordering_fields = ["issue_date", "total_amount", "created_at"]
    ordering = ["-created_at"]


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["invoice__invoice_number", "invoice__patient__first_name"]
    ordering_fields = ["payment_date", "amount", "created_at"]
    ordering = ["-payment_date"]
