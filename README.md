# fbschedulerai 🚀

> **Autonomous Zero-Cost AI Content Engine & Meta Graph API Auto-Publisher**  
> An enterprise-grade, self-hosted system that ideates reflections, generates branded graphics and 9:16 vertical video reels, and programmatically publishes to Facebook Pages and Reels with **$0/month** recurring AI costs.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django 5.0](https://img.shields.io/badge/Django-5.0-092E20.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A.svg?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Meta Graph API](https://img.shields.io/badge/Meta_Graph_API-v19.0+-0081FB.svg?logo=meta&logoColor=white)](https://developers.facebook.com/)

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Zero-Cost Architecture](#-zero-cost-architecture)
- [System Architecture & Workflow](#-system-architecture--workflow)
- [Tech Stack](#-tech-stack)
- [Quick Start with Docker](#-quick-start-with-docker)
- [Local Development Setup (Non-Docker)](#-local-development-setup-non-docker)
- [Environment Configuration](#-environment-configuration)
- [Meta Graph API & Token Setup](#-meta-graph-api--token-setup)
- [Celery Scheduling & Cron Routines](#-celery-scheduling--cron-routines)
- [Django Admin & Hero KPI Dashboard](#-django-admin--hero-kpi-dashboard)
- [Management Commands](#-management-commands)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**fbschedulerai** is an autonomous, production-ready content generation and multi-media scheduling engine. Originally engineered for spiritual leaders and digital evangelization (specifically designed for **Rev. Fr. Ejiogu Chukwuemeka** by **Engr. Christian Kelechi Eze**), this platform eliminates daily manual intervention while keeping operational and API costs near absolute zero.

The system autonomously:
1. Prompts zero-cost LLM endpoints to curate liturgical thoughts, morning prayers, and scripture reflections.
2. Synthesizes branded visual quote cards (via Pillow and serverless image generation) and vertical video reels (9:16) with synthesized neural voiceovers (via `edge-tts`) and burned-in typography.
3. Queues and publishes posts directly to Facebook via the Meta Graph API, including full compliance with Meta's **3-Step Resumable Reels Protocol**.

---

## ✨ Key Features

- 🤖 **Zero-Cost LLM Ideation Engine**: Integrates with OpenRouter's free router (`meta-llama/llama-3.2-3b-instruct:free`, `mistralai/mistral-7b-instruct:free`, etc.) to generate structured posts containing title, caption, scripture citation, hashtags, and visual prompts.
- 🎨 **Branded Quote Card Generator**: Dynamically composites high-resolution images, gradient overlays, liturgical branding, and styled typography using Python `Pillow` and Hugging Face serverless inference.
- 🎬 **Vertical Video Reels (9:16) Generator**:
  - **Neural TTS**: High-fidelity, natural voiceovers generated for free via `edge-tts` (Microsoft Edge neural voice models).
  - **FFmpeg & MoviePy Assembly**: Generates vertical 1080x1920 MP4 videos formatted strictly according to Meta Reels specifications (H.264 video codec, AAC audio, 24-30 fps).
- 📲 **Production Meta Graph API Publisher**:
  - Direct feed updates (`POST /{page-id}/feed`)
  - Photo posts (`POST /{page-id}/photos`)
  - **Meta 3-Step Resumable Reels Upload Protocol**: Session start &rarr; Binary chunk stream to `rupload.facebook.com` &rarr; Finish & publish.
- ⏰ **Autonomous Celery Task Queue**:
  - Pre-scheduled periodic cron routines for morning, midday, and evening posts.
  - Automatic queue scanner running every 5 minutes to dispatch due posts.
  - Exponential backoff retry handler to absorb transient network failures or Meta rate limits.
- 🔒 **Token Security & Live Health Vault**:
  - Secure credential storage (via `.env` or encrypted database vault).
  - Live token verification with one-click health status checks in the dashboard and automated midnight health audits.
- 📊 **Custom Hero Admin KPI Dashboard**:
  - Real-time KPIs for Total, Scheduled, Published, and Failed posts.
  - Live preview widgets for generated images, vertical video reels, and audio clips.
  - One-click trigger buttons to immediately generate reflections, dispatch due posts, or audit token validity.

---

## 💰 Zero-Cost Architecture

| Pipeline Layer | Technology / Service | Monthly Cost |
| :--- | :--- | :--- |
| **Backend Framework** | Django 5.x & Django REST Framework | **$0.00** |
| **Compute / VPS** | Self-hosted Linux VPS (Contabo Ubuntu LTS) / Local Docker | Free tier or low-cost VPS |
| **Database & Queue** | PostgreSQL + Redis (Self-hosted) | **$0.00** |
| **Text Generation (LLM)** | OpenRouter Free Router (Llama 3.2, Mistral) | **$0.00** |
| **Voiceover Synthesis (TTS)** | Microsoft Edge Neural Voices (`edge-tts`) | **$0.00** |
| **Image & Graphic Synthesis** | Pillow + Hugging Face Serverless / SD-Turbo | **$0.00** |
| **Video Assembly** | System FFmpeg & MoviePy | **$0.00** |
| **Social Publishing** | Meta Graph API (Pages & Video Reels) | **$0.00** |

---

## 🏗 System Architecture & Workflow

```mermaid
flowchart TD
    subgraph Scheduling ["⏰ Celery Beat & Trigger Layer"]
        CB[Celery Beat Crontab]
        Manual[Admin Dashboard One-Click Trigger]
    end

    subgraph ContentPipeline ["🧠 Content Pipeline Orchestrator"]
        Prompt[Prompt Bank Selector]
        LLM["OpenRouter Free LLM\n(Llama 3.2 / Mistral)"]
        TTS["edge-tts\n(Neural Audio Synthesis)"]
        ImgEngine["Image Service\n(Pillow + HF Serverless)"]
        VidEngine["Video Service\n(FFmpeg + MoviePy 9:16 Reels)"]
    end

    subgraph Storage ["💾 Persistence & Vault"]
        DB[("PostgreSQL / SQLite\n(GeneratedPost, MediaAsset)")]
        Vault[("Meta Token Vault\n(Encrypted Page Credentials)")]
    end

    subgraph Dispatcher ["🚀 Publishing Engine"]
        Queue["Due Post Dispatcher\n(Every 5 Mins)"]
        Client[Meta Graph Client]
        Audit[Publishing Log Audit]
    end

    subgraph MetaGraph ["🌐 Meta Graph API"]
        FBFeed["POST /{page-id}/feed"]
        FBPhoto["POST /{page-id}/photos"]
        FBReel["3-Step Reels Protocol\n(rupload.facebook.com)"]
    end

    CB --> Prompt
    Manual --> Prompt
    Prompt --> LLM
    LLM --> ImgEngine
    LLM --> TTS
    TTS --> VidEngine
    ImgEngine --> DB
    VidEngine --> DB
    LLM --> DB

    Queue --> DB
    Queue --> Client
    Vault --> Client
    Client --> FBFeed
    Client --> FBPhoto
    Client --> FBReel
    Client --> Audit
```

---

## 🛠 Tech Stack

- **Core:** Python 3.12, Django 5.0, Django REST Framework, `django-environ`
- **Asynchronous Processing:** Celery 5.4, Redis 7
- **Database:** PostgreSQL 15 (Docker) or SQLite3 (Local testing)
- **Media Engine:** FFmpeg, `moviepy`, `Pillow`, `edge-tts`
- **Inference & APIs:** OpenRouter API, Hugging Face Serverless API, Meta Graph API v19.0+
- **Infrastructure:** Docker, Docker Compose, Gunicorn, Nginx

---

## 🚀 Quick Start with Docker

The fastest way to spin up the entire application (Django, PostgreSQL, Redis, Celery Worker, and Celery Beat):

### 1. Clone the Repository
```bash
git clone https://github.com/christiankelechi/fbschedulerai.git
cd fbschedulerai
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your `OPENROUTER_API_KEY`, `META_PAGE_ID`, and `META_PAGE_ACCESS_TOKEN` (see [Environment Configuration](#-environment-configuration)).

### 3. Build & Run Containers
```bash
docker compose up -d --build
```

### 4. Run Migrations & Initialize
```bash
# Run database migrations
docker compose exec web python manage.py migrate

# Seed pre-built Catholic reflection and prayer prompt banks
docker compose exec web python manage.py seed_prompts

# Create administrative superuser
docker compose exec web python manage.py createsuperuser
```

### 5. Access Dashboard
Navigate to `http://localhost:8000/admin/` and log in with your superuser credentials.

---

## 💻 Local Development Setup (Non-Docker)

### 1. Prerequisites
- Python 3.12 installed
- System FFmpeg installed and available on your system `PATH`
- Redis server running locally on port `6379`

### 2. Virtual Environment & Dependencies
```bash
# Create and activate virtual environment
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install required Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Local Database
In your `.env` file, uncomment SQLite for zero-setup local development:
```env
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://127.0.0.1:6379/0
```

### 4. Migrate and Seed
```bash
python manage.py migrate
python manage.py seed_prompts
python manage.py createsuperuser
```

### 5. Start Background Workers
In separate terminal windows:
```bash
# Terminal 1: Celery Worker
celery -A core_project worker -l info

# Terminal 2: Celery Beat Scheduler
celery -A core_project beat -l info

# Terminal 3: Django Web Server
python manage.py runserver
```

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root with the following parameters:

```env
# ==========================================
# Django Core Settings
# ==========================================
SECRET_KEY=your-secure-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# ==========================================
# Database Configuration
# ==========================================
# Full PostgreSQL connection string (Docker or Production)
DATABASE_URL=postgres://postgres:postgres@localhost:5432/fbscheduler
# Or use SQLite for local development:
# DATABASE_URL=sqlite:///db.sqlite3

# ==========================================
# Redis / Celery Task Queue
# ==========================================
REDIS_URL=redis://redis:6379/0

# ==========================================
# Meta Graph API (Facebook Publishing)
# ==========================================
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_PAGE_ID=your_facebook_numeric_page_id
META_PAGE_ACCESS_TOKEN=your_never_expiring_page_access_token

# ==========================================
# Zero-Cost AI Inference Providers
# ==========================================
# OpenRouter API Key for free LLM models
OPENROUTER_API_KEY=your_openrouter_api_key

# Hugging Face API Token for image quote card backgrounds
HUGGINGFACE_API_KEY=your_huggingface_api_token
```

---

## 🔑 Meta Graph API & Token Setup

To publish autonomously 24/7 without authentication interruptions, you need a **Never-Expiring Page Access Token**.

### Required Permissions
Your Meta App and Token must have the following 4 scopes:
- `pages_show_list`
- `pages_read_engagement`
- `pages_manage_posts`
- `publish_video` *(Crucial for 9:16 Video Reels)*

### 3-Step Token Exchange Process
1. **Short-Lived User Token**: Generate in [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer) with the permissions above.
2. **Exchange for 60-Day Token**:
   ```bash
   curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token?\
   grant_type=fb_exchange_token&\
   client_id=YOUR_APP_ID&\
   client_secret=YOUR_APP_SECRET&\
   fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
   ```
3. **Obtain Never-Expiring Page Token**:
   ```bash
   curl -X GET "https://graph.facebook.com/v19.0/YOUR_PAGE_ID?fields=access_token,name&\
   access_token=YOUR_60_DAY_USER_TOKEN"
   ```

> 📖 **Full Guide:** For detailed screenshots, edge cases, and Reels protocols, read [`api setup.md`](api%20setup.md).

---

## ⏰ Celery Scheduling & Cron Routines

The engine comes pre-configured with default Celery Beat crontab routines in `core_project/settings.py`:

| Routine Name | Crontab | Description |
| :--- | :--- | :--- |
| `publish-due-posts-every-5-mins` | `*/5 * * * *` | Scans `GeneratedPost` queue and publishes any post whose `scheduled_time` has arrived. |
| `generate-morning-prayer-daily` | `0 5 * * *` | Generates Morning Prayer at 05:00 UTC (scheduled to publish at 06:00 UTC). |
| `generate-daily-reflection-reel` | `0 11 * * *` | Generates vertical 9:16 video Reel at 11:00 UTC (scheduled to publish at 12:00 UTC). |
| `generate-evening-reflection-daily` | `0 18 * * *` | Generates Evening Reflection at 18:00 UTC (scheduled to publish at 19:00 UTC). |
| `verify-meta-token-daily` | `15 0 * * *` | Runs daily token health audit against Meta Graph API at midnight. |

---

## 📊 Django Admin & Hero KPI Dashboard

The system features an enhanced, modern Django Admin dashboard (`/admin/`):

- **Hero KPIs**: Real-time counter widgets displaying Total Posts, Scheduled, Published, and Failed counts.
- **Token Health Indicator**: Live badge showing the active Meta Page name, Page ID, and validation state (`🟢 Active`, `🟡 Unverified`, `🔴 Expired`).
- **Interactive Quick Actions**:
  - `Generate Content Now`: Immediately synthesizes a post with selectable category, format, and lead time.
  - `Publish Due Now`: Forces an instant dispatch check without waiting for the 5-minute cron.
  - `Verify Facebook Token`: Queries Meta Graph API in real-time to check token validity and permissions.
- **Embedded Media Players**:
  - Inline image quote card previews.
  - HTML5 video player for vertical 9:16 reels.
  - Audio waveform player for voiceover artifacts.
- **Audit Trails**: Full `PublishingLog` recording endpoint used, Meta Post ID, roundtrip duration, and sanitized request/response payloads.

---

## ⌨️ Management Commands

Manage and test your content engine directly from the terminal:

```bash
# Seed initial prompt banks into database
python manage.py seed_prompts

# Manually generate a reflection
python manage.py generate_reflection --category daily_reflection --type image_quote --delay-hours 1

# Immediately scan and publish due posts
python manage.py publish_due

# Verify Meta token status and permissions
python manage.py verify_token
```

---

## 📁 Project Structure

```text
fbschedulerai/
├── api setup.md             # In-depth Meta Graph API & Reels protocol guide
├── content/                 # Content ideation & media synthesis app
│   ├── admin.py             # Admin models & custom media preview filters
│   ├── models.py            # ContentPrompt, MediaAsset, GeneratedPost models
│   ├── tasks.py             # Celery tasks for autonomous content generation
│   ├── management/commands/ # seed_prompts, generate_reflection commands
│   └── services/            # Core business logic
│       ├── llm_service.py   # OpenRouter LLM structured output client
│       ├── image_service.py # Pillow & HF quote card generator
│       ├── tts_service.py   # edge-tts neural voiceover synthesis
│       ├── video_service.py # FFmpeg & moviepy 9:16 Reel generator
│       └── orchestrator.py  # End-to-end pipeline coordinator
├── core_project/            # Django root configuration
│   ├── celery.py            # Celery app initialization
│   ├── settings.py          # App settings & Celery Beat schedules
│   ├── urls.py              # Custom dashboard routes & API endpoints
│   └── admin_views.py       # One-click dashboard action triggers
├── publishing/              # Meta Graph API publishing app
│   ├── admin.py             # Token Vault & Publishing Log admin
│   ├── models.py            # MetaTokenVault & PublishingLog models
│   ├── tasks.py             # Due post dispatch & token health check tasks
│   ├── management/commands/ # publish_due, verify_token commands
│   └── services/            # Publishing service logic
│       ├── meta_client.py   # Meta Graph API & 3-Step Reels client
│       └── publisher.py     # Publishing retry & audit log orchestrator
├── templates/               # Custom Django Admin templates
│   └── admin/index.html     # Hero KPI Dashboard template
├── docker-compose.yml       # Production/development multi-container stack
├── Dockerfile               # Python 3.12 + FFmpeg application image
├── requirements.txt         # Project dependencies
├── .env.example             # Template for environment configuration
├── LICENSE                  # MIT License
└── README.md                # Project documentation
```

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome!
To contribute:
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

Developed with ❤️ by **[Christian Kelechi Eze](https://github.com/christiankelechi)**.

