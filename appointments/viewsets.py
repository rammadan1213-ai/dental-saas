from rest_framework import viewsets, permissions, filters
from .models import Appointment
from .serializers import AppointmentSerializer


class ClinicFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        clinic = getattr(self.request.user, "clinic", None)
        if clinic and not self.request.user.is_superuser:
            queryset = queryset.filter(clinic=clinic)
        return queryset


class AppointmentViewSet(ClinicFilterMixin, viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["patient__first_name", "patient__last_name", "reason"]
    ordering_fields = ["date", "start_time", "created_at"]
    ordering = ["-date", "-start_time"]

    def get_queryset(self):
        return super().get_queryset()
