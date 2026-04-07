from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Patient, PatientDocument
from .serializers import PatientSerializer, PatientDocumentSerializer


class ClinicFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        clinic = getattr(self.request.user, "clinic", None)
        if clinic and not self.request.user.is_superuser:
            queryset = queryset.filter(clinic=clinic)
        return queryset


class PatientViewSet(ClinicFilterMixin, viewsets.ModelViewSet):
    queryset = Patient.objects.filter(is_active=True)
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["first_name", "last_name", "phone", "email"]
    ordering_fields = ["created_at", "first_name", "last_name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return super().get_queryset()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class PatientDocumentViewSet(ClinicFilterMixin, viewsets.ModelViewSet):
    queryset = PatientDocument.objects.all()
    serializer_class = PatientDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset()
