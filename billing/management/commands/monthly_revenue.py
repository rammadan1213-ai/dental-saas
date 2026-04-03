from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
from billing.models import Invoice, Payment


class Command(BaseCommand):
    help = "Generate monthly revenue report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=int,
            help="Month number (1-12). Default: current month",
        )
        parser.add_argument(
            "--year",
            type=int,
            help="Year. Default: current year",
        )
        parser.add_argument(
            "--clinic",
            type=int,
            help="Clinic ID. Default: all clinics",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        month = options.get("month") or now.month
        year = options.get("year") or now.year

        start_date = timezone.datetime(year, month, 1)
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1)
        else:
            end_date = timezone.datetime(year, month + 1, 1)

        invoices = Invoice.objects.filter(
            issue_date__gte=start_date.date(), issue_date__lt=end_date.date()
        )

        clinic_id = options.get("clinic")
        if clinic_id:
            invoices = invoices.filter(clinic_id=clinic_id)

        total_invoiced = (
            invoices.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        )
        total_paid = invoices.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        total_outstanding = float(total_invoiced) - float(total_paid)

        payments = Payment.objects.filter(
            payment_date__gte=start_date.date(), payment_date__lt=end_date.date()
        )
        if clinic_id:
            payments = payments.filter(clinic_id=clinic_id)

        payments_by_method = payments.values("payment_method").annotate(
            total=Sum("amount"), count=Count("id")
        )

        invoices_by_status = invoices.values("status").annotate(
            count=Count("id"), total=Sum("total_amount")
        )

        self.stdout.write(
            self.style.NOTES(
                f"\n=== Revenue Report: {start_date.strftime('%B %Y')} ===\n"
            )
        )

        self.stdout.write(self.style.NOTES("SUMMARY:"))
        self.stdout.write(f"  Total Invoiced:    ${total_invoiced}")
        self.stdout.write(f"  Total Paid:        ${total_paid}")
        self.stdout.write(f"  Outstanding:       ${total_outstanding}")
        self.stdout.write(f"  Total Invoices:    {invoices.count()}\n")

        self.stdout.write(self.style.NOTES("BY STATUS:"))
        for item in invoices_by_status:
            self.stdout.write(
                f"  {item['status']}: {item['count']} invoices (${item['total']})"
            )

        self.stdout.write(self.style.NOTES("\nPAYMENTS BY METHOD:"))
        for item in payments_by_method:
            method_name = dict(Payment.PaymentMethod.choices).get(
                item["payment_method"], item["payment_method"]
            )
            self.stdout.write(
                f"  {method_name}: {item['count']} payments (${item['total']})"
            )

        self.stdout.write(self.style.SUCCESS("\nReport generated successfully!\n"))
