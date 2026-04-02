# 🦷 Dental Clinic SaaS Platform

A multi-tenant dental clinic management system built with Django.

## Features

- **Multi-tenant Architecture** - Each clinic has isolated data
- **Subscription Plans** - Basic ($10), Pro ($25), Enterprise ($50)
- **Stripe Integration** - Full payment processing
- **Role-based Access** - Admin, Dentist, Receptionist
- **Feature Gating** - Different features per plan

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/dental-clinic.git
cd dental-clinic

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database (PostgreSQL for production)
DATABASE_URL=postgres://user:pass@host:5432/dbname

# Stripe
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Email (optional)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
```

## Deployment

### Render (Recommended)

1. Push to GitHub
2. Create new **Web Service** on [Render](https://render.com)
3. Connect your GitHub repo
4. Set environment variables in Render dashboard
5. Deploy!

**Build Command:** `./build.sh`
**Start Command:** `gunicorn dental_clinic.wsgi:application`

## Plans & Features

| Feature | Basic | Pro | Enterprise |
|---------|-------|-----|------------|
| Patients | 500 | 10,000 | Unlimited |
| Billing | ❌ | ✅ | ✅ |
| Reports | ❌ | ✅ | ✅ |
| Analytics | ❌ | ❌ | ✅ |

## License

MIT License
