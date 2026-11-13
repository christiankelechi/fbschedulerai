import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from content.models import GeneratedPost, MediaAsset, ContentCategory, PostType, PostStatus
from publishing.models import PublishingLog, MetaTokenVault, PublishingStatus
from content.services.orchestrator import ContentPipelineOrchestrator
from content.services.email_service import ZeniaEmailService
from publishing.services.publisher import PostPublisher
from publishing.services.meta_client import MetaGraphClient

logger = logging.getLogger(__name__)


@staff_member_required
def mark_facebook_posted_view(request, post_id):
    """
    One-click action for Christian to confirm that he has reviewed and
    posted the reflection to Rev. Fr. Ejiogu Chukwuemeka's official Facebook Page.
    """
    post = get_object_or_404(GeneratedPost, id=post_id)
    post_url = request.POST.get('post_url', request.GET.get('post_url', ''))
    
    post.mark_as_facebook_posted(post_url=post_url)

    # Record manual posting activity in PublishingLog for complete audit history
    PublishingLog.objects.create(
        post=post,
        channel='facebook_manual',
        recipient='Rev. Fr. Ejiogu Facebook Page (Manual Post by Engr. Christian Eze)',
        status=PublishingStatus.SUCCESS,
        endpoint_used='Manual Facebook Web/App Posting',
        meta_post_id=post_url or f"manual-{post.id}",
        request_payload=f"Confirmed manual publish: {post.title} ({post.category})"
    )

    messages.success(
        request,
        f"✅ Confirmed! Post #{post.id} ('{post.title or post.get_category_display()}') marked as POSTED to Facebook!"
    )
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


@staff_member_required
def unmark_facebook_posted_view(request, post_id):
    """
    Reverts a post back to pending status if marked accidentally.
    """
    post = get_object_or_404(GeneratedPost, id=post_id)
    post.unmark_as_facebook_posted()

    messages.info(
        request,
        f"↩️ Post #{post.id} reverted back to Pending Facebook review."
    )
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


@staff_member_required
def trigger_send_email_view(request, post_id):
    """
    One-click manual action to forward or re-send any post to Christian's email.
    """
    post = get_object_or_404(GeneratedPost, id=post_id)
    recipient = request.GET.get('email', None)

    try:
        email_svc = ZeniaEmailService()
        log = email_svc.send_post_for_review(post, recipient=recipient)
        messages.success(
            request,
            f"📧 Post #{post.id} successfully emailed to {log.recipient} via Zenia Email API!"
        )
    except Exception as e:
        logger.error(f"Error emailing Post #{post.id}: {e}", exc_info=True)
        messages.error(request, f"Email delivery error for Post #{post.id}: {e}")

    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


@staff_member_required
def trigger_morning_flow_view(request):
    """
    Immediate trigger for the 3:00 AM Morning Prayer flow:
    Curates reflection, generates quote card graphic, and dispatches to Christian's email.
    """
    try:
        orchestrator = ContentPipelineOrchestrator()
        post = orchestrator.generate_and_email_morning_prayer()
        messages.success(
            request,
            f"🌅 Morning Prayer #{post.id} successfully generated & emailed to Christian ({post.email_recipient})! Ready for 6:00 AM review."
        )
    except Exception as e:
        logger.error(f"Error generating morning reflection: {e}", exc_info=True)
        messages.error(request, f"Morning Prayer generation error: {e}")

    return redirect('/admin/')


@staff_member_required
def trigger_evening_flow_view(request):
    """
    Immediate trigger for Evening Bible Study:
    Curates scripture study, generates branded quote card graphic, and dispatches to Christian's email.
    """
    try:
        orchestrator = ContentPipelineOrchestrator()
        post = orchestrator.generate_and_email_evening_bible_study()
        messages.success(
            request,
            f"📖 Evening Bible Study #{post.id} successfully generated & emailed to Christian ({post.email_recipient})! Ready for evening posting."
        )
    except Exception as e:
        logger.error(f"Error generating evening bible study: {e}", exc_info=True)
        messages.error(request, f"Evening Bible Study generation error: {e}")

    return redirect('/admin/')


@staff_member_required
def trigger_reel_flow_view(request):
    """
    Generates a 9:16 Vertical Video Reel with Edge-TTS voiceover and motion design.
    """
    try:
        orchestrator = ContentPipelineOrchestrator()
        post = orchestrator.generate_post(
            category=ContentCategory.DAILY_REFLECTION,
            post_type=PostType.VERTICAL_REEL,
            scheduled_time=timezone.now(),
            dispatch_email=False
        )
        messages.success(
            request,
            f"🎬 Vertical Video Reel #{post.id} successfully synthesized with voiceover audio and saved to Media Library!"
        )
    except Exception as e:
        logger.error(f"Error synthesizing video reel: {e}", exc_info=True)
        messages.error(request, f"Reel synthesis error: {e}")

    return redirect('/admin/')


@staff_member_required
def test_email_connection_view(request):
    """
    Health check to test connectivity to the Zenia Email API.
    """
    try:
        email_svc = ZeniaEmailService()
        result = email_svc.test_connection()
        if result.get('success'):
            messages.success(
                request,
                f"🟢 Zenia Email Channel Verified! Test message delivered to {result.get('recipient')}."
            )
        else:
            messages.warning(
                request,
                f"🟡 Zenia Email API responded with status {result.get('status_code')}: {result.get('response')}"
            )
    except Exception as e:
        logger.error(f"Email health check error: {e}", exc_info=True)
        messages.error(request, f"Email connection error: {e}")

    return redirect('/admin/')


@staff_member_required
def trigger_generation_view(request):
    """
    Generic manual trigger from Admin Dashboard to immediately run content ideation & synthesis.
    """
    category = request.GET.get('category', ContentCategory.DAILY_REFLECTION)
    post_type = request.GET.get('type', PostType.IMAGE_QUOTE)
    hours = int(request.GET.get('delay_hours', 0))
    dispatch_email = request.GET.get('email', 'false').lower() == 'true'

    try:
        orchestrator = ContentPipelineOrchestrator()
        target_time = timezone.now() + timezone.timedelta(hours=hours)
        post = orchestrator.generate_post(
            category=category,
            post_type=post_type,
            scheduled_time=target_time,
            dispatch_email=dispatch_email
        )
        messages.success(
            request,
            f"✨ Successfully generated {post.get_post_type_display()} (#{post.id})! Emailed: {post.is_emailed}"
        )
    except Exception as e:
        logger.error(f"Error in manual generation: {e}", exc_info=True)
        messages.error(request, f"Generation error: {e}")

    return redirect('/admin/')


@staff_member_required
def trigger_publish_due_view(request):
    """
    Scans queue and publishes due posts immediately (Legacy Meta queue).
    """
    from publishing.tasks import publish_due_posts_task
    try:
        result = publish_due_posts_task()
        count = result.get('dispatched_count', 0)
        messages.success(request, f"🚀 Scanned queue: Dispatched {count} due post(s).")
    except Exception as e:
        messages.error(request, f"Publishing queue error: {e}")

    return redirect('/admin/')


@staff_member_required
def trigger_publish_single_post_view(request, post_id):
    """
    One-click immediate publish via Meta API for a specific post.
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
