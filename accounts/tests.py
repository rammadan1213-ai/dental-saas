from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import User

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="receptionist",
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, "receptionist")
        self.assertTrue(user.is_active)

    def test_create_admin_user(self):
        user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            role="admin",
        )
        self.assertTrue(user.is_admin_user)
        self.assertTrue(user.is_staff)

    def test_create_dentist_user(self):
        user = User.objects.create_user(
            username="dentist",
            email="dentist@example.com",
            password="dentistpass123",
            role="dentist",
            specialty="General Dentistry",
        )
        self.assertTrue(user.is_dentist)
        self.assertEqual(user.specialty, "General Dentistry")


class AuthenticationTest(TestCase):
    def test_login_view(self):
        User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="receptionist",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
