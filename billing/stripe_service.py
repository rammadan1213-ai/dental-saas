import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(user, plan_price_id):
    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=user.email,
        line_items=[
            {
                "price": plan_price_id,
                "quantity": 1,
            }
        ],
        success_url="https://yourdomain.com/success/",
        cancel_url="https://yourdomain.com/cancel/",
    )
