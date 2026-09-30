from django.contrib import admin
from .models import ContentPrompt, MediaAsset, GeneratedPost

@admin.register(ContentPrompt)
class ContentPromptAdmin(admin.ModelAdmin):
    list_display = ('category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('prompt_text',)

@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('asset_type', 'file_path', 'created_at')
    list_filter = ('asset_type',)

@admin.register(GeneratedPost)
class GeneratedPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'prompt', 'scheduled_time', 'is_published', 'created_at')
    list_filter = ('is_published', 'scheduled_time')
    search_fields = ('caption', 'scripture_citation')
