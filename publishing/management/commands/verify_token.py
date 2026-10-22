from django.core.management.base import BaseCommand
from publishing.services.meta_client import MetaGraphClient


class Command(BaseCommand):
    help = "Verifies Facebook Page Access Token and permissions against Meta Graph API."

    def handle(self, *args, **options):
        self.stdout.write("Connecting to Meta Graph API to verify token...")
        client = MetaGraphClient()

        if not client.is_configured():
            self.stdout.write(self.style.WARNING(
                "Meta credentials are not configured in .env or MetaTokenVault. "
                "The system is currently operating in mock simulation mode."
            ))
            return

        result = client.verify_token()
        if result.get('valid'):
            self.stdout.write(self.style.SUCCESS(
                f"Token is VALID! Connected to Page: '{result.get('page_name')}' (Page ID: {result.get('page_id')})"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"Token verification failed: {result.get('message')}"
            ))
