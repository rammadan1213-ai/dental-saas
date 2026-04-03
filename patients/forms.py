from django import forms
from .models import Patient, PatientDocument


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "age",
            "gender",
            "blood_type",
            "allergies",
            "medical_history",
            "medications",
            "emergency_contact",
            "emergency_phone",
            "notes",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "age": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "max": "150"}
            ),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "blood_type": forms.TextInput(attrs={"class": "form-control"}),
            "allergies": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "medical_history": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "medications": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "emergency_contact": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_phone": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class PatientDocumentForm(forms.ModelForm):
    class Meta:
        model = PatientDocument
        fields = ["document_type", "title", "file", "description"]
        widgets = {
            "document_type": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class PatientSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search by name, phone, or email...",
            }
        ),
    )
    gender = forms.ChoiceField(
        choices=[("", "All Genders")] + Patient.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
