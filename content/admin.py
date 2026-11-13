from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.utils import timezone
from .models import ContentPrompt, MediaAsset, GeneratedPost, PostStatus
from content.services.email_service import ZeniaEmailService
from publishing.services.publisher import PostPublisher


@admin.register(ContentPrompt)
class ContentPromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'is_active', 'created_at', 'updated_at')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'prompt_text')
    actions = ['activate_prompts', 'deactivate_prompts']

    @admin.action(description="Activate selected prompts")
    def activate_prompts(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Selected prompts activated.", messages.SUCCESS)

    @admin.action(description="Deactivate selected prompts")
    def deactivate_prompts(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected prompts deactivated.", messages.WARNING)


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'preview_thumbnail', 'title', 'asset_type', 'aspect_ratio', 'duration_seconds', 'created_at')
    list_filter = ('asset_type', 'aspect_ratio')
    search_fields = ('title', 'transcript', 'file_path')
    readonly_fields = ('preview_large', 'created_at')

    def preview_thumbnail(self, obj):
        if not obj.file_path:
            return "-"
        if obj.thumbnail:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px;" />', obj.thumbnail.url)
        elif obj.asset_type == 'image':
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px;" />', obj.file_path.url)
        elif obj.asset_type == 'video':
            return format_html('<span style="background: #2563eb; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 11px;">🎬 Video Reel</span>')
        elif obj.asset_type == 'audio':
            return format_html('<span style="background: #7c3aed; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 11px;">🎙 Audio</span>')
        return "-"
    preview_thumbnail.short_description = "Preview"

    def preview_large(self, obj):
        if not obj.file_path:
            return "No media file uploaded"
        url = obj.file_path.url
        if obj.asset_type == 'image':
            return format_html('<img src="{}" style="max-height: 400px; border-radius: 8px; border: 1px solid #cbd5e1;" />', url)
        elif obj.asset_type == 'video':
            return format_html('<video src="{}" style="max-height: 480px; border-radius: 8px;" controls></video>', url)
        elif obj.asset_type == 'audio':
            return format_html('<audio src="{}" controls style="width: 320px;"></audio>', url)
        return url
    preview_large.short_description = "Live Interactive Preview"


@admin.register(GeneratedPost)
class GeneratedPostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'media_preview',
        'title',
        'category',
        'post_type',
        'email_status_badge',
        'facebook_status_badge',
        'quick_actions',
        'created_at'
    )
    list_filter = (
        'facebook_posted',
        'is_emailed',
        'category',
        'post_type',
        'status',
        'created_at'
    )
    search_fields = ('title', 'caption', 'scripture_citation', 'hashtags', 'email_recipient')
    readonly_fields = (
        'media_detail_preview',
        'full_copyable_post',
        'created_at',
        'updated_at',
        'emailed_at',
        'facebook_posted_at',
        'published_at'
    )
    actions = [
        'mark_selected_as_posted',
        'unmark_selected_as_posted',
        'send_email_review_selected',
        'publish_selected_posts'
    ]

    def media_preview(self, obj):
        if not obj.media or not obj.media.file_path:
            return format_html('<span style="color: #94a3b8; font-size: 11px;">No Media</span>')
        if obj.media.thumbnail:
            return format_html('<img src="{}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 6px;" />', obj.media.thumbnail.url)
        elif obj.media.asset_type == 'image':
            return format_html('<img src="{}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 6px;" />', obj.media.file_path.url)
        elif obj.media.asset_type == 'video':
            return format_html('<span style="background: #1e293b; color: #e2e8f0; padding: 4px 6px; border-radius: 4px; font-size: 11px;">🎬 9:16</span>')
        return "-"
    media_preview.short_description = "Media"

    def email_status_badge(self, obj):
        if obj.is_emailed:
            time_str = obj.emailed_at.strftime('%H:%M') if obj.emailed_at else ""
            return format_html(
                '<span style="background-color: #0284c7; color: #fff; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">'
                '📧 Emailed {}</span>',
                time_str
            )
        return format_html(
            '<span style="background-color: #64748b; color: #fff; padding: 3px 8px; border-radius: 6px; font-size: 11px;">'
            '⚪ Not Sent</span>'
        )
    email_status_badge.short_description = "Email Review"

    def facebook_status_badge(self, obj):
        if obj.facebook_posted:
            time_str = obj.facebook_posted_at.strftime('%b %d, %H:%M') if obj.facebook_posted_at else ""
            return format_html(
                '<span style="background-color: #10b981; color: #fff; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700;">'
                '✅ Posted ({})</span>',
                time_str
            )
        return format_html(
            '<span style="background-color: #f59e0b; color: #000; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700;">'
            '⏳ Pending Post</span>'
        )
    facebook_status_badge.short_description = "Facebook Status"

    def quick_actions(self, obj):
        if obj.facebook_posted:
            return format_html(
                '<a href="/admin/action/posts/{}/unmark-posted/" style="background: #f1f5f9; color: #475569; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 600;">↩️ Unmark</a> '
                '<a href="/admin/action/posts/{}/send-email/" style="background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 600;">📧 Resend</a>',
                obj.id, obj.id
            )
        return format_html(
            '<a href="/admin/action/posts/{}/mark-posted/" style="background: #10b981; color: #fff; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 700;">✅ Mark Posted</a> '
            '<a href="/admin/action/posts/{}/send-email/" style="background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 600;">📧 Email</a>',
            obj.id, obj.id
        )
    quick_actions.short_description = "Quick Actions"

    def full_copyable_post(self, obj):
        text = obj.full_published_text
        return format_html(
            '<textarea style="width: 100%; height: 180px; font-family: monospace; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1;" readonly>{}</textarea>',
            text
        )
    full_copyable_post.short_description = "Complete Facebook Post Copy (Ready to Paste)"

    def media_detail_preview(self, obj):
        if not obj.media:
            return "No media asset linked."
        return obj.media.preview_html
    media_detail_preview.short_description = "Attached Media Preview"

    @admin.action(description="✅ Mark selected posts as Posted to Facebook")
    def mark_selected_as_posted(self, request, queryset):
        for post in queryset:
            post.mark_as_facebook_posted()
        self.message_user(request, f"Marked {queryset.count()} post(s) as Posted to Facebook!", messages.SUCCESS)

    @admin.action(description="↩️ Unmark selected posts (Revert to Pending Facebook Post)")
    def unmark_selected_as_posted(self, request, queryset):
        for post in queryset:
            post.unmark_as_facebook_posted()
        self.message_user(request, f"Reverted {queryset.count()} post(s) to Pending.", messages.INFO)

    @admin.action(description="📧 Forward selected posts to Christian Eze's Email (Zenia)")
    def send_email_review_selected(self, request, queryset):
        email_svc = ZeniaEmailService()
        success = 0
        for post in queryset:
            try:
                email_svc.send_post_for_review(post)
                success += 1
            except Exception as e:
                self.message_user(request, f"Failed to email Post #{post.id}: {e}", messages.ERROR)
        if success:
            self.message_user(request, f"Successfully emailed {success} post(s) for review!", messages.SUCCESS)

    @admin.action(description="🚀 Publish selected posts via Meta Graph API")
    def publish_selected_posts(self, request, queryset):
        publisher = PostPublisher()
        success_count = 0
        for post in queryset:
            log = publisher.publish(post)
            if log.status == 'success':
                success_count += 1
        self.message_user(request, f"Dispatched {success_count} post(s) to Meta.", messages.SUCCESS)
