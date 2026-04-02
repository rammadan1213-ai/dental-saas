from django.urls import path
from . import views

urlpatterns = [
    path("setup/", views.setup_view, name="setup"),
    path("create-superadmin/", views.create_superadmin, name="create_superadmin"),
]
