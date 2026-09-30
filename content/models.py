from django.db import models

class ContentPrompt(models.fields.Field):
    pass # Wait, let's just make models

class ContentPrompt(models.Model):
    category = models.CharField(max_length=100, choices=[
        ('morning_prayer', 'Morning Prayer'),
        ('evening_reflection', 'Evening Reflection'),
        ('scripture', 'Scripture Thought')
    ])
    prompt_text = models.TextField(help_text="The prompt template sent to the LLM")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} Prompt ({self.id})"

class MediaAsset(models.fields.Field):
    pass

class MediaAsset(models.Model):
    ASSET_TYPES = [
        ('image', 'Image Quote Card'),
        ('video', 'Vertical Video Reel'),
        ('audio', 'Voiceover Audio')
    ]
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    file_path = models.FileField(upload_to='generated_media/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_asset_type_display()} - {self.file_path.name}"

class GeneratedPost(models.Model):
    prompt = models.ForeignKey(ContentPrompt, on_delete=models.SET_NULL, null=True)
    caption = models.TextField()
    scripture_citation = models.CharField(max_length=255, blank=True)
    hashtags = models.CharField(max_length=255, blank=True)
    media = models.ForeignKey(MediaAsset, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata for scheduling
    scheduled_time = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post scheduled for {self.scheduled_time} ({'Published' if self.is_published else 'Pending'})"
