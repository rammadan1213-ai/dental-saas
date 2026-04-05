from django.urls import path
from . import views
from . import payment_views

app_name = "billing"

urlpatterns = [
    # Web Views
    path("invoices/", views.InvoiceListView.as_view(), name="invoice_list"),
    path("invoices/create/", views.InvoiceCreateView.as_view(), name="invoice_create"),
    path(
        "invoices/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice_detail"
    ),
    path(
        "invoices/<int:pk>/update/",
        views.InvoiceUpdateView.as_view(),
        name="invoice_update",
    ),
    path(
        "invoices/<int:pk>/delete/",
        views.InvoiceDeleteView.as_view(),
        name="invoice_delete",
    ),
    path("invoices/<int:pk>/pdf/", views.export_invoice_pdf, name="invoice_pdf"),
    path(
        "invoices/<int:pk>/payment/",
        views.PaymentCreateView.as_view(),
        name="payment_create",
    ),
    path("payments/", views.PaymentListView.as_view(), name="payment_list"),
    # Stripe
    path(
        "create-checkout-session/",
        views.create_checkout_session,
        name="create_checkout",
    ),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),
    # Subscription
    path("subscription/", views.subscription_view, name="subscription"),
    path("subscription/cancel/", views.cancel_subscription, name="cancel_subscription"),
    # Create invoice from treatment
    path(
        "invoices/create/from-treatment/<int:patient_id>/<int:treatment_id>/",
        views.create_invoice_from_treatment,
        name="create_invoice_from_treatment",
    ),
    path(
        "invoices/<int:invoice_id>/checkout/",
        views.create_invoice_checkout,
        name="invoice_checkout",
    ),
    # Payment Request (Manual)
    path(
        "payment/request/", payment_views.submit_payment_request, name="payment_request"
    ),
    path(
        "payment/my-requests/",
        payment_views.my_payment_requests,
        name="my_payment_requests",
    ),
    path(
        "admin/payments/",
        payment_views.admin_payment_requests,
        name="admin_payment_requests",
    ),
    path(
        "admin/payment/<int:request_id>/approve/",
        payment_views.approve_payment_request,
        name="approve_payment",
    ),
    path(
        "admin/payment/<int:request_id>/reject/",
        payment_views.reject_payment_request,
        name="reject_payment",
    ),
]
