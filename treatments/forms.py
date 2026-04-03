from django import forms
from .models import Treatment, DentalService
from accounts.models import User


class TreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = [
            "patient",
            "appointment",
            "dental_service",
            "dentist",
            "diagnosis",
            "procedure",
            "tooth_number",
            "anesthesia_used",
            "status",
            "cost",
            "notes",
            "treatment_date",
        ]
        widgets = {
            "patient": forms.Select(attrs={"class": "form-control"}),
            "appointment": forms.Select(attrs={"class": "form-control"}),
            "dental_service": forms.Select(attrs={"class": "form-control"}),
            "dentist": forms.Select(attrs={"class": "form-control"}),
            "diagnosis": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "procedure": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "tooth_number": forms.TextInput(attrs={"class": "form-control"}),
            "anesthesia_used": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "cost": forms.NumberInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "treatment_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["dentist"].queryset = User.objects.filter(
            role=User.Role.DENTIST, is_active=True
        )
        self.fields["dental_service"].queryset = DentalService.objects.filter(
            is_active=True
        )
        self.fields["dental_service"].required = False

    def clean(self):
        cleaned_data = super().clean()
        dental_service = cleaned_data.get("dental_service")
        if dental_service and not cleaned_data.get("cost"):
            cleaned_data["cost"] = dental_service.default_price
        return cleaned_data


class TreatmentFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[("", "All Status")] + list(Treatment.Status.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    dentist = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.DENTIST, is_active=True),
        required=False,
        empty_label="All Dentists",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
