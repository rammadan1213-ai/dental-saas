from django import forms
from .models import Treatment, TreatmentTemplate
from accounts.models import User


class TreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = [
            "patient",
            "appointment",
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


class TreatmentTemplateForm(forms.ModelForm):
    class Meta:
        model = TreatmentTemplate
        fields = ["name", "description", "default_cost", "category", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "default_cost": forms.NumberInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


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
