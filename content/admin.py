from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import ContentPrompt, MediaAsset, GeneratedPost, PostStatus
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
        'status_badge',
        'scheduled_time',
        'is_published',
        'meta_post_id',
        'created_at'
    )
    list_filter = ('status', 'category', 'post_type', 'is_published', 'scheduled_time')
    search_fields = ('title', 'caption', 'scripture_citation', 'hashtags', 'meta_post_id')
    readonly_fields = ('media_detail_preview', 'created_at', 'updated_at', 'published_at')
    actions = ['publish_selected_posts', 'mark_as_scheduled', 'mark_as_draft']

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

    def status_badge(self, obj):
        colors = {
            PostStatus.PUBLISHED: ('#10b981', '#ffffff'),
            PostStatus.SCHEDULED: ('#f59e0b', '#000000'),
            PostStatus.FAILED: ('#ef4444', '#ffffff'),
            PostStatus.PUBLISHING: ('#3b82f6', '#ffffff'),
            PostStatus.DRAFT: ('#64748b', '#ffffff'),
        }
        bg, fg = colors.get(obj.status, ('#64748b', '#ffffff'))
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def media_detail_preview(self, obj):
        if not obj.media:
            return "No media asset linked."
        return obj.media.preview_html
    media_detail_preview.short_description = "Attached Media Preview"

    @admin.action(description="🚀 Publish selected posts to Facebook now")
    def publish_selected_posts(self, request, queryset):
        publisher = PostPublisher()
        success_count = 0
        fail_count = 0

        for post in queryset:
            log = publisher.publish(post)
            if log.status == 'success':
                success_count += 1
            else:
                fail_count += 1

        if success_count:
            self.message_user(request, f"Successfully published {success_count} post(s) to Facebook!", messages.SUCCESS)
        if fail_count:
            self.message_user(request, f"Failed to publish {fail_count} post(s). Check logs for details.", messages.ERROR)

    @admin.action(description="Mark selected posts as Scheduled")
    def mark_as_scheduled(self, request, queryset):
        queryset.update(status=PostStatus.SCHEDULED)
        self.message_user(request, "Selected posts marked as Scheduled.", messages.SUCCESS)

    @admin.action(description="Mark selected posts as Draft")
    def mark_as_draft(self, request, queryset):
        queryset.update(status=PostStatus.DRAFT)
        self.message_user(request, "Selected posts marked as Draft.", messages.SUCCESS)
