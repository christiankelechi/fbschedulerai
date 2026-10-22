from django.core.management.base import BaseCommand
from publishing.tasks import publish_due_posts_task


class Command(BaseCommand):
    help = "Scans database for due scheduled posts and publishes them to Facebook."

    def handle(self, *args, **options):
        self.stdout.write("Scanning for due scheduled posts...")
        result = publish_due_posts_task()
        count = result.get('dispatched_count', 0)
        post_ids = result.get('post_ids', [])

        if count > 0:
            self.stdout.write(self.style.SUCCESS(f"Successfully dispatched {count} post(s) for publishing: {post_ids}"))
        else:
            self.stdout.write(self.style.NOTICE("No posts are currently due for publication."))
