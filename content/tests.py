from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from content.models import GeneratedPost, ContentCategory, PostType, PostStatus
from content.services.email_service import ZeniaEmailService
from content.services.orchestrator import ContentPipelineOrchestrator
from core_project.urls import custom_admin_index


class ZeniaEmailServiceTestCase(TestCase):
    def setUp(self):
        self.post = GeneratedPost.objects.create(
            title="Test Morning Reflection",
            category=ContentCategory.MORNING_PRAYER,
            post_type=PostType.IMAGE_QUOTE,
            caption="Lord, guide our steps today.",
            scripture_citation="Psalm 119:105",
            hashtags="#MorningPrayer #Catholic",
            status=PostStatus.DRAFT
        )

    def test_message_body_formatting(self):
        svc = ZeniaEmailService()
        body = svc._build_message_body(self.post)
        self.assertIn("REV. FR. EJIOGU CHUKWUEMEKA", body)
        self.assertIn("Psalm 119:105", body)
        self.assertIn("Lord, guide our steps today.", body)
        self.assertIn("#MorningPrayer", body)

    @patch("requests.post")
    def test_send_post_for_review_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"msg": "You should receive an email from us"}'
        mock_post.return_value = mock_resp

        svc = ZeniaEmailService()
        log = svc.send_post_for_review(self.post, recipient="christian.eze.241801@unn.edu.ng")

        self.post.refresh_from_db()
        self.assertTrue(self.post.is_emailed)
        self.assertEqual(self.post.status, PostStatus.EMAILED)
        self.assertEqual(self.post.email_recipient, "christian.eze.241801@unn.edu.ng")
        self.assertEqual(log.status, 'success')


class GeneratedPostModelTestCase(TestCase):
    def setUp(self):
        self.post = GeneratedPost.objects.create(
            title="Faith and Hope",
            category=ContentCategory.EVENING_BIBLE_STUDY,
            post_type=PostType.IMAGE_QUOTE,
            caption="Let us walk by faith.",
            scripture_citation="2 Corinthians 5:7",
            status=PostStatus.DRAFT
        )

    def test_mark_and_unmark_facebook_posted(self):
        # 1. Mark as posted
        self.post.mark_as_facebook_posted(post_url="https://facebook.com/posts/123")
        self.post.refresh_from_db()
        self.assertTrue(self.post.facebook_posted)
        self.assertTrue(self.post.is_published)
        self.assertEqual(self.post.status, PostStatus.PUBLISHED)
        self.assertEqual(self.post.facebook_post_url, "https://facebook.com/posts/123")
        self.assertIsNotNone(self.post.facebook_posted_at)

        # 2. Unmark
        self.post.unmark_as_facebook_posted()
        self.post.refresh_from_db()
        self.assertFalse(self.post.facebook_posted)
        self.assertFalse(self.post.is_published)
        self.assertIsNone(self.post.facebook_posted_at)


class AdminDashboardViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123'
        )
        self.factory = RequestFactory()

    def test_custom_admin_index_rendering(self):
        request = self.factory.get('/admin/')
        request.user = self.user

        response = custom_admin_index(request)
        response.render()

        self.assertEqual(response.status_code, 200)
        content_str = response.content.decode('utf-8')
        self.assertIn("Today's Facebook Posting Compliance Tracker", content_str)
        self.assertIn("christian.eze.241801@unn.edu.ng", content_str)
        self.assertIn("Rev. Fr. Ejiogu Chukwuemeka", content_str)
