from django.urls import path
from . import views

app_name = "treatments"

urlpatterns = [
    path("", views.TreatmentListView.as_view(), name="treatment_list"),
    path("create/", views.TreatmentCreateView.as_view(), name="treatment_create"),
    path("<int:pk>/", views.TreatmentDetailView.as_view(), name="treatment_detail"),
    path(
        "<int:pk>/update/", views.TreatmentUpdateView.as_view(), name="treatment_update"
    ),
    path(
        "<int:pk>/delete/", views.TreatmentDeleteView.as_view(), name="treatment_delete"
    ),
    path("templates/", views.TreatmentTemplateListView.as_view(), name="template_list"),
    path(
        "templates/create/",
        views.TreatmentTemplateCreateView.as_view(),
        name="template_create",
    ),
    path(
        "templates/<int:pk>/update/",
        views.TreatmentTemplateUpdateView.as_view(),
        name="template_update",
    ),
]
