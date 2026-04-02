from django.urls import path
from . import views

urlpatterns = [
    path("setup/", views.setup_view, name="setup"),
]
