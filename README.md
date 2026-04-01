# Dental Clinic SaaS Platform

A comprehensive, production-ready **Multi-Tenant SaaS Dental Clinic Management System** built with Django and Django REST Framework. This platform enables dental clinics to manage patients, appointments, treatments, billing, and subscriptions.

## Features

### Core Functionality
- **Patient Management**: Complete CRUD operations with medical history tracking
- **Appointment Scheduling**: Calendar view with status tracking (Pending, Confirmed, Completed, Cancelled)
- **Treatment Records**: Track diagnoses, procedures, and costs per patient
- **Billing & Invoicing**: Generate invoices, record payments, and export to PDF
- **Dashboard & Analytics**: Visual reports with charts and statistics

### Multi-Tenant SaaS Architecture
- **Clinic Isolation**: Each clinic has its own data (patients, appointments, etc.)
- **Subscription Management**: Three plan tiers with feature restrictions
- **Stripe Payments**: Integrated payment processing for subscriptions

### User Roles
- **Admin**: Full system access, user management, audit logs
- **Dentist**: Manage appointments, treatments, view patient records
- **Receptionist**: Patient management, appointments, billing

### Subscription Plans

| Feature | Basic ($10/mo) | Pro ($25/mo) | Enterprise ($50/mo) |
|---------|----------------|--------------|---------------------|
| Patients | 500 | Unlimited | Unlimited |
| Appointments | Yes | Yes | Yes |
| Billing & Invoicing | No | Yes | Yes |
| Basic Reports | No | Yes | Yes |
| Advanced Analytics | No | No | Yes |

## Tech Stack

- **Backend**: Django 4.2, Django REST Framework
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Session-based with JWT support
- **Payments**: Stripe
- **PDF Generation**: xhtml2pdf
- **Charts**: Chart.js

## Project Structure

```
dental_clinic/
├── accounts/              # User authentication and management
├── patients/              # Patient records and documents
├── appointments/          # Appointment scheduling
├── treatments/            # Treatment records
├── billing/               # Invoices and payments
├── dashboard/             # Analytics and reports
├── clinics/               # Multi-tenant clinic & subscription models
├── payments/              # Stripe payment integration
├── dental_clinic/         # Django project settings
├── templates/             # Base templates
├── static/                # CSS, JavaScript, images
└── media/                 # Uploaded files
```

## Installation

### Prerequisites
- Python 3.9+
- pip
- Stripe account (for payments)

### Setup Instructions

1. **Clone or navigate to the project directory**
   ```bash
   cd dental-clinic
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
   STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create sample data (includes demo clinic)**
   ```bash
   python manage.py create_sample_data
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - App: `http://127.0.0.1:8000/`
   - Admin: `http://127.0.0.1:8000/admin/`

## Default Login Credentials

After running `create_sample_data`:
- **Admin**: `admin` / `admin123`
- **Dentist**: `drsmith` / `dentist123`
- **Receptionist**: `receptionist` / `reception123`

## Stripe Setup

### 1. Get Stripe API Keys
1. Sign up at [Stripe](https://stripe.com)
2. Go to Developers > API Keys
3. Copy Test Mode keys

### 2. Set Up Webhooks (for production)
1. Go to Developers > Webhooks
2. Add endpoint: `https://yourdomain.com/api/payments/webhook/`
3. Select events:
   - `checkout.session.completed`
   - `invoice.paid`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Copy webhook signing secret

### 3. Configure Environment Variables
```env
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

## API Endpoints

### Subscription API
- `POST /subscription/api/create-checkout/` - Create Stripe checkout session
- `GET /subscription/manage/` - View/manage subscription
- `POST /api/payments/cancel/` - Cancel subscription

### Payment API
- `POST /api/payments/create-checkout-session/` - Create checkout session
- `POST /api/payments/create-payment/` - One-time payment
- `POST /api/payments/webhook/` - Stripe webhook handler
- `GET /api/payments/history/` - Payment history

### Core API
- `GET /api/patients/` - List patients
- `POST /api/patients/` - Create patient
- `GET /api/appointments/` - List appointments
- `POST /api/appointments/` - Create appointment
- `GET /api/invoices/` - List invoices
- `POST /api/invoices/` - Create invoice
- `GET /api/payments/` - List payments

## Production Deployment

### Environment Variables
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
DATABASE_URL=postgres://user:pass@host:5432/dbname
```

### Using Gunicorn
```bash
pip install gunicorn
gunicorn dental_clinic.wsgi:application --bind 0.0.0.0:8000
```

### Cloud Platforms
- **Railway**: Add `Railway.toml`
- **Render**: Use render.yaml
- **AWS**: Elastic Beanstalk or ECS
- **DigitalOcean**: App Platform or Droplets

## Security Features

- CSRF protection
- Password hashing with PBKDF2
- SQL injection prevention via ORM
- XSS protection in templates
- Subscription-based feature access control
- Multi-tenant data isolation
- Audit logging

## License

MIT License

## Acknowledgments

- Django & Django REST Framework
- Bootstrap 5
- Stripe
- Chart.js
- xhtml2pdf
