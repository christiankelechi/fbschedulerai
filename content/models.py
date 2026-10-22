from django.db import models
from django.utils import timezone
from django.utils.html import format_html


class ContentCategory(models.TextChoices):
    MORNING_PRAYER = 'morning_prayer', 'Morning Prayer'
    DAILY_REFLECTION = 'daily_reflection', 'Daily Reflection'
    EVENING_REFLECTION = 'evening_reflection', 'Evening Reflection'
    SCRIPTURE = 'scripture', 'Scripture Thought'
    SAINT_OF_THE_DAY = 'saint_of_the_day', 'Saint of the Day'
    SUNDAY_HOMILY = 'sunday_homily', 'Sunday Homily Thought'


class PostType(models.TextChoices):
    TEXT_ONLY = 'text_only', 'Text Feed Post'
    IMAGE_QUOTE = 'image_quote', 'Image Quote Card'
    VERTICAL_REEL = 'vertical_reel', 'Vertical Video Reel (9:16)'


class PostStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    SCHEDULED = 'scheduled', 'Scheduled'
    PUBLISHING = 'publishing', 'Publishing In Progress'
    PUBLISHED = 'published', 'Published'
    FAILED = 'failed', 'Failed'


class ContentPrompt(models.Model):
    category = models.CharField(
        max_length=50,
        choices=ContentCategory.choices,
        default=ContentCategory.DAILY_REFLECTION,
        help_text="Liturgical or thematic category for the prompt."
    )
    title = models.CharField(
        max_length=255,
        default="Standard Catholic Reflection Prompt",
        help_text="Descriptive title for this prompt template."
    )
    prompt_text = models.TextField(
        help_text="The prompt template sent to the zero-cost LLM (supports {category}, {date}, etc.)."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this prompt is eligible to be selected for scheduled runs."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Content Prompt'
        verbose_name_plural = 'Content Prompts'

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"


class MediaAsset(models.Model):
    ASSET_TYPES = [
        ('image', 'Image Quote Card'),
        ('video', 'Vertical Video Reel (9:16)'),
        ('audio', 'Voiceover Audio (TTS)'),
    ]

    title = models.CharField(max_length=255, blank=True, default="")
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default='image')
    file_path = models.FileField(upload_to='generated_media/%Y/%m/%d/')
    thumbnail = models.ImageField(upload_to='generated_media/thumbnails/%Y/%m/%d/', blank=True, null=True)
    duration_seconds = models.FloatField(blank=True, null=True, help_text="Duration in seconds (for audio/video).")
    aspect_ratio = models.CharField(max_length=20, default='1:1', help_text="e.g. 1:1, 9:16, 4:5")
    transcript = models.TextField(blank=True, default="", help_text="Transcript or overlaid text.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media Asset'
        verbose_name_plural = 'Media Assets'

    def __str__(self):
        return f"{self.get_asset_type_display()} - {self.title or self.file_path.name}"

    @property
    def preview_html(self):
        if not self.file_path:
            return "No file"
        url = self.file_path.url
        if self.asset_type == 'image':
            return format_html('<img src="{}" style="max-height: 120px; border-radius: 8px; border: 1px solid #ccc;" />', url)
        elif self.asset_type == 'video':
            return format_html(
                '<video src="{}" style="max-height: 180px; border-radius: 8px;" controls preload="metadata"></video>',
                url
            )
        elif self.asset_type == 'audio':
            return format_html(
                '<audio src="{}" controls style="width: 220px;"></audio>',
                url
            )
        return url


class GeneratedPost(models.Model):
    title = models.CharField(max_length=255, blank=True, default="", help_text="Editorial title / theme of the post.")
    category = models.CharField(
        max_length=50,
        choices=ContentCategory.choices,
        default=ContentCategory.DAILY_REFLECTION
    )
    post_type = models.CharField(
        max_length=30,
        choices=PostType.choices,
        default=PostType.IMAGE_QUOTE
    )
    prompt = models.ForeignKey(
        ContentPrompt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    caption = models.TextField(
        help_text="Primary post copy / reflection caption published to Facebook."
    )
    scripture_citation = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Scripture reference (e.g. Matthew 11:28-30)."
    )
    hashtags = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Curated hashtags separated by spaces."
    )
    media = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
        db_index=True
    )
    scheduled_time = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Target publishing timestamp."
    )
    is_published = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Quick boolean flag indicating published state."
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual timestamp when successfully published via Meta API."
    )
    meta_post_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Returned Meta Graph API Post / Video / Reel ID."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_time', '-created_at']
        verbose_name = 'Generated Post'
        verbose_name_plural = 'Generated Posts'

    def __str__(self):
        time_str = self.scheduled_time.strftime('%Y-%m-%d %H:%M') if self.scheduled_time else 'Unscheduled'
        return f"[{self.get_status_display()}] {self.title or self.caption[:40]} ({time_str})"

    @property
    def full_published_text(self):
        parts = [self.caption.strip()]
        if self.scripture_citation:
            parts.append(f"\n📖 Scripture: {self.scripture_citation.strip()}")
        parts.append("\nRev. Fr. Ejiogu Chukwuemeka")
        if self.hashtags:
            parts.append(f"\n{self.hashtags.strip()}")
        return "\n".join(parts)
