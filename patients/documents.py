from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from patients.models import Patient


@registry.register_document
class PatientDocument(Document):
    id = fields.IntegerField(attr="id")
    first_name = fields.TextField(
        attr="first_name", fields={"raw": fields.KeywordField()}
    )
    last_name = fields.TextField(
        attr="last_name", fields={"raw": fields.KeywordField()}
    )
    full_name = fields.TextField(
        attr="full_name", fields={"raw": fields.KeywordField()}
    )
    phone = fields.TextField(attr="phone", fields={"raw": fields.KeywordField()})
    email = fields.TextField(attr="email", fields={"raw": fields.KeywordField()})
    gender = fields.KeywordField(attr="gender")
    is_active = fields.BooleanField(attr="is_active")
    clinic_id = fields.IntegerField(attr="clinic_id")

    class Index:
        name = "patients"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Patient
        fields = []

    def get_queryset(self):
        return super().get_queryset().select_related("clinic")

    def prepare_clinic_id(self, instance):
        return instance.clinic_id if instance.clinic else None
