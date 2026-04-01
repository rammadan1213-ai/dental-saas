from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
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
]
