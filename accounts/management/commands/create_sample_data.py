from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from accounts.models import User
from patients.models import Patient
from appointments.models import Appointment
from treatments.models import Treatment
from billing.models import Invoice, InvoiceItem, Payment
from clinics.models import Clinic, Subscription


class Command(BaseCommand):
    help = "Creates sample data for the dental clinic"

    def handle(self, *args, **options):
        self.stdout.write("Creating sample data...")

        admin_user = User.objects.create_user(
            username="admin",
            email="admin@dentalclinic.com",
            password="admin123",
            first_name="Admin",
            last_name="User",
            role="admin",
        )
        self.stdout.write(f"Created admin user: {admin_user.username}")

        clinic = Clinic.objects.create(
            name="Smile Dental Clinic",
            address="123 Main Street, City, State 12345",
            phone="555-123-4567",
            email="info@smiledental.com",
            owner=admin_user,
        )
        self.stdout.write(f"Created clinic: {clinic.name}")

        admin_user.clinic = clinic
        admin_user.save()

        Subscription.objects.create(
            clinic=clinic,
            plan="enterprise",
            is_active=True,
            expiry_date=date.today() + timedelta(days=365),
        )
        self.stdout.write("Created clinic subscription")

        dentist1 = User.objects.create_user(
            username="drsmith",
            email="drsmith@dentalclinic.com",
            password="dentist123",
            first_name="John",
            last_name="Smith",
            role="dentist",
            specialty="General Dentistry",
            clinic=clinic,
        )
        dentist2 = User.objects.create_user(
            username="drjohnson",
            email="drjohnson@dentalclinic.com",
            password="dentist123",
            first_name="Sarah",
            last_name="Johnson",
            role="dentist",
            specialty="Orthodontics",
            clinic=clinic,
        )
        self.stdout.write(f"Created dentist users")

        receptionist = User.objects.create_user(
            username="receptionist",
            email="reception@dentalclinic.com",
            password="reception123",
            first_name="Emily",
            last_name="Brown",
            role="receptionist",
            clinic=clinic,
        )
        self.stdout.write(f"Created receptionist user")

        patients_data = [
            {
                "first_name": "Alice",
                "last_name": "Williams",
                "email": "alice@email.com",
                "phone": "555-0101",
                "gender": "female",
            },
            {
                "first_name": "Bob",
                "last_name": "Davis",
                "email": "bob@email.com",
                "phone": "555-0102",
                "gender": "male",
            },
            {
                "first_name": "Carol",
                "last_name": "Miller",
                "email": "carol@email.com",
                "phone": "555-0103",
                "gender": "female",
            },
            {
                "first_name": "David",
                "last_name": "Wilson",
                "email": "david@email.com",
                "phone": "555-0104",
                "gender": "male",
            },
            {
                "first_name": "Eva",
                "last_name": "Moore",
                "email": "eva@email.com",
                "phone": "555-0105",
                "gender": "female",
            },
        ]

        patients = []
        for i, p_data in enumerate(patients_data):
            dob = timezone.now().date() - timedelta(days=365 * (25 + i * 5))
            patient = Patient.objects.create(
                clinic=clinic,
                **p_data,
                date_of_birth=dob,
                address=f"{i + 1} Main St, City",
                blood_type=["A+", "B+", "O+", "AB+", "A-"][i],
                medical_history="No known conditions",
                allergies="None known",
            )
            patients.append(patient)
        self.stdout.write(f"Created {len(patients)} patients")

        today = timezone.now().date()
        for i, patient in enumerate(patients[:3]):
            Appointment.objects.create(
                clinic=clinic,
                patient=patient,
                dentist=dentist1,
                date=today + timedelta(days=i),
                start_time=timezone.now().time().replace(hour=9 + i * 2, minute=0),
                end_time=timezone.now().time().replace(hour=10 + i * 2, minute=0),
                status=["pending", "confirmed", "completed"][i],
                reason=f"Routine checkup for {patient.full_name}",
            )
        self.stdout.write("Created sample appointments")

        for i, patient in enumerate(patients[:3]):
            Treatment.objects.create(
                clinic=clinic,
                patient=patient,
                dentist=dentist1,
                diagnosis=f"Dental examination - Patient {i + 1}",
                procedure=f"Cleaning and polishing - Treatment {i + 1}",
                status="completed",
                cost=150.00 + (i * 50),
                treatment_date=today - timedelta(days=i * 7),
            )
        self.stdout.write("Created sample treatments")

        for i, patient in enumerate(patients[:3]):
            invoice = Invoice.objects.create(
                clinic=clinic,
                patient=patient,
                invoice_number=Invoice.generate_invoice_number(),
                created_by=receptionist,
                issue_date=today - timedelta(days=i * 7),
                due_date=today + timedelta(days=30),
                subtotal=200.00 + (i * 100),
                tax_amount=20.00 + (i * 10),
                discount_amount=0,
                total_amount=220.00 + (i * 110),
                amount_paid=100.00 + (i * 50),
                status=["paid", "partial", "sent"][i],
            )

            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"Dental procedure - {patient.full_name}",
                quantity=1,
                unit_price=200.00 + (i * 100),
                total_price=200.00 + (i * 100),
            )

            if i < 2:
                Payment.objects.create(
                    clinic=clinic,
                    invoice=invoice,
                    amount=100.00 + (i * 50),
                    payment_date=today - timedelta(days=i * 3),
                    payment_method="cash",
                    recorded_by=receptionist,
                )
        self.stdout.write("Created sample invoices and payments")

        self.stdout.write(self.style.SUCCESS("Sample data created successfully!"))
        self.stdout.write("\nLogin credentials:")
        self.stdout.write("Admin: admin / admin123")
        self.stdout.write("Dentist: drsmith / dentist123")
        self.stdout.write("Receptionist: receptionist / reception123")
