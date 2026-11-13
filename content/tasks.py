import logging
from celery import shared_task
from django.utils import timezone
from content.models import ContentCategory, PostType, GeneratedPost
from content.services.orchestrator import ContentPipelineOrchestrator
from content.services.email_service import ZeniaEmailService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_content_task(self, category=ContentCategory.DAILY_REFLECTION, post_type=PostType.IMAGE_QUOTE, scheduled_delay_hours=0, dispatch_email=False):
    """
    Celery task to autonomously generate reflection content and media.
    Optionally dispatches immediately to Christian's email.
    """
    try:
        logger.info(f"[Celery] Starting autonomous content task: category={category}, type={post_type}, email={dispatch_email}")
        orchestrator = ContentPipelineOrchestrator()
        target_time = timezone.now() + timezone.timedelta(hours=scheduled_delay_hours)
        post = orchestrator.generate_post(
            category=category,
            post_type=post_type,
            scheduled_time=target_time,
            dispatch_email=dispatch_email
        )
        logger.info(f"[Celery] Successfully generated Post #{post.id} (status={post.status})")
        return {"post_id": post.id, "status": post.status, "category": post.category, "is_emailed": post.is_emailed}
    except Exception as exc:
        logger.error(f"[Celery] Content generation task error: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=90)
def dispatch_morning_prayer_email_task(self):
    """
    Scheduled task running at 3:00 AM WAT.
    Synthesizes Morning Prayer reflection + branded quote card,
    then automatically dispatches to Christian's email for morning review (ready from 6am).
    """
    try:
        logger.info("[Celery Beat] Executing 3:00 AM Morning Prayer Curation & Email Dispatch...")
        orchestrator = ContentPipelineOrchestrator()
        post = orchestrator.generate_and_email_morning_prayer()
        logger.info(f"[Celery Beat] 3:00 AM Morning Prayer Post #{post.id} generated and emailed successfully!")
        return {"post_id": post.id, "status": post.status, "emailed": post.is_emailed}
    except Exception as exc:
        logger.error(f"[Celery Beat] Error in 3:00 AM Morning Prayer dispatch: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=90 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=90)
def dispatch_evening_bible_study_email_task(self):
    """
    Scheduled task running at 5:00 PM WAT.
    Synthesizes Evening Bible Study reflection + branded quote card,
    then automatically dispatches to Christian's email for evening review and posting.
    """
    try:
        logger.info("[Celery Beat] Executing 5:00 PM Evening Bible Study Curation & Email Dispatch...")
        orchestrator = ContentPipelineOrchestrator()
        post = orchestrator.generate_and_email_evening_bible_study()
        logger.info(f"[Celery Beat] Evening Bible Study Post #{post.id} generated and emailed successfully!")
        return {"post_id": post.id, "status": post.status, "emailed": post.is_emailed}
    except Exception as exc:
        logger.error(f"[Celery Beat] Error in Evening Bible Study dispatch: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=90 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_post_review_email_task(self, post_id: int, recipient=None):
    """
    Celery task to dispatch an existing post to Christian's review email.
    """
    try:
        post = GeneratedPost.objects.get(id=post_id)
        email_service = ZeniaEmailService()
        log = email_service.send_post_for_review(post, recipient=recipient)
        return {"post_id": post_id, "status": log.status, "duration_ms": log.duration_ms}
    except GeneratedPost.DoesNotExist:
        logger.error(f"Post #{post_id} not found for email dispatch.")
        return {"error": "Post not found"}
    except Exception as exc:
        logger.error(f"Error emailing Post #{post_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def generate_daily_reflection_reel_task():
    """Scheduled task for Midday Reflection (Vertical Video Reel 9:16)."""
    return generate_content_task.delay(
        category=ContentCategory.DAILY_REFLECTION,
        post_type=PostType.VERTICAL_REEL,
        scheduled_delay_hours=0,
        dispatch_email=False
    )
