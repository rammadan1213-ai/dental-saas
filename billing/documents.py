from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from billing.models import Invoice


@registry.register_document
class InvoiceDocument(Document):
    id = fields.IntegerField(attr="id")
    invoice_number = fields.TextField(
        attr="invoice_number", fields={"raw": fields.KeywordField()}
    )
    status = fields.KeywordField(attr="status")
    total_amount = fields.FloatField(attr="total_amount")
    amount_paid = fields.FloatField(attr="amount_paid")
    patient_name = fields.TextField(attr="patient_name")
    clinic_id = fields.IntegerField(attr="clinic_id")

    class Index:
        name = "invoices"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Invoice
        fields = []

    def get_queryset(self):
        return super().get_queryset().select_related("patient", "clinic")

    def prepare_patient_name(self, instance):
        return instance.patient.full_name if instance.patient else None

    def prepare_clinic_id(self, instance):
        return instance.clinic_id if instance.clinic else None
