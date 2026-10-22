from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import PublishingLog, MetaTokenVault, PublishingStatus, TokenVerificationStatus
from publishing.services.meta_client import MetaGraphClient


@admin.register(MetaTokenVault)
class MetaTokenVaultAdmin(admin.ModelAdmin):
    list_display = ('page_name', 'page_id', 'verification_badge', 'is_active', 'last_verified_at', 'updated_at')
    list_filter = ('verification_status', 'is_active')
    search_fields = ('page_name', 'page_id', 'app_id')
    readonly_fields = ('last_verified_at', 'created_at', 'updated_at')
    actions = ['verify_selected_tokens']

    def verification_badge(self, obj):
        colors = {
            TokenVerificationStatus.VALID: ('#10b981', 'Valid & Active'),
            TokenVerificationStatus.INVALID: ('#ef4444', 'Invalid / Expired'),
            TokenVerificationStatus.UNVERIFIED: ('#f59e0b', 'Unverified'),
        }
        color, text = colors.get(obj.verification_status, ('#64748b', 'Unknown'))
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">{}</span>',
            color, text
        )
    verification_badge.short_description = "Token Health"

    @admin.action(description="🔍 Verify selected tokens with Meta Graph API")
    def verify_selected_tokens(self, request, queryset):
        for vault in queryset:
            client = MetaGraphClient(page_id=vault.page_id, access_token=vault.access_token)
            res = client.verify_token()
            if res.get('valid'):
                self.message_user(request, f"Token for {vault.page_name} is VALID!", messages.SUCCESS)
            else:
                self.message_user(request, f"Token for {vault.page_name} failed: {res.get('message')}", messages.ERROR)


@admin.register(PublishingLog)
class PublishingLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'post_link',
        'status_badge',
        'endpoint_used',
        'meta_post_id',
        'retry_count',
        'duration_display',
        'created_at'
    )
    list_filter = ('status', 'endpoint_used', 'created_at')
    search_fields = ('meta_post_id', 'error_message', 'request_payload', 'response_payload')
    readonly_fields = (
        'post',
        'status',
        'endpoint_used',
        'meta_post_id',
        'duration_ms',
        'retry_count',
        'error_message',
        'request_payload',
        'response_payload',
        'created_at',
        'updated_at'
    )

    def post_link(self, obj):
        if obj.post:
            return format_html(
                '<a href="/admin/content/generatedpost/{}/change/">Post #{} ({})</a>',
                obj.post.id, obj.post.id, obj.post.title or obj.post.caption[:25]
            )
        return "-"
    post_link.short_description = "Target Post"

    def status_badge(self, obj):
        colors = {
            PublishingStatus.SUCCESS: ('#10b981', 'Success'),
            PublishingStatus.FAILED: ('#ef4444', 'Failed'),
            PublishingStatus.IN_PROGRESS: ('#3b82f6', 'In Progress'),
            PublishingStatus.PENDING: ('#64748b', 'Pending'),
            PublishingStatus.RETRYING: ('#f59e0b', 'Retrying'),
        }
        color, text = colors.get(obj.status, ('#64748b', obj.status))
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">{}</span>',
            color, text
        )
    status_badge.short_description = "Status"

    def duration_display(self, obj):
        return f"{obj.duration_ms} ms"
    duration_display.short_description = "Latency"
