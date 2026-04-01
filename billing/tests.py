from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Invoice, Payment
from patients.models import Patient

User = get_user_model()


class InvoiceModelTest(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Test",
            last_name="Patient",
            email="patient@test.com",
            phone="555-0100",
            date_of_birth="1990-01-01",
            gender="male",
        )
        self.invoice = Invoice.objects.create(
            patient=self.patient,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            total_amount=500.00,
            amount_paid=200.00,
            status="partial",
        )

    def test_invoice_creation(self):
        self.assertIsNotNone(self.invoice.invoice_number)
        self.assertEqual(self.invoice.patient, self.patient)
        self.assertEqual(self.invoice.status, "partial")

    def test_balance_due(self):
        self.assertEqual(self.invoice.balance_due, 300.00)

    def test_generate_invoice_number(self):
        new_number = Invoice.generate_invoice_number()
        self.assertIsNotNone(new_number)
        self.assertTrue(new_number.startswith("INV-"))


class PaymentModelTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            role="admin",
        )
        self.patient = Patient.objects.create(
            first_name="Test",
            last_name="Patient",
            email="patient@test.com",
            phone="555-0100",
            date_of_birth="1990-01-01",
            gender="male",
        )
        self.invoice = Invoice.objects.create(
            patient=self.patient,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            total_amount=500.00,
            amount_paid=0.00,
            status="sent",
        )
        self.payment = Payment.objects.create(
            invoice=self.invoice,
            amount=200.00,
            payment_date=timezone.now().date(),
            payment_method="cash",
            recorded_by=self.admin_user,
        )

    def test_payment_creation(self):
        self.assertEqual(self.payment.amount, 200.00)
        self.assertEqual(self.payment.invoice, self.invoice)

    def test_invoice_status_update_on_payment(self):
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, 200.00)
        self.assertEqual(self.invoice.status, "partial")
