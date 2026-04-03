from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="home"),
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    path("reports/", views.ReportView.as_view(), name="reports"),
    path("insights/", views.smart_insights, name="insights"),
    path("api/stats/", views.get_dashboard_stats, name="dashboard_stats"),
]
