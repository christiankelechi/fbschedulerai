import time
import json
import logging
from typing import Optional, Dict, Any
import requests
from django.conf import settings
from django.utils import timezone
from content.models import GeneratedPost, ContentCategory, PostType, PostStatus
from publishing.models import PublishingLog, PublishingStatus

logger = logging.getLogger(__name__)


class EmailDispatchError(Exception):
    """Custom exception raised when email dispatch via Zenia fails."""
    pass


class ZeniaEmailService:
    """
    Dedicated Email Service forwarding curated pastoral content to Engr. Christian Kelechi Eze
    for editorial review prior to manual Facebook posting.
    
    Powered by the Zenia Email Provider API endpoint:
    https://zenia-email-api.vercel.app/api/v1/register_email
    """

    DEFAULT_API_URL = "https://zenia-email-api.vercel.app/api/v1/register_email"
    DEFAULT_RECIPIENT = "christian.eze.241801@unn.edu.ng"

    def __init__(self, api_url: Optional[str] = None, default_recipient: Optional[str] = None):
        self.api_url = api_url or getattr(settings, 'ZENIA_EMAIL_API_URL', self.DEFAULT_API_URL)
        self.default_recipient = default_recipient or getattr(settings, 'REVIEW_EMAIL', self.DEFAULT_RECIPIENT)

    def send_post_for_review(
        self,
        post: GeneratedPost,
        recipient: Optional[str] = None,
        timeout: int = 15
    ) -> PublishingLog:
        """
        Formats and dispatches the post content to Christian's email.
        Records an audit log in PublishingLog and marks the post as emailed.
        """
        start_time = time.time()
        target_email = recipient or self.default_recipient
        logger.info(f"[EmailService] Preparing review dispatch for Post #{post.id} to {target_email}")

        # 1. Build Email Subject, Title, and Text Payload
        subject, email_title = self._build_subject_and_title(post)
        message_text = self._build_message_body(post)

        payload = {
            "userEmail": target_email,
            "text": message_text,
            "subject": subject,
            "title": email_title,
        }

        # 2. Initialize Audit Log
        log = PublishingLog(
            post=post,
            channel='email',
            recipient=target_email,
            endpoint_used="/api/v1/register_email",
            status=PublishingStatus.IN_PROGRESS,
            request_payload=json.dumps({
                "recipient": target_email,
                "subject": subject,
                "title": email_title,
                "post_id": post.id,
                "category": post.category,
            })
        )

        try:
            # 3. Dispatch POST request to Zenia Email API
            response = requests.post(
                url=self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            duration_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                logger.info(f"[EmailService] Successfully emailed Post #{post.id} to {target_email} in {duration_ms}ms")
                log.status = PublishingStatus.SUCCESS
                log.response_payload = response.text
                log.duration_ms = duration_ms
                log.save()

                # 4. Mark Post as Emailed
                post.mark_as_emailed(recipient=target_email)
                return log
            else:
                err_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"[EmailService] Failed to email Post #{post.id}: {err_msg}")
                log.status = PublishingStatus.FAILED
                log.response_payload = response.text
                log.error_message = err_msg
                log.duration_ms = duration_ms
                log.save()
                raise EmailDispatchError(err_msg)

        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[EmailService] Exception during email dispatch for Post #{post.id}: {exc}", exc_info=True)
            log.status = PublishingStatus.FAILED
            log.error_message = str(exc)
            log.duration_ms = duration_ms
            log.save()
            raise EmailDispatchError(str(exc)) from exc

    def test_connection(self, recipient: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends a live test verification ping to Christian's email.
        """
        target_email = recipient or self.default_recipient
        now_str = timezone.now().strftime("%B %d, %Y at %I:%M %p WAT")
        payload = {
            "userEmail": target_email,
            "title": "Zenia Email Channel Active • FbScheduler AI",
            "subject": f"🟢 System Test Verification — {now_str}",
            "text": (
                f"Hello Engr. Christian Kelechi Eze,\n\n"
                f"This is an automated health check confirming that your Zenia Email Provider integration "
                f"is online and fully operational.\n\n"
                f"• Target Reviewer: {target_email}\n"
                f"• Server Time: {now_str}\n"
                f"• Morning 3:00 AM & Evening Bible Study dispatches will arrive at this address.\n\n"
                f"Blessings,\n"
                f"Rev. Fr. Ejiogu Chukwuemeka Content Engine"
            )
        }
        res = requests.post(url=self.api_url, json=payload, timeout=12)
        return {
            "status_code": res.status_code,
            "response": res.text,
            "recipient": target_email,
            "success": res.status_code == 200
        }

    def _build_subject_and_title(self, post: GeneratedPost) -> tuple[str, str]:
        date_str = timezone.now().strftime("%b %d, %Y")
        
        if post.category == ContentCategory.MORNING_PRAYER:
            subject = f"🌅 [3:00 AM Review] Morning Prayer & Reflection — {date_str}"
            title = "Morning Reflection Ready for Review & Facebook Posting"
        elif post.category == ContentCategory.EVENING_BIBLE_STUDY:
            subject = f"📖 [Evening Review] Evening Bible Study — {date_str}"
            title = "Evening Bible Study Ready for Review & Facebook Posting"
        elif post.category == ContentCategory.EVENING_REFLECTION:
            subject = f"🕊 [Evening Review] Evening Reflection & Examen — {date_str}"
            title = "Evening Reflection Ready for Review & Facebook Posting"
        elif post.category == ContentCategory.SUNDAY_HOMILY:
            subject = f"⛪ [Sunday Homily] Sunday Reflection — {date_str}"
            title = "Sunday Homily Thought Ready for Review & Facebook Posting"
        else:
            subject = f"✨ [Editorial Review] Daily Catholic Reflection: {post.title or date_str}"
            title = "Daily Pastoral Reflection Ready for Review"

        return subject, title

    def _build_message_body(self, post: GeneratedPost) -> str:
        date_str = timezone.now().strftime("%A, %B %d, %Y")
        media_info = "None (Text Only)"
        media_url_line = ""
        if post.media and post.media.file_path:
            media_info = f"{post.media.get_asset_type_display()} ({post.media.file_path.name})"
            url = post.media.file_path.url
            if url.startswith("http://") or url.startswith("https://"):
                media_url_line = (
                    f"☁️ Cloudinary Image Link (Click to View/Download for Facebook):\n"
                    f"   👉 {url}\n"
                )

        lines = [
            "✝ REV. FR. EJIOGU CHUKWUEMEKA — SOCIAL MEDIA EDITORIAL REVIEW",
            f"Date: {date_str}",
            f"Category: {post.get_category_display()} | Type: {post.get_post_type_display()} | Post ID: #{post.id}",
            "────────────────────────────────────────────────────────",
            "",
            "Dear Engr. Christian,",
            "",
            "The backend engine has curated and stored this reflection for Rev. Fr. Ejiogu Chukwuemeka's Facebook Page.",
            "Please review the formatted text below, copy it, and publish to Facebook with the corresponding graphic.",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📌 THEME / TITLE: {post.title or 'Daily Liturgical Reflection'}",
            f"📖 SCRIPTURE CITATION: {post.scripture_citation or 'Scripture Selection'}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "📝 FULL FACEBOOK POST COPY (Ready to Copy & Paste):",
            "────────────────────────────────────────────────────────",
            post.full_published_text,
            "────────────────────────────────────────────────────────",
            "",
            f"🎨 MEDIA ARTIFACT: {media_info}",
        ]

        if media_url_line:
            lines.append(media_url_line)

        lines.extend([
            "Media files can also be previewed, downloaded, and managed from your Django Admin Dashboard:",
            "👉 http://127.0.0.1:8000/admin/",
            "",
            "✅ WORKFLOW CHECKLIST:",
            "1. Review the caption and make any pastoral or editorial adjustments.",
            "2. Download or attach the graphic above and publish to Rev. Fr. Ejiogu Chukwuemeka's official Facebook Page.",
            "3. Return to the Admin Dashboard and click 'Mark as Posted to Facebook' to keep today's monitoring status updated.",
            "",
            "Blessings,",
            "Autonomous Catholic Content Scheduler"
        ])
        return "\n".join(lines)

