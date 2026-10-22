import logging
from celery import shared_task
from django.utils import timezone
from content.models import ContentCategory, PostType
from content.services.orchestrator import ContentPipelineOrchestrator

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_content_task(self, category=ContentCategory.DAILY_REFLECTION, post_type=PostType.IMAGE_QUOTE, scheduled_delay_hours=1):
    """
    Celery task to autonomously generate reflection content and media.
    Schedules publication for `scheduled_delay_hours` into the future.
    """
    try:
        logger.info(f"[Celery] Starting autonomous content task for category: {category}, type: {post_type}")
        orchestrator = ContentPipelineOrchestrator()
        target_time = timezone.now() + timezone.timedelta(hours=scheduled_delay_hours)
        post = orchestrator.generate_post(
            category=category,
            post_type=post_type,
            scheduled_time=target_time
        )
        logger.info(f"[Celery] Successfully generated Post #{post.id} scheduled for {target_time}")
        return {"post_id": post.id, "status": post.status, "scheduled_time": str(target_time)}
    except Exception as exc:
        logger.error(f"[Celery] Content generation task error: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def generate_morning_prayer_task():
    """Scheduled task for Morning Prayer (Quote Card)."""
    return generate_content_task.delay(
        category=ContentCategory.MORNING_PRAYER,
        post_type=PostType.IMAGE_QUOTE,
        scheduled_delay_hours=1
    )


@shared_task
def generate_daily_reflection_reel_task():
    """Scheduled task for Midday Reflection (Vertical Video Reel)."""
    return generate_content_task.delay(
        category=ContentCategory.DAILY_REFLECTION,
        post_type=PostType.VERTICAL_REEL,
        scheduled_delay_hours=1
    )


@shared_task
def generate_evening_reflection_task():
    """Scheduled task for Evening Reflection (Quote Card)."""
    return generate_content_task.delay(
        category=ContentCategory.EVENING_REFLECTION,
        post_type=PostType.IMAGE_QUOTE,
        scheduled_delay_hours=1
    )
