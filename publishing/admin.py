from django.contrib import admin
from .models import PublishingLog, MetaTokenVault

@admin.register(PublishingLog)
class PublishingLogAdmin(admin.ModelAdmin):
    list_display = ('post', 'status', 'retry_count', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('error_message', 'meta_post_id')

@admin.register(MetaTokenVault)
class MetaTokenVaultAdmin(admin.ModelAdmin):
    list_display = ('page_name', 'page_id', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('page_name', 'page_id')
