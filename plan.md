# Project Plan: Automated Facebook Content Generation & Scheduling Engine

## 1. Executive Summary
This document outlines a comprehensive 3-week delivery plan, architecture, and guidelines for building an autonomous content creation and scheduling backend engine. The platform is designed for Rev. Fr. Ejiogu Chukwuemeka to generate niche-relevant reflections, scriptural thoughts, and educational content. It synthesizes visual/video media and programmatically publishes posts and Reels to Facebook using zero-cost AI endpoints, all orchestrated by a Django and Django REST Framework (DRF) backend.

## 2. Architecture Overview
The system is built on a scalable, asynchronous, and cost-efficient stack deployed on a self-hosted Contabo VPS.

### Technology Stack
*   **Backend Framework:** Python 3.12, Django 5.x, Django REST Framework (DRF)
*   **Asynchronous Task Queue:** Celery
*   **Message Broker:** Redis
*   **Database:** PostgreSQL (for storing posts, metadata, logs, and token vaults)
*   **Media Assembly:** FFmpeg (system binary), `moviepy`, `Pillow`
*   **Server Environment:** Ubuntu 24.04 LTS (Contabo VPS), Docker Compose, Nginx, Let's Encrypt SSL

### Zero-Cost Inference Strategy
*   **Text Generation (LLM):** OpenRouter (free models like Llama 3, Mistral)
*   **Image Generation:** Hugging Face Serverless Inference / Local SD-Turbo
*   **Voiceover (TTS):** `edge-tts` (Microsoft Edge Neural Voices)
*   **Publishing:** Meta Graph API (Page Publishing & Reels Endpoints)

---

## 3. Three-Week Delivery Plan

### Week 1: Foundation, Local Environment & Core Models
**Goal:** Set up the local Docker development environment, base Django project, and connect to Meta.
*   **Day 1-2: Local Infrastructure Setup**
    *   Initialize local development environment (Windows/Linux/macOS).
    *   Install Docker, Docker Compose, and ensure local system dependencies (like FFmpeg) are available via Docker.
    *   Set up local tunneling (e.g., ngrok or local API router) for Meta webhook testing if needed.
*   **Day 3: Django & DRF Boilerplate**
    *   Initialize Django 5 project and DRF.
    *   Configure PostgreSQL database and Redis broker in `docker-compose.yml`.
    *   Set up environment variables (`.env`) for secrets, DB credentials, and API keys.
*   **Day 4-5: Database Design & Models**
    *   Create models for `ContentPrompt`, `GeneratedPost`, `MediaAsset`, and `PublishingLog`.
    *   Create a secure Vault model for Meta Page Access Tokens and App Secrets.
    *   Build out Django Admin for monitoring these models.
*   **Day 6-7: Meta Developer App Configuration**
    *   Create and configure Meta Developer App.
    *   Secure long-lived Page Access Tokens.
    *   Test basic connection to the Meta Graph API.

### Week 2: AI Pipeline & Media Generation
**Goal:** Implement text generation, image rendering, and video synthesis pipelines.
*   **Day 1-2: LLM Text Generation Integration**
    *   Implement OpenRouter API client.
    *   Create structured prompt templates for captions, scripture citations, hashtags, and visual prompts.
    *   Write Celery tasks for autonomous ideation based on prompt banks.
*   **Day 3-4: Static Image Generation**
    *   Integrate Hugging Face Serverless Inference for image generation.
    *   Use `Pillow` to apply branded quote overlays, typography, and logos onto generated graphics.
*   **Day 5-6: Video & Audio Synthesis (Reels)**
    *   Implement `edge-tts` for voiceover synthesis from generated text.
    *   Use `moviepy` and `FFmpeg` to stitch audio, vertical video loops (9:16), and subtitles.
    *   Ensure output is a compressed MP4 ready for Meta.
*   **Day 7: Pipeline Integration & Queuing**
    *   Link the text, image, and video generators into a cohesive Celery workflow.
    *   Handle API rate limits and throttling using Celery's retry mechanism with exponential backoff.

### Week 3: Automation, Testing & VPS Deployment
**Goal:** Automate publishing to Facebook, finalize the scheduling engine, test locally, and deploy to VPS.
*   **Day 1-2: Facebook Publishing Engine (Photos/Posts)**
    *   Implement REST endpoints to handle `/{page-id}/feed` and `/{page-id}/photos`.
    *   Write tasks to attach generated images and post text.
*   **Day 3-4: Meta Reels Upload Protocol**
    *   Implement the 3-step Reels upload workflow:
        1.  Start: Generate reel video session ID.
        2.  Transfer: Upload binary data to Meta `rupload` servers.
        3.  Finish: Apply captions, publish/visibility flags, and trigger indexing.
*   **Day 5: Scheduling, Local E2E Testing & Admin Dashboard**
    *   Configure Celery Beat cron expressions for periodic triggers.
    *   Enhance Django Admin to show FAILED/SUCCESS statuses.
    *   Run comprehensive E2E tests locally simulating real-world scheduling.
*   **Day 6-7: VPS Provisioning & Production Deployment**
    *   Purchase and initialize Ubuntu 24.04 on Contabo VPS.
    *   Install Docker, Nginx, setup domain and SSL (Let's Encrypt) on the VPS.
    *   Deploy the tested application to the VPS and monitor resources (CPU/RAM during video rendering).
    *   Provide documentation, `.env.example`, and operational handover.

---

## 4. Professional Setup Guidelines

### Code Structure & Best Practices
*   **Apps:** Separate logic into distinct Django apps (e.g., `core`, `ai_pipeline`, `facebook_publisher`).
*   **Fat Models, Skinny Views:** Keep business logic in models or separate service classes (e.g., `services/openrouter.py`, `services/ffmpeg_builder.py`).
*   **DRF Serializers:** Use DRF for API inputs (if exposing a webhook or frontend in the future) and validation.

### Security
*   **Environment Variables:** NEVER hardcode tokens. Use `python-dotenv` or `django-environ`.
*   **Token Encryption:** Consider encrypting the Meta Access Tokens in the PostgreSQL database using packages like `django-cryptography` if strict security is desired.

### Background Tasks (Celery)
*   **Resource Management:** Throttle video rendering tasks using Celery worker concurrency limits so they do not max out the Contabo VPS CPU.
*   **Error Handling:** Anticipate Meta API rate limits and OpenRouter timeouts. Use `@shared_task(bind=True, max_retries=3)` with `countdown` (exponential backoff).

### Deployment (Dockerized)
*   Maintain a `docker-compose.yml` defining:
    *   `web`: Django Gunicorn server.
    *   `db`: PostgreSQL.
    *   `redis`: Redis broker.
    *   `celery_worker`: Main worker for API calls.
    *   `celery_worker_heavy`: Dedicated worker for FFmpeg tasks with limited concurrency (e.g., `concurrency=1`).
    *   `celery_beat`: The scheduler.

### Logging & Monitoring
*   Configure Python's `logging` module to output to console (for Docker logs) and file.
*   Log all Meta API responses, especially non-200 HTTP statuses, with the trace ID provided by Meta for debugging.
