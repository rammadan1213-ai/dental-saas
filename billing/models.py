from django.db import models
from django.utils.translation import gettext_lazy as _
from patients.models import Patient
from accounts.models import User


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SENT = "sent", _("Sent")
        PAID = "paid", _("Paid")
        PARTIAL = "partial", _("Partial")
        OVERDUE = "overdue", _("Overdue")
        CANCELLED = "cancelled", _("Cancelled")

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="invoices",
        null=True,
        blank=True,
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="invoices"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_invoices"
    )
    issue_date = models.DateField()
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.patient.full_name}"

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    @property
    def is_fully_paid(self):
        return self.amount_paid >= self.total_amount

    @classmethod
    def generate_invoice_number(cls):
        last_invoice = cls.objects.order_by("-created_at").first()
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split("-")[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"INV-{new_number:06d}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=500)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")

    def __str__(self):
        return f"{self.description} - {self.total_price}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", _("Cash")
        CREDIT_CARD = "credit_card", _("Credit Card")
        DEBIT_CARD = "debit_card", _("Debit Transfer")
        BANK_TRANSFER = "bank_transfer", _("Bank Transfer")
        INSURANCE = "insurance", _("Insurance")
        OTHER = "other", _("Other")

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="recorded_payments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date"]
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_invoice_amount_paid()

    def update_invoice_amount_paid(self):
        invoice = self.invoice
        total_paid = sum(p.amount for p in invoice.payments.all())
        invoice.amount_paid = total_paid
        if total_paid >= invoice.total_amount:
            invoice.status = Invoice.Status.PAID
        elif total_paid > 0:
            invoice.status = Invoice.Status.PARTIAL
        invoice.save()
