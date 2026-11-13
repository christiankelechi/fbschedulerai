# Vercel Deployment & Setup Guide

This project is fully configured and optimized for zero-cost serverless hosting on **Vercel** with continuous deployment directly from GitHub.

---

## 🚀 1. What Has Been Configured for Vercel

1. **`vercel.json`**:
   - Uses `@vercel/python` (Python 3.12) to serve Django's WSGI application (`core_project/wsgi.py`).
   - Uses `@vercel/static-build` with `build_files.sh` to run `collectstatic` and database migrations.
   - Configures **Vercel Cron Jobs**:
     - `0 2 * * *` (02:00 UTC = **03:00 AM WAT**): Triggers Morning Prayer curation & email dispatch.
     - `0 16 * * *` (16:00 UTC = **05:00 PM WAT**): Triggers Evening Bible Study curation & email dispatch.

2. **`build_files.sh`**:
   - Automatically installs `requirements.txt`.
   - Runs `python3 manage.py migrate --noinput` to keep the cloud PostgreSQL schema up to date.
   - Runs `python3 manage.py collectstatic --noinput --clear` using **WhiteNoise**.

3. **Static & Media Asset Handling**:
   - `whitenoise` serves all Django admin CSS/JS assets directly without needing an external S3 bucket.
   - On Vercel, `MEDIA_ROOT` points to `/tmp/media` to ensure compatibility with Vercel's read-only serverless filesystem.

4. **Security & Origins**:
   - `ALLOWED_HOSTS` includes `.vercel.app` and custom domains.
   - `CSRF_TRUSTED_ORIGINS` includes `https://*.vercel.app`.

---

## 🔑 2. Required Environment Variables on Vercel

In your **Vercel Project Dashboard** &rarr; **Settings** &rarr; **Environment Variables**, add the following keys:

| Variable Name | Recommended Value / Description |
| :--- | :--- |
| `SECRET_KEY` | Your Django secret key (e.g. `django-insecure-test-key-for-local-dev`) |
| `DEBUG` | `False` (for production) |
| `ALLOWED_HOSTS` | `.vercel.app,localhost,127.0.0.1` |
| `DATABASE_URL` | `postgres://avnadmin:AVNS_q0CsS51ZZTeY6e4Xbu4@pg-38f7fc77-chuksejiogu1920-b280.g.aivencloud.com:24034/defaultdb?sslmode=require` |
| `TIME_ZONE` | `Africa/Lagos` |
| `REVIEW_EMAIL` | `christian.eze.241801@unn.edu.ng` |
| `ZENIA_EMAIL_API_URL` | `https://zenia-email-api.vercel.app/api/v1/register_email` |
| `MORNING_DISPATCH_HOUR` | `3` |
| `EVENING_DISPATCH_HOUR` | `17` |
| `OPENROUTER_API_KEY` | *(Optional: Your OpenRouter API Key)* |
| `HUGGINGFACE_API_KEY` | *(Optional: Your Hugging Face API Key)* |

---

## 📦 3. How to Deploy (Push from GitHub)

Run the following commands in your terminal to commit the changes and push to GitHub:

```bash
git add .
git commit -m "Configure Vercel serverless deployment, WhiteNoise static files, and Vercel Cron jobs"
git push origin main
```

Once pushed, Vercel will automatically detect the commit, run `build_files.sh`, collect static files, and deploy your application.

---

## ⏰ 4. How the Automated Schedule Works on Vercel

Because Vercel is a serverless platform without persistent background workers (no 24/7 Celery worker), the automated schedule runs via **Vercel Cron Jobs**:
- **03:00 AM WAT (02:00 UTC)**: Vercel sends a GET request to `/api/cron/morning-prayer/`, generating the reflection, rendering the quote card, and emailing `christian.eze.241801@unn.edu.ng`.
- **05:00 PM WAT (16:00 UTC)**: Vercel sends a GET request to `/api/cron/evening-bible-study/`, generating and emailing the Evening Bible Study.
- You can also trigger generation anytime from the **Admin Dashboard** at `https://your-project.vercel.app/admin/`.

