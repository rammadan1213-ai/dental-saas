from django.urls import path
from . import views

app_name = "clinics"

urlpatterns = [
    path("pricing/", views.PricingView.as_view(), name="pricing"),
    path(
        "expired/", views.SubscriptionExpiredView.as_view(), name="subscription_expired"
    ),
    path("manage/", views.SubscriptionManageView.as_view(), name="subscription_manage"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("api/create-checkout/", views.api_create_checkout, name="api_checkout"),
]
