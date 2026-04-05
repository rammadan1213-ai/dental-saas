from django.urls import path
from . import views

app_name = "patients"

urlpatterns = [
    path("", views.PatientListView.as_view(), name="patient_list"),
    path("create/", views.PatientCreateView.as_view(), name="patient_create"),
    path("<int:pk>/", views.PatientDetailView.as_view(), name="patient_detail"),
    path("<int:pk>/update/", views.PatientUpdateView.as_view(), name="patient_update"),
    path("<int:pk>/delete/", views.PatientDeleteView.as_view(), name="patient_delete"),
    path(
        "<int:pk>/documents/upload/",
        views.PatientDocumentUploadView.as_view(),
        name="document_upload",
    ),
    path("api/search/", views.get_patients_json, name="patient_search_api"),
    path("api/search/", views.get_patients_json, name="patient_search"),
]
