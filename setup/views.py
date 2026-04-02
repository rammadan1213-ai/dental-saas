from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date, timedelta
from accounts.models import User
from clinics.models import Clinic, Subscription
from patients.models import Patient
from appointments.models import Appointment
from treatments.models import Treatment
from billing.models import Invoice, Payment
from django.utils import timezone


def setup_view(request):
    """One-time setup to create initial admin user"""

    if request.method == "POST":
        clinic_name = request.POST.get("clinic_name", "Demo Dental Clinic")
        admin_username = request.POST.get("username", "admin")
        admin_email = request.POST.get("email", "admin@demo.com")
        admin_password = request.POST.get("password", "admin123")

        # Check if user already exists
        if User.objects.filter(username=admin_username).exists():
            messages.warning(request, "Admin user already exists. Please login.")
            return redirect("accounts:login")

        # Create clinic
        clinic = Clinic.objects.create(name=clinic_name, owner=None)

        # Create admin user with superuser=True
        admin = User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name="Admin",
            role="admin",
            is_staff=True,
            is_superuser=True,
            clinic=clinic,
        )

        # Link clinic owner
        clinic.owner = admin
        clinic.save()

        # Create subscription
        Subscription.objects.create(
            clinic=clinic,
            plan="enterprise",
            is_active=True,
            expiry_date=date.today() + timedelta(days=365),
        )

        # Create sample data
        create_sample_data(clinic, admin)

        messages.success(
            request, f"Setup complete! Login with: {admin_username} / {admin_password}"
        )
        return redirect("accounts:login")

    return render(request, "setup/setup.html")


def create_superadmin(request):
    """Create super admin user (bypasses existing user check)"""

    if request.method == "POST":
        username = request.POST.get("username", "eng.abdulrahem")
        email = request.POST.get("email", "eng.abdulrahem@example.com")
        password = request.POST.get("password", "hagaag13")
        clinic_name = request.POST.get("clinic_name", "Main Dental Clinic")

        # Create clinic
        clinic = Clinic.objects.create(name=clinic_name, owner=None)

        # Create super admin
        admin = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name="Abdulrahem",
            last_name="Engineer",
            role="admin",
            is_staff=True,
            is_superuser=True,
            clinic=clinic,
        )

        clinic.owner = admin
        clinic.save()

        # Add enterprise subscription
        Subscription.objects.create(
            clinic=clinic,
            plan="enterprise",
            is_active=True,
            expiry_date=date.today() + timedelta(days=365),
        )

        messages.success(
            request, f"Super admin created! Login with: {username} / {password}"
        )
        return redirect("accounts:login")

    return render(request, "setup/create_superadmin.html")


def quick_create_superadmin(request):
    """Quick create super admin without form"""
    username = "eng.abdulrahem"
    password = "hagaag13"

    if User.objects.filter(username=username).exists():
        messages.info(request, "Super admin already exists!")
    else:
        clinic = Clinic.objects.create(name="Main Dental Clinic", owner=None)

        admin = User.objects.create_user(
            username=username,
            email="eng.abdulrahem@example.com",
            password=password,
            first_name="Abdulrahem",
            last_name="Engineer",
            role="admin",
            is_staff=True,
            is_superuser=True,
            clinic=clinic,
        )

        clinic.owner = admin
        clinic.save()

        Subscription.objects.create(
            clinic=clinic,
            plan="enterprise",
            is_active=True,
            expiry_date=date.today() + timedelta(days=365),
        )

        messages.success(
            request, f"Super admin created! Username: {username}, Password: {password}"
        )

    return redirect("accounts:login")


def create_sample_data(clinic, admin_user):
    """Create sample patients, appointments, etc."""
    from django.utils import timezone
    from datetime import timedelta

    # Create patients
    patients = []
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
    ]

    for p_data in patients_data:
        dob = timezone.now().date() - timedelta(days=365 * 30)
        patient = Patient.objects.create(
            clinic=clinic,
            **p_data,
            date_of_birth=dob,
            address="123 Main St",
            blood_type="A+",
            medical_history="No known conditions",
            allergies="None",
        )
        patients.append(patient)

    # Create dentist
    dentist = User.objects.create_user(
        username="drsmith",
        email="drsmith@clinic.com",
        password="dentist123",
        first_name="John",
        last_name="Smith",
        role="dentist",
        clinic=clinic,
    )

    # Create receptionist
    receptionist = User.objects.create_user(
        username="receptionist",
        email="reception@clinic.com",
        password="reception123",
        first_name="Emily",
        last_name="Brown",
        role="receptionist",
        clinic=clinic,
    )

    today = timezone.now().date()

    # Create appointments
    for i, patient in enumerate(patients[:3]):
        Appointment.objects.create(
            clinic=clinic,
            patient=patient,
            dentist=dentist,
            date=today + timedelta(days=i),
            start_time=timezone.now().time().replace(hour=9 + i * 2, minute=0),
            end_time=timezone.now().time().replace(hour=10 + i * 2, minute=0),
            status=["pending", "confirmed", "completed"][i],
            reason=f"Routine checkup",
        )

    # Create treatments
    for i, patient in enumerate(patients[:3]):
        Treatment.objects.create(
            clinic=clinic,
            patient=patient,
            dentist=dentist,
            diagnosis=f"Examination - Patient {i + 1}",
            procedure=f"Cleaning and polishing",
            status="completed",
            cost=150.00 + (i * 50),
            treatment_date=today - timedelta(days=i * 7),
        )

    # Create invoices
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

        if i < 2:
            Payment.objects.create(
                clinic=clinic,
                invoice=invoice,
                amount=100.00 + (i * 50),
                payment_date=today - timedelta(days=i * 3),
                payment_method="cash",
                recorded_by=receptionist,
            )
