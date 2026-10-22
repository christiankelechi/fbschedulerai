from django.db import models
from django.utils import timezone
from content.models import GeneratedPost


class PublishingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    SUCCESS = 'success', 'Success'
    FAILED = 'failed', 'Failed'
    RETRYING = 'retrying', 'Retrying'


class TokenVerificationStatus(models.TextChoices):
    VALID = 'valid', 'Valid & Active'
    INVALID = 'invalid', 'Invalid / Expired'
    UNVERIFIED = 'unverified', 'Unverified'


class MetaTokenVault(models.Model):
    """
    Secure vault for storing Facebook Page credentials, long-lived access tokens,
    and monitoring token validity.
    """
    page_name = models.CharField(max_length=255, help_text="Facebook Page display name (e.g. Rev. Fr. Ejiogu Chukwuemeka)")
    page_id = models.CharField(max_length=255, unique=True, help_text="Numeric Facebook Page ID")
    access_token = models.TextField(help_text="Never-Expiring Page Access Token")
    app_id = models.CharField(max_length=255, blank=True, default="", help_text="Meta App ID")
    app_secret = models.CharField(max_length=255, blank=True, default="", help_text="Meta App Secret")
    is_active = models.BooleanField(default=True, help_text="Designates this as the primary active publishing vault")
    verification_status = models.CharField(
        max_length=20,
        choices=TokenVerificationStatus.choices,
        default=TokenVerificationStatus.UNVERIFIED
    )
    last_verified_at = models.DateTimeField(null=True, blank=True)
    error_details = models.TextField(blank=True, default="", help_text="Details if token verification failed.")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-updated_at']
        verbose_name = 'Meta Token Vault'
        verbose_name_plural = 'Meta Token Vaults'

    def __str__(self):
        status_icon = "🟢" if self.verification_status == 'valid' else "🟡" if self.verification_status == 'unverified' else "🔴"
        return f"{status_icon} {self.page_name} (Page ID: {self.page_id})"


class PublishingLog(models.Model):
    post = models.ForeignKey(GeneratedPost, on_delete=models.CASCADE, related_name='publishing_logs')
    status = models.CharField(max_length=20, choices=PublishingStatus.choices, default=PublishingStatus.PENDING, db_index=True)
    endpoint_used = models.CharField(max_length=100, blank=True, default="", help_text="Graph API endpoint e.g. /{page-id}/feed, /{page-id}/photos, /{page-id}/video_reels")
    meta_post_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID returned by Meta Graph API")
    request_payload = models.TextField(blank=True, default="", help_text="Sanitized request summary")
    response_payload = models.TextField(blank=True, default="", help_text="Full response or error JSON from Meta")
    error_message = models.TextField(blank=True, default="")
    retry_count = models.IntegerField(default=0)
    duration_ms = models.IntegerField(default=0, help_text="Publishing roundtrip latency in ms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Publishing Log'
        verbose_name_plural = 'Publishing Logs'

    def __str__(self):
        return f"Log #{self.id} | Post #{self.post_id} | {self.get_status_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
