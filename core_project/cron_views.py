import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from content.services.orchestrator import ContentPipelineOrchestrator

logger = logging.getLogger(__name__)


def _is_authorized_cron(request) -> bool:
    """
    Validates optional Vercel Cron authorization header.
    If CRON_SECRET is configured, Vercel automatically sends 'Authorization: Bearer <CRON_SECRET>'.
    """
    cron_secret = getattr(settings, 'CRON_SECRET', '')
    if not cron_secret:
        return True
    auth_header = request.headers.get('Authorization', '')
    return auth_header == f"Bearer {cron_secret}"


@csrf_exempt
@require_http_methods(["GET", "POST"])
def cron_morning_prayer_view(request):
    """
    Vercel Cron endpoint scheduled for 02:00 UTC (03:00 AM WAT).
    Curates morning prayer reflection + quote card graphic,
    then automatically dispatches to Christian's email.
    """
    if not _is_authorized_cron(request):
        return JsonResponse({"error": "Unauthorized cron request"}, status=401)

    try:
        logger.info("[Vercel Cron] Triggered Morning Prayer curation & email dispatch...")
        orchestrator = ContentPipelineOrchestrator()
        post = orchestrator.generate_and_email_morning_prayer()
        return JsonResponse({
            "status": "success",
            "task": "morning_prayer",
            "post_id": post.id,
            "title": post.title,
            "category": post.category,
            "is_emailed": post.is_emailed,
            "email_recipient": post.email_recipient
        }, status=200)
    except Exception as e:
        logger.error(f"[Vercel Cron] Morning Prayer failed: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def cron_evening_bible_study_view(request):
    """
    Vercel Cron endpoint scheduled for 16:00 UTC (17:00 / 05:00 PM WAT).
    Curates evening Bible study reflection + quote card graphic,
    then automatically dispatches to Christian's email.
    """
    if not _is_authorized_cron(request):
        return JsonResponse({"error": "Unauthorized cron request"}, status=401)

    try:
        logger.info("[Vercel Cron] Triggered Evening Bible Study curation & email dispatch...")
        orchestrator = ContentPipelineOrchestrator()
        post = orchestrator.generate_and_email_evening_bible_study()
        return JsonResponse({
            "status": "success",
            "task": "evening_bible_study",
            "post_id": post.id,
            "title": post.title,
            "category": post.category,
            "is_emailed": post.is_emailed,
            "email_recipient": post.email_recipient
        }, status=200)
    except Exception as e:
        logger.error(f"[Vercel Cron] Evening Bible Study failed: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def cron_health_view(request):
    """
    Simple health check endpoint for monitoring Vercel deployment.
    """
    return JsonResponse({
        "status": "healthy",
        "service": "Rev. Fr. Ejiogu FB Content Scheduler Backend",
        "deployed_on": "Vercel",
        "time_zone": getattr(settings, 'TIME_ZONE', 'Africa/Lagos')
    }, status=200)

