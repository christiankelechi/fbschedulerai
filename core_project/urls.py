from datetime import timedelta
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.utils import timezone
from content.models import GeneratedPost, MediaAsset, ContentCategory, PostStatus
from publishing.models import PublishingLog, MetaTokenVault
from core_project.admin_views import (
    mark_facebook_posted_view,
    unmark_facebook_posted_view,
    trigger_send_email_view,
    trigger_morning_flow_view,
    trigger_evening_flow_view,
    trigger_reel_flow_view,
    test_email_connection_view,
    trigger_generation_view,
    trigger_publish_due_view,
    trigger_publish_single_post_view,
    trigger_verify_token_view,
)


def custom_admin_index(request):
    """
    Supplies rich dashboard statistics, daily Facebook posting compliance tracker,
    7-day activity streak, live media galleries, and recent audit logs to the admin view.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 1. Today's Specific Posts (Morning & Evening)
    today_morning_post = GeneratedPost.objects.filter(
        category=ContentCategory.MORNING_PRAYER,
        created_at__range=(today_start, today_end)
    ).first()

    today_evening_post = GeneratedPost.objects.filter(
        category__in=[ContentCategory.EVENING_BIBLE_STUDY, ContentCategory.EVENING_REFLECTION],
        created_at__range=(today_start, today_end)
    ).first()

    # If no post was created today yet, fetch the most recent one for context
    if not today_morning_post:
        latest_morning = GeneratedPost.objects.filter(category=ContentCategory.MORNING_PRAYER).order_by('-created_at').first()
    else:
        latest_morning = today_morning_post

    if not today_evening_post:
        latest_evening = GeneratedPost.objects.filter(
            category__in=[ContentCategory.EVENING_BIBLE_STUDY, ContentCategory.EVENING_REFLECTION]
        ).order_by('-created_at').first()
    else:
        latest_evening = today_evening_post

    morning_is_posted = bool(today_morning_post and today_morning_post.facebook_posted)
    evening_is_posted = bool(today_evening_post and today_evening_post.facebook_posted)

    today_posted_count = (1 if morning_is_posted else 0) + (1 if evening_is_posted else 0)

    if morning_is_posted and evening_is_posted:
        today_compliance_status = "completed"
        today_compliance_label = "🎉 COMPLETE: Both Morning & Evening Reflections Posted Today!"
    elif morning_is_posted:
        today_compliance_status = "morning_only"
        today_compliance_label = "⚡ IN PROGRESS: Morning Posted (1/2) • Evening Bible Study Pending"
    elif evening_is_posted:
        today_compliance_status = "evening_only"
        today_compliance_label = "⚡ IN PROGRESS: Evening Posted (1/2) • Morning Reflection Pending"
    else:
        today_compliance_status = "pending"
        today_compliance_label = "⏳ PENDING: No Posts Recorded on Facebook for Today Yet (0/2)"

    # 2. 7-Day Activity & Compliance Streak
    past_7_days = []
    for day_offset in range(6, -1, -1):
        target_day = (now - timedelta(days=day_offset)).date()
        d_start = timezone.make_aware(timezone.datetime.combine(target_day, timezone.datetime.min.time()))
        d_end = timezone.make_aware(timezone.datetime.combine(target_day, timezone.datetime.max.time()))

        day_posts = GeneratedPost.objects.filter(created_at__range=(d_start, d_end))
        day_m = day_posts.filter(category=ContentCategory.MORNING_PRAYER).first()
        day_e = day_posts.filter(category__in=[ContentCategory.EVENING_BIBLE_STUDY, ContentCategory.EVENING_REFLECTION]).first()

        m_ok = bool(day_m and day_m.facebook_posted)
        e_ok = bool(day_e and day_e.facebook_posted)

        is_today = (target_day == now.date())

        past_7_days.append({
            'date': target_day.strftime("%a %d"),
            'is_today': is_today,
            'morning_ok': m_ok,
            'evening_ok': e_ok,
            'both_ok': m_ok and e_ok,
            'has_activity': bool(m_ok or e_ok),
        })

    # 3. Overall Statistics & Metrics
    total_posts = GeneratedPost.objects.count()
    emailed_posts_count = GeneratedPost.objects.filter(is_emailed=True).count()
    facebook_posted_count = GeneratedPost.objects.filter(facebook_posted=True).count()
    pending_facebook_count = GeneratedPost.objects.filter(facebook_posted=False).count()
    total_media_count = MediaAsset.objects.count()

    recent_posts = GeneratedPost.objects.select_related('media').order_by('-created_at')[:10]
    recent_logs = PublishingLog.objects.select_related('post').order_by('-created_at')[:8]
    active_vault = MetaTokenVault.objects.filter(is_active=True).first()

    context = {
        # Real-time Header & Reviewer
        'current_wat_time': now.strftime("%A, %B %d, %Y • %I:%M %p WAT"),
        'review_email': getattr(settings, 'REVIEW_EMAIL', 'christian.eze.241801@unn.edu.ng'),
        # Today's Posting Compliance Centerpiece
        'today_compliance_status': today_compliance_status,
        'today_compliance_label': today_compliance_label,
        'today_posted_count': today_posted_count,
        'today_morning_post': today_morning_post,
        'today_evening_post': today_evening_post,
        'latest_morning': latest_morning,
        'latest_evening': latest_evening,
        'morning_is_posted': morning_is_posted,
        'evening_is_posted': evening_is_posted,
        # 7-Day Activity Streak
        'past_7_days': past_7_days,
        # KPI Cards
        'total_posts': total_posts,
        'emailed_posts_count': emailed_posts_count,
        'facebook_posted_count': facebook_posted_count,
        'pending_facebook_count': pending_facebook_count,
        'total_media_count': total_media_count,
        # Content & Audit
        'recent_posts': recent_posts,
        'recent_logs': recent_logs,
        'active_vault': active_vault,
        'title': 'Rev. Fr. Ejiogu FB Content Scheduler Dashboard',
    }
    return admin.site.index(request, extra_context=context)


urlpatterns = [
    # Dedicated Editorial & Review Operations
    path("admin/action/posts/<int:post_id>/mark-posted/", mark_facebook_posted_view, name="admin_mark_facebook_posted"),
    path("admin/action/posts/<int:post_id>/unmark-posted/", unmark_facebook_posted_view, name="admin_unmark_facebook_posted"),
    path("admin/action/posts/<int:post_id>/send-email/", trigger_send_email_view, name="admin_send_email"),
    path("admin/action/morning-flow/", trigger_morning_flow_view, name="admin_morning_flow"),
    path("admin/action/evening-flow/", trigger_evening_flow_view, name="admin_evening_flow"),
    path("admin/action/reel-flow/", trigger_reel_flow_view, name="admin_reel_flow"),
    path("admin/action/test-email/", test_email_connection_view, name="admin_test_email"),

    # Legacy & Direct API routes
    path("admin/action/generate-content/", trigger_generation_view, name="admin_generate_content"),
    path("admin/action/publish-due/", trigger_publish_due_view, name="admin_publish_due"),
    path("admin/action/verify-token/", trigger_verify_token_view, name="admin_verify_token"),
    path("admin/action/posts/<int:post_id>/publish-now/", trigger_publish_single_post_view, name="admin_publish_single_post"),

    # Custom Admin Index with Dashboard KPIs
    path("admin/", custom_admin_index),
    # Standard Admin
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
