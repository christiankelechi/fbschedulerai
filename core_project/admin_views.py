import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from content.models import GeneratedPost, MediaAsset, ContentCategory, PostType, PostStatus
from publishing.models import PublishingLog, MetaTokenVault
from content.services.orchestrator import ContentPipelineOrchestrator
from publishing.services.publisher import PostPublisher
from publishing.services.meta_client import MetaGraphClient

logger = logging.getLogger(__name__)


@staff_member_required
def trigger_generation_view(request):
    """
    Manual trigger from Admin Dashboard to immediately run content ideation & synthesis.
    """
    category = request.GET.get('category', ContentCategory.DAILY_REFLECTION)
    post_type = request.GET.get('type', PostType.IMAGE_QUOTE)
    hours = int(request.GET.get('delay_hours', 1))

    try:
        orchestrator = ContentPipelineOrchestrator()
        target_time = timezone.now() + timezone.timedelta(hours=hours)
        post = orchestrator.generate_post(
            category=category,
            post_type=post_type,
            scheduled_time=target_time
        )
        messages.success(
            request,
            f"✨ Successfully generated new {post.get_post_type_display()} (#{post.id}) scheduled for {target_time.strftime('%b %d, %H:%M UTC')}!"
        )
    except Exception as e:
        logger.error(f"Error in manual generation: {e}", exc_info=True)
        messages.error(request, f"Generation error: {e}")

    return redirect('/admin/')


@staff_member_required
def trigger_publish_due_view(request):
    """
    Scans queue and publishes due posts immediately.
    """
    from publishing.tasks import publish_due_posts_task
    try:
        result = publish_due_posts_task()
        count = result.get('dispatched_count', 0)
        messages.success(request, f"🚀 Scanned queue: Dispatched {count} due post(s) to Meta.")
    except Exception as e:
        messages.error(request, f"Publishing queue error: {e}")

    return redirect('/admin/')


@staff_member_required
def trigger_publish_single_post_view(request, post_id):
    """
    One-click immediate publish for a specific post.
    """
    post = get_object_or_404(GeneratedPost, id=post_id)
    try:
        publisher = PostPublisher()
        log = publisher.publish(post)
        if log.status == 'success':
            messages.success(request, f"🎉 Post #{post.id} successfully published to Facebook Page! (Meta ID: {log.meta_post_id})")
        else:
            messages.error(request, f"Failed to publish Post #{post.id}: {log.error_message}")
    except Exception as e:
        messages.error(request, f"Publishing exception: {e}")

    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


@staff_member_required
def trigger_verify_token_view(request):
    """
    Health check to verify Facebook Page token against Meta Graph API.
    """
    try:
        client = MetaGraphClient()
        res = client.verify_token()
        if res.get('valid'):
            messages.success(request, f"🟢 Facebook Token is VALID & ACTIVE for Page: {res.get('page_name')} (ID: {res.get('page_id')})")
        else:
            messages.warning(request, f"🔴 Token Verification Failed: {res.get('message')}")
    except Exception as e:
        messages.error(request, f"Verification error: {e}")

    return redirect('/admin/')
