from django.db import models
from content.models import GeneratedPost

class PublishingLog(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ]
    post = models.ForeignKey(GeneratedPost, on_delete=models.CASCADE, related_name='publishing_logs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    meta_post_id = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Log for Post {self.post.id} - {self.status}"

class MetaTokenVault(models.Model):
    """
    Secure vault for storing long-lived access tokens.
    In a fully productionized setup, these values would be encrypted in the DB.
    """
    page_id = models.CharField(max_length=255, unique=True)
    page_name = models.CharField(max_length=255)
    access_token = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.page_name
