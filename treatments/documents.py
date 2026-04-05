from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from treatments.models import Treatment


@registry.register_document
class TreatmentDocument(Document):
    id = fields.IntegerField(attr="id")
    procedure = fields.TextField(
        attr="procedure", fields={"raw": fields.KeywordField()}
    )
    diagnosis = fields.TextField(
        attr="diagnosis", fields={"raw": fields.KeywordField()}
    )
    status = fields.KeywordField(attr="status")
    cost = fields.FloatField(attr="cost")
    patient_name = fields.TextField(attr="patient_name")
    clinic_id = fields.IntegerField(attr="clinic_id")

    class Index:
        name = "treatments"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Treatment
        fields = []

    def get_queryset(self):
        return super().get_queryset().select_related("patient", "clinic")

    def prepare_patient_name(self, instance):
        return instance.patient.full_name if instance.patient else None

    def prepare_clinic_id(self, instance):
        return instance.clinic_id if instance.clinic else None
