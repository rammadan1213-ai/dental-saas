from rest_framework import serializers
from .models import Patient, PatientDocument


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "date_of_birth",
            "gender",
            "blood_type",
            "allergies",
            "medical_history",
            "medications",
            "emergency_contact",
            "emergency_phone",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PatientDocumentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)

    class Meta:
        model = PatientDocument
        fields = [
            "id",
            "patient",
            "document_type",
            "title",
            "file",
            "description",
            "created_at",
        ]
        read_only_fields = ["created_at"]
