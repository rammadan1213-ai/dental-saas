from django import forms
from django.utils import timezone
from .models import Appointment
from accounts.models import User


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            "patient",
            "dentist",
            "date",
            "start_time",
            "end_time",
            "status",
            "priority",
            "reason",
            "notes",
        ]
        widgets = {
            "patient": forms.Select(attrs={"class": "form-control"}),
            "dentist": forms.Select(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "start_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "end_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["dentist"].queryset = User.objects.filter(
            role=User.Role.DENTIST, is_active=True
        )


class AppointmentFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[("", "All Status")] + list(Appointment.Status.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    priority = forms.ChoiceField(
        choices=[("", "All Priority")] + list(Appointment.Priority.choices),
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
