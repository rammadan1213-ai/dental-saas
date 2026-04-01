from django.urls import path
from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.AppointmentListView.as_view(), name="appointment_list"),
    path("create/", views.AppointmentCreateView.as_view(), name="appointment_create"),
    path("<int:pk>/", views.AppointmentDetailView.as_view(), name="appointment_detail"),
    path(
        "<int:pk>/update/",
        views.AppointmentUpdateView.as_view(),
        name="appointment_update",
    ),
    path(
        "<int:pk>/delete/",
        views.AppointmentDeleteView.as_view(),
        name="appointment_delete",
    ),
    path(
        "calendar/",
        views.AppointmentCalendarView.as_view(),
        name="appointment_calendar",
    ),
    path(
        "<int:pk>/update-status/", views.update_appointment_status, name="update_status"
    ),
    path("api/appointments/", views.get_appointments_json, name="appointments_json"),
]
