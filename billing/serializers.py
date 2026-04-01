from rest_framework import serializers
from .models import Invoice, InvoiceItem, Payment
from patients.serializers import PatientSerializer
from accounts.serializers import UserSerializer


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ["id", "description", "quantity", "unit_price", "total_price"]


class PaymentSerializer(serializers.ModelSerializer):
    recorded_by = UserSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "invoice",
            "amount",
            "payment_date",
            "payment_method",
            "reference_number",
            "notes",
            "recorded_by",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    patient_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "patient",
            "patient_id",
            "created_by",
            "issue_date",
            "due_date",
            "subtotal",
            "tax_amount",
            "discount_amount",
            "total_amount",
            "amount_paid",
            "status",
            "notes",
            "items",
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["invoice_number", "created_at", "updated_at"]
