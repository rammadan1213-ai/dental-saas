from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Patient

User = get_user_model()


class PatientModelTest(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="555-0101",
            date_of_birth="1990-01-15",
            gender="male",
        )

    def test_patient_creation(self):
        self.assertEqual(self.patient.full_name, "John Doe")
        self.assertEqual(self.patient.email, "john.doe@example.com")
        self.assertTrue(self.patient.is_active)

    def test_patient_age(self):
        self.assertIsNotNone(self.patient.age)
        self.assertGreater(self.patient.age, 0)


class PatientViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            role="admin",
        )
        self.client.login(username="admin", password="testpass123")

    def test_patient_list_view(self):
        response = self.client.get(reverse("patients:patient_list"))
        self.assertEqual(response.status_code, 200)

    def test_patient_create_view(self):
        response = self.client.get(reverse("patients:patient_create"))
        self.assertEqual(response.status_code, 200)

    def test_patient_create(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "phone": "555-0102",
            "date_of_birth": "1995-05-20",
            "gender": "female",
        }
        response = self.client.post(reverse("patients:patient_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Patient.objects.count(), 1)
