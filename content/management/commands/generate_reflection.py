from django.core.management.base import BaseCommand
from django.utils import timezone
from content.models import ContentCategory, PostType
from content.services.orchestrator import ContentPipelineOrchestrator
from publishing.services.publisher import PostPublisher


class Command(BaseCommand):
    help = "Generates a Catholic reflection post (Quote Card or Vertical Reel) using the zero-cost pipeline."

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            default=ContentCategory.DAILY_REFLECTION,
            choices=[c[0] for c in ContentCategory.choices],
            help="Content category (e.g. morning_prayer, daily_reflection, evening_reflection)"
        )
        parser.add_argument(
            '--type',
            type=str,
            default=PostType.IMAGE_QUOTE,
            choices=[t[0] for t in PostType.choices],
            help="Post media type (image_quote, vertical_reel, text_only)"
        )
        parser.add_argument(
            '--delay-hours',
            type=int,
            default=1,
            help="Hours in advance to schedule publication"
        )
        parser.add_argument(
            '--publish-now',
            action='store_true',
            help="Publish immediately to Meta instead of waiting for scheduled time."
        )

    def handle(self, *args, **options):
        category = options['category']
        post_type = options['type']
        delay_hours = options['delay_hours']
        publish_now = options['publish_now']

        self.stdout.write(f"Generating reflection: category={category}, type={post_type}...")

        orchestrator = ContentPipelineOrchestrator()
        target_time = timezone.now() + timezone.timedelta(hours=delay_hours)

        post = orchestrator.generate_post(
            category=category,
            post_type=post_type,
            scheduled_time=target_time
        )

        self.stdout.write(self.style.SUCCESS(f"Post #{post.id} created successfully!"))
        self.stdout.write(f"Title: {post.title}")
        self.stdout.write(f"Scripture: {post.scripture_citation}")
        if post.media:
            self.stdout.write(f"Media: {post.media.get_asset_type_display()} -> {post.media.file_path.name}")

        if publish_now:
            self.stdout.write("Publishing immediately to Meta Graph API...")
            publisher = PostPublisher()
            log = publisher.publish(post)
            if log.status == 'success':
                self.stdout.write(self.style.SUCCESS(f"Successfully published to Facebook! (Meta ID: {log.meta_post_id})"))
            else:
                self.stdout.write(self.style.ERROR(f"Publishing failed: {log.error_message}"))
