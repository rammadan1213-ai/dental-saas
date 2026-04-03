from django.db import models
from django.db.models import Sum
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
    treatment = models.ForeignKey(
        "treatments.Treatment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
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
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    notes = models.TextField(blank=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    stripe_invoice_id = models.CharField(max_length=255, blank=True)
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
        total = float(self.total_amount or 0)
        paid = float(self.amount_paid or 0)
        return max(0, total - paid)

    @property
    def remaining_amount_prop(self):
        return self.balance_due

    @property
    def is_fully_paid(self):
        return float(self.amount_paid or 0) >= float(self.total_amount or 0)

    @property
    def payment_status(self):
        paid = float(self.amount_paid or 0)
        total = float(self.total_amount or 0)
        if paid >= total:
            return "paid"
        elif paid > 0:
            return "partial"
        return self.status

    @property
    def paid_percentage(self):
        total = float(self.total_amount or 0)
        if total == 0:
            return 0
        return min(100, (float(self.amount_paid or 0) / total) * 100)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = Invoice.generate_invoice_number()
        self.remaining_amount = self.balance_due
        super().save(*args, **kwargs)

    @classmethod
    def generate_invoice_number(cls):
        from django.utils import timezone

        today = timezone.now().date()
        prefix = f"INV-{today.strftime('%Y%m%d')}"
        last_invoice = (
            cls.objects.filter(invoice_number__startswith=prefix)
            .order_by("-invoice_number")
            .first()
        )
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}-{new_num:04d}"


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
        DEBIT_CARD = "debit_card", _("Debit Card")
        BANK_TRANSFER = "bank_transfer", _("Bank Transfer")
        ZAAD = "zaad", _("Zaad (Somali Mobile Money)")
        EDAHAB = "edahab", _("E-Dahab (Somali Mobile Money)")
        SAHAL = "sahal", _("Sahal (Somali Mobile Money)")
        INSURANCE = "insurance", _("Insurance")
        COMPANY = "company", _("Company/Employer")
        INSTALLMENT = "installment", _("Payment Plan/Installment")
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
        from django.db import transaction

        with transaction.atomic():
            invoice = Invoice.objects.select_for_update().get(pk=self.invoice.pk)
            total_paid = sum(p.amount for p in invoice.payments.all())
            invoice.amount_paid = total_paid

            if total_paid >= float(invoice.total_amount or 0):
                invoice.status = Invoice.Status.PAID
            elif total_paid > 0:
                invoice.status = Invoice.Status.PARTIAL
            else:
                invoice.status = Invoice.Status.SENT

            invoice.save(update_fields=["amount_paid", "status", "updated_at"])
