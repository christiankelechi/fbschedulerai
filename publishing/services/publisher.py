import time
import json
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from content.models import GeneratedPost, PostType, PostStatus
from publishing.models import PublishingLog, PublishingStatus
from .meta_client import MetaGraphClient, MetaAPIError

logger = logging.getLogger(__name__)


class PostPublisher:
    """
    Publishing orchestrator that translates a GeneratedPost into Meta Graph API calls,
    records detailed publishing logs, tracks execution latency, and manages status transitions.
    """

    def __init__(self, meta_client: Optional[MetaGraphClient] = None):
        self.meta_client = meta_client or MetaGraphClient()

    def publish(self, post: GeneratedPost, allow_mock: bool = True) -> PublishingLog:
        """
        Publishes a single post.
        If credentials are not configured and allow_mock is True, simulates publication
        for local development and verification without crashing.
        """
        start_time = time.time()
        logger.info(f"Publishing Post #{post.id} (Type: {post.post_type})")

        post.status = PostStatus.PUBLISHING
        post.save(update_fields=['status'])

        endpoint = self._determine_endpoint(post)
        log = PublishingLog(
            post=post,
            status=PublishingStatus.IN_PROGRESS,
            endpoint_used=endpoint,
            retry_count=post.publishing_logs.count()
        )

        try:
            # Check for live Meta configuration
            if not self.meta_client.is_configured():
                if allow_mock:
                    logger.warning("Meta credentials not configured. Executing simulated mock publication.")
                    return self._handle_mock_publication(post, log, start_time)
                else:
                    raise MetaAPIError("Meta credentials are missing and mock publishing is disabled.")

            # Live Graph API Dispatch
            full_caption = post.full_published_text
            res: Dict[str, Any] = {}

            if post.post_type == PostType.TEXT_ONLY:
                res = self.meta_client.publish_feed_post(message=full_caption)
                meta_id = res.get('id')

            elif post.post_type == PostType.IMAGE_QUOTE:
                if not post.media or not post.media.file_path:
                    raise ValueError(f"Post #{post.id} is an image post but has no linked media asset.")
                res = self.meta_client.publish_photo_post(
                    photo_path=post.media.file_path.path,
                    caption=full_caption
                )
                meta_id = res.get('post_id') or res.get('id')

            elif post.post_type == PostType.VERTICAL_REEL:
                if not post.media or not post.media.file_path:
                    raise ValueError(f"Post #{post.id} is a video reel but has no linked media asset.")
                res = self.meta_client.publish_reel_video(
                    video_path=post.media.file_path.path,
                    description=full_caption
                )
                meta_id = res.get('id')

            else:
                raise ValueError(f"Unsupported post type: {post.post_type}")

            duration_ms = int((time.time() - start_time) * 1000)

            # Update Log
            log.status = PublishingStatus.SUCCESS
            log.meta_post_id = str(meta_id)
            log.request_payload = f"Type: {post.post_type} | Category: {post.category}"
            log.response_payload = json.dumps(res)
            log.duration_ms = duration_ms
            log.save()

            # Update Post
            post.status = PostStatus.PUBLISHED
            post.is_published = True
            post.published_at = timezone.now()
            post.meta_post_id = str(meta_id)
            post.save()

            logger.info(f"Post #{post.id} successfully published to Meta (ID: {meta_id}) in {duration_ms}ms")
            return log

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            err_message = str(e)
            logger.error(f"Failed to publish Post #{post.id}: {err_message}", exc_info=True)

            log.status = PublishingStatus.FAILED
            log.error_message = err_message
            log.duration_ms = duration_ms
            log.save()

            post.status = PostStatus.FAILED
            post.save(update_fields=['status'])
            return log

    def _determine_endpoint(self, post: GeneratedPost) -> str:
        if post.post_type == PostType.TEXT_ONLY:
            return f"/{self.meta_client.page_id or 'PAGE_ID'}/feed"
        elif post.post_type == PostType.IMAGE_QUOTE:
            return f"/{self.meta_client.page_id or 'PAGE_ID'}/photos"
        elif post.post_type == PostType.VERTICAL_REEL:
            return f"/{self.meta_client.page_id or 'PAGE_ID'}/video_reels"
        return "/unknown"

    def _handle_mock_publication(
        self,
        post: GeneratedPost,
        log: PublishingLog,
        start_time: float
    ) -> PublishingLog:
        import uuid
        mock_id = f"mock_{uuid.uuid4().hex[:12]}"
        duration_ms = int((time.time() - start_time) * 1000)

        log.status = PublishingStatus.SUCCESS
        log.meta_post_id = mock_id
        log.request_payload = f"[MOCK MODE] Type: {post.post_type} | Category: {post.category}"
        log.response_payload = json.dumps({
            "mock": True,
            "id": mock_id,
            "message": "Simulated successful publish because Meta credentials are not configured yet."
        })
        log.duration_ms = duration_ms
        log.save()

        post.status = PostStatus.PUBLISHED
        post.is_published = True
        post.published_at = timezone.now()
        post.meta_post_id = mock_id
        post.save()

        logger.info(f"[MOCK] Post #{post.id} marked published with mock ID {mock_id}")
        return log
