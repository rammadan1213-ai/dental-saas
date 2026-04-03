from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, Payment


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "patient",
            "treatment",
            "issue_date",
            "due_date",
            "tax_amount",
            "discount_amount",
            "notes",
            "status",
        ]
        widgets = {
            "patient": forms.Select(attrs={"class": "form-control"}),
            "treatment": forms.Select(attrs={"class": "form-control"}),
            "issue_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "due_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "tax_amount": forms.NumberInput(attrs={"class": "form-control"}),
            "discount_amount": forms.NumberInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["description", "quantity", "unit_price"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "unit_price": forms.NumberInput(attrs={"class": "form-control"}),
        }


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm, extra=1, can_delete=True
)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            "amount",
            "payment_date",
            "payment_method",
            "reference_number",
            "notes",
        ]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "payment_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "payment_method": forms.Select(attrs={"class": "form-control"}),
            "reference_number": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class InvoiceFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[("", "All Status")] + list(Invoice.Status.choices),
        required=False,
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
