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
    path("services/", views.DentalServiceListView.as_view(), name="service_list"),
    path(
        "services/create/",
        views.DentalServiceCreateView.as_view(),
        name="service_create",
    ),
    path(
        "services/<int:pk>/update/",
        views.DentalServiceUpdateView.as_view(),
        name="service_update",
    ),
    path(
        "services/<int:pk>/delete/",
        views.DentalServiceDeleteView.as_view(),
        name="service_delete",
    ),
]
