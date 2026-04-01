import pytest
from django.conf import settings
from accounts.models import User
from patients.models import Patient


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", email="admin@test.com", password="testpass123", role="admin"
    )


@pytest.fixture
def dentist_user(db):
    return User.objects.create_user(
        username="dentist",
        email="dentist@test.com",
        password="testpass123",
        role="dentist",
    )


@pytest.fixture
def patient(db):
    return Patient.objects.create(
        first_name="Test",
        last_name="Patient",
        email="patient@test.com",
        phone="555-0100",
        date_of_birth="1990-01-01",
        gender="male",
    )
