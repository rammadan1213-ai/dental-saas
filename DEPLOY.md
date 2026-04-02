# 🚀 RENDER DEPLOYMENT CHECKLIST

## Step 1: Install Git
1. Download Git: https://git-scm.com/download/win
2. Install with default settings
3. Restart your terminal

## Step 2: Push Code to GitHub

Open a NEW terminal (after Git install) and run:

```bash
cd "C:\Users\abdir\Videos\django project"

git init

git add .

git commit -m "Complete SaaS platform"

git branch -M main

git remote add origin https://github.com/YOUR_USERNAME/dental-clinic.git

git push -u origin main
```

## Step 3: Connect to Render

1. Go to: https://dashboard.render.com
2. Login with: rammadan1213@gmail.com
3. Click your service: dental-clinic-app-fcyw

## Step 4: Add Environment Variables

1. Go to **Environment** tab
2. Add these variables:

```
SECRET_KEY=your-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=dental-clinic-app-fcyw.onrender.com

# Stripe (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Keep your existing DATABASE_URL
```

## Step 5: Deploy

Click **"Manual Deploy"** → **"Deploy latest commit"**

## ✅ Verify Deployment

After deploy completes:
- [ ] Site loads: https://dental-clinic-app-fcyw.onrender.com
- [ ] Login works: /accounts/login/
- [ ] Registration works: /accounts/register/

## 🔧 Troubleshooting

### If deploy fails:
- Check **Logs** tab in Render
- Common issues:
  - Missing environment variables
  - Database migration errors

### If Stripe doesn't work:
- Add Stripe webhook: https://dashboard.stripe.com/test/webhooks
- Endpoint: https://dental-clinic-app-fcyw.onrender.com/api/payments/webhook/
- Events: checkout.session.completed, invoice.paid

---

## 📋 Your Render Dashboard
https://dashboard.render.com
Email: rammadan1213@gmail.com
App: https://dental-clinic-app-fcyw.onrender.com
