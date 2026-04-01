from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path(
        "create-checkout-session/",
        views.create_checkout_session,
        name="create_checkout",
    ),
    path("create-payment/", views.create_one_time_payment, name="create_payment"),
    path("webhook/", views.stripe_webhook, name="webhook"),
    path("history/", views.get_payment_history, name="history"),
    path("cancel/", views.cancel_subscription, name="cancel"),
]
