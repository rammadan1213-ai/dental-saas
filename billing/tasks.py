from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_email(user_id, email, clinic_name):
    """Send welcome email to new clinic owner"""
    try:
        send_mail(
            subject=f"Welcome to {clinic_name}!",
            message=f"""
            Welcome to Dental SaaS!
            
            Your clinic '{clinic_name}' has been created successfully.
            
            Get started by:
            1. Adding your first patient
            2. Scheduling appointments
            3. Exploring the features
            
            Best regards,
            Dental SaaS Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {email}")
        return f"Welcome email sent to {email}"
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return str(e)


@shared_task
def send_subscription_expiry_reminder(clinic_id, email, days_remaining):
    """Send subscription expiry reminder"""
    try:
        send_mail(
            subject="Subscription Expiry Reminder",
            message=f"""
            Your subscription will expire in {days_remaining} days.
            
            Please renew your subscription to continue using our service.
            
            Visit your dashboard to renew.
            
            Best regards,
            Dental SaaS Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Expiry reminder sent to {email}")
        return f"Expiry reminder sent to {email}"
    except Exception as e:
        logger.error(f"Failed to send expiry reminder: {e}")
        return str(e)


@shared_task
def generate_invoice_pdf(invoice_id):
    """Generate invoice PDF in background"""
    from billing.models import Invoice
    import os
    from django.conf import settings
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from io import BytesIO

    try:
        invoice = Invoice.objects.get(id=invoice_id)
        template = get_template("billing/invoice_pdf.html")
        context = {"invoice": invoice}
        html = template.render(context)

        pdf_dir = os.path.join(settings.MEDIA_ROOT, "invoices")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"Invoice_{invoice.invoice_number}.pdf")

        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                BytesIO(html.encode("UTF-8")), dest=pdf_file, encoding="UTF-8"
            )

        logger.info(f"Invoice PDF generated: {pdf_path}")
        return f"PDF generated: {pdf_path}"
    except Exception as e:
        logger.error(f"Failed to generate invoice PDF: {e}")
        return str(e)


@shared_task
def check_expired_subscriptions():
    """Check for expired subscriptions and notify"""
    from clinics.models import Subscription
    from datetime import date

    expired = Subscription.objects.filter(expiry_date__lt=date.today(), is_active=True)

    for sub in expired:
        if sub.clinic.owner and sub.clinic.owner.email:
            send_subscription_expiry_reminder.delay(
                sub.clinic.id, sub.clinic.owner.email, 0
            )
        sub.is_active = False
        sub.save()

    return f"Checked {expired.count()} expired subscriptions"


@shared_task
def send_payment_confirmation(payment_id):
    """Send payment confirmation email"""
    from billing.models import Payment

    try:
        payment = Payment.objects.get(id=payment_id)
        email = payment.invoice.patient.email

        if email:
            send_mail(
                subject=f"Payment Received - ${payment.amount}",
                message=f"""
                Payment Confirmation
                
                We have received your payment of ${payment.amount}.
                
                Invoice: {payment.invoice.invoice_number}
                Date: {payment.payment_date}
                
                Thank you for your business!
                
                Best regards,
                Dental SaaS Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            logger.info(f"Payment confirmation sent for payment {payment_id}")
            return f"Payment confirmation sent"
    except Exception as e:
        logger.error(f"Failed to send payment confirmation: {e}")
        return str(e)
