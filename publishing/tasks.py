import logging
from celery import shared_task
from django.utils import timezone
from content.models import GeneratedPost, PostStatus
from publishing.services.publisher import PostPublisher
from publishing.services.meta_client import MetaGraphClient

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def publish_single_post_task(self, post_id: int):
    """
    Celery task to publish an individual post to Facebook Meta Graph API.
    Retries up to 3 times with exponential backoff on transient failure.
    """
    try:
        post = GeneratedPost.objects.get(id=post_id)
        if post.is_published:
            logger.info(f"[Celery] Post #{post_id} is already published. Skipping.")
            return {"post_id": post_id, "status": "already_published"}

        publisher = PostPublisher()
        log = publisher.publish(post)

        if log.status == 'failed':
            logger.warning(f"[Celery] Publishing failed for Post #{post_id}: {log.error_message}")
            if self.request.retries < self.max_retries:
                countdown = 60 * (2 ** self.request.retries)
                logger.info(f"[Celery] Retrying Post #{post_id} in {countdown} seconds...")
                raise self.retry(countdown=countdown)

        return {"post_id": post_id, "status": log.status, "meta_post_id": log.meta_post_id}

    except GeneratedPost.DoesNotExist:
        logger.error(f"[Celery] Post #{post_id} does not exist.")
        return {"error": "Post not found"}
    except Exception as exc:
        logger.error(f"[Celery] Unexpected error publishing Post #{post_id}: {exc}", exc_info=True)
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@shared_task
def publish_due_posts_task():
    """
    Periodic task running every 5 minutes.
    Scans for posts that are scheduled and due for publication.
    """
    now = timezone.now()
    due_posts = GeneratedPost.objects.filter(
        is_published=False,
        scheduled_time__lte=now,
        status__in=[PostStatus.SCHEDULED, PostStatus.FAILED]
    ).exclude(status=PostStatus.PUBLISHING)

    count = due_posts.count()
    logger.info(f"[Celery Beat] Checking due posts: found {count} ready to publish.")

    dispatched = []
    for post in due_posts:
        logger.info(f"[Celery Beat] Dispatching publish task for Post #{post.id}")
        publish_single_post_task.delay(post.id)
        dispatched.append(post.id)

    return {"dispatched_count": len(dispatched), "post_ids": dispatched}


@shared_task
def verify_meta_tokens_task():
    """
    Daily health check task to verify Facebook Page Access Tokens.
    """
    client = MetaGraphClient()
    result = client.verify_token()
    logger.info(f"[Celery Beat] Meta Token Health Verification result: {result}")
    return result
