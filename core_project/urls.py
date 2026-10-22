from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core_project.admin_views import (
    trigger_generation_view,
    trigger_publish_due_view,
    trigger_publish_single_post_view,
    trigger_verify_token_view,
)


def custom_admin_index(request):
    """
    Supplies rich dashboard statistics, live media galleries, and recent audit logs
    to the customized Django admin index view.
    """
    from content.models import GeneratedPost, MediaAsset, PostStatus
    from publishing.models import PublishingLog, MetaTokenVault

    total_posts = GeneratedPost.objects.count()
    scheduled_posts = GeneratedPost.objects.filter(status=PostStatus.SCHEDULED).count()
    published_posts = GeneratedPost.objects.filter(is_published=True).count()
    failed_posts = GeneratedPost.objects.filter(status=PostStatus.FAILED).count()
    recent_posts = GeneratedPost.objects.select_related('media').order_by('-created_at')[:8]
    recent_logs = PublishingLog.objects.select_related('post').order_by('-created_at')[:8]
    active_vault = MetaTokenVault.objects.filter(is_active=True).first()

    context = {
        'total_posts': total_posts,
        'scheduled_posts': scheduled_posts,
        'published_posts': published_posts,
        'failed_posts': failed_posts,
        'recent_posts': recent_posts,
        'recent_logs': recent_logs,
        'active_vault': active_vault,
        'title': 'Rev. Fr. Ejiogu FB Content Scheduler Dashboard',
    }
    return admin.site.index(request, extra_context=context)


urlpatterns = [
    # Dashboard quick action routes
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
