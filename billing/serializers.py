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
    patient_id = serializers.IntegerField(write_only=True, required=False)
    treatment_id = serializers.IntegerField(write_only=True, required=False)
    balance_due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    remaining_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    paid_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "patient",
            "patient_id",
            "treatment",
            "treatment_id",
            "created_by",
            "issue_date",
            "due_date",
            "subtotal",
            "tax_amount",
            "discount_amount",
            "total_amount",
            "amount_paid",
            "remaining_amount",
            "balance_due",
            "paid_percentage",
            "status",
            "notes",
            "items",
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "invoice_number",
            "created_at",
            "updated_at",
            "remaining_amount",
        ]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField()
    treatment_id = serializers.IntegerField(required=False, allow_null=True)
    items = InvoiceItemSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = [
            "patient_id",
            "treatment_id",
            "issue_date",
            "due_date",
            "tax_amount",
            "discount_amount",
            "notes",
            "status",
            "items",
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        patient_id = validated_data.pop("patient_id")
        treatment_id = validated_data.pop("treatment_id", None)

        from patients.models import Patient
        from treatments.models import Treatment

        patient = Patient.objects.get(pk=patient_id)
        validated_data["patient"] = patient
        validated_data["invoice_number"] = Invoice.generate_invoice_number()
        validated_data["created_by"] = self.context["request"].user
        clinic = getattr(self.context["request"].user, "clinic", None)
        validated_data["clinic"] = clinic

        if treatment_id:
            try:
                validated_data["treatment"] = Treatment.objects.get(pk=treatment_id)
            except Treatment.DoesNotExist:
                pass

        subtotal = 0
        for item_data in items_data:
            subtotal += item_data.get("quantity", 1) * item_data.get("unit_price", 0)

        tax_amount = float(validated_data.get("tax_amount", 0) or 0)
        discount_amount = float(validated_data.get("discount_amount", 0) or 0)
        validated_data["subtotal"] = subtotal
        validated_data["total_amount"] = subtotal + tax_amount - discount_amount
        validated_data["amount_paid"] = 0

        invoice = Invoice.objects.create(**validated_data)

        for item_data in items_data:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=item_data["description"],
                quantity=item_data.get("quantity", 1),
                unit_price=item_data["unit_price"],
            )

        return invoice


class AddPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_date = serializers.DateField()
    payment_method = serializers.CharField()
    reference_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_payment_method(self, value):
        valid_methods = [method[0] for method in Payment.PaymentMethod.choices]
        if value not in valid_methods:
            raise serializers.ValidationError(
                f"Invalid payment method. Must be one of: {valid_methods}"
            )
        return value
