from django.shortcuts import render
from django.utils import timezone
from content.models import GeneratedPost, ContentCategory, MediaAsset
from publishing.models import PublishingLog
import logging

logger = logging.getLogger(__name__)


def landing_page_view(request):
    """
    Public-facing landing page explaining the FBSchedulerAI architecture,
    daily autonomous Catholic devotional cadence, email review workflows,
    and system status.
    """
    now = timezone.now()
    
    # Safe database stat retrieval with fallbacks
    try:
        total_posts = GeneratedPost.objects.count()
        emailed_posts = GeneratedPost.objects.filter(is_emailed=True).count()
        facebook_posted = GeneratedPost.objects.filter(facebook_posted=True).count()
        total_media = MediaAsset.objects.count()
        
        latest_morning = GeneratedPost.objects.filter(
            category=ContentCategory.MORNING_PRAYER
        ).order_by("-created_at").first()
        
        latest_evening = GeneratedPost.objects.filter(
            category__in=[ContentCategory.EVENING_BIBLE_STUDY, ContentCategory.EVENING_REFLECTION]
        ).order_by("-created_at").first()
        
        db_connected = True
    except Exception as e:
        logger.warning(f"Landing page DB query fallback: {e}")
        total_posts = 0
        emailed_posts = 0
        facebook_posted = 0
        total_media = 0
        latest_morning = None
        latest_evening = None
        db_connected = False

    context = {
        "now": now,
        "total_posts": total_posts,
        "emailed_posts": emailed_posts,
        "facebook_posted": facebook_posted,
        "total_media": total_media,
        "latest_morning": latest_morning,
        "latest_evening": latest_evening,
        "db_connected": db_connected,
        "review_email": "christian.eze.241801@unn.edu.ng",
        "app_version": "2.4.0",
    }
    return render(request, "landing.html", context)

