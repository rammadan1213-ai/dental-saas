from rest_framework import serializers
from .models import Treatment
from patients.serializers import PatientSerializer
from accounts.serializers import UserSerializer


class TreatmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = UserSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    dentist_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Treatment
        fields = [
            "id",
            "patient",
            "patient_id",
            "dentist",
            "dentist_id",
            "diagnosis",
            "procedure",
            "tooth_number",
            "anesthesia_used",
            "status",
            "cost",
            "notes",
            "treatment_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
