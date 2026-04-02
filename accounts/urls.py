from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/update/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path(
        "users/<int:pk>/password/",
        views.UserPasswordChangeView.as_view(),
        name="user_password_change",
    ),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path(
        "clinic/settings/", views.ClinicSettingsView.as_view(), name="clinic_settings"
    ),
    path(
        "password-reset/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        views.CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("audit-logs/", views.AuditLogListView.as_view(), name="audit_log_list"),
    path(
        "admin/dashboard/",
        views.SuperAdminDashboardView.as_view(),
        name="superadmin_dashboard",
    ),
    path(
        "admin/clinic/<int:pk>/", views.ClinicDetailView.as_view(), name="clinic_detail"
    ),
    path(
        "admin/toggle-clinic/<int:clinic_id>/",
        views.toggle_clinic_status,
        name="toggle_clinic",
    ),
    path(
        "admin/update-subscription/<int:clinic_id>/",
        views.update_clinic_subscription,
        name="update_subscription",
    ),
    path(
        "switch-to-clinic/",
        views.SwitchToClinicView.as_view(),
        name="switch_to_clinic",
    ),
]
