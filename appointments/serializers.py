from rest_framework import serializers
from .models import Appointment
from patients.serializers import PatientSerializer
from accounts.serializers import UserSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = UserSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    dentist_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_id",
            "dentist",
            "dentist_id",
            "date",
            "start_time",
            "end_time",
            "status",
            "priority",
            "reason",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
