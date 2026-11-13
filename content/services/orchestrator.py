import logging
from datetime import datetime
from typing import Optional
from django.utils import timezone
from content.models import GeneratedPost, ContentPrompt, MediaAsset, ContentCategory, PostType, PostStatus
from .llm_service import LLMService, ReflectionOutput
from .image_service import QuoteCardGenerator
from .tts_service import TTSService
from .video_service import ReelVideoGenerator
from .email_service import ZeniaEmailService

logger = logging.getLogger(__name__)


class ContentPipelineOrchestrator:
    """
    High-level orchestrator for autonomous content ideation, media synthesis,
    and editorial review dispatching via Zenia Email.
    Integrates LLM text generation, Quote Card design, TTS voiceover synthesis,
    and Reel video assembly into a unified OOP workflow.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        image_generator: Optional[QuoteCardGenerator] = None,
        tts_service: Optional[TTSService] = None,
        video_generator: Optional[ReelVideoGenerator] = None,
        email_service: Optional[ZeniaEmailService] = None
    ):
        self.llm = llm_service or LLMService()
        self.image_gen = image_generator or QuoteCardGenerator()
        self.tts = tts_service or TTSService()
        self.video_gen = video_generator or ReelVideoGenerator()
        self.email_service = email_service or ZeniaEmailService()

    def generate_post(
        self,
        category: str = ContentCategory.DAILY_REFLECTION,
        post_type: str = PostType.IMAGE_QUOTE,
        scheduled_time: Optional[datetime] = None,
        custom_instructions: Optional[str] = None,
        prompt_instance: Optional[ContentPrompt] = None,
        dispatch_email: bool = False,
        recipient_email: Optional[str] = None
    ) -> GeneratedPost:
        """
        Executes end-to-end post generation:
        1. Selects or records prompt
        2. Queries LLM for structured theological content
        3. Generates required media (Quote Card or Vertical Reel)
        4. Persists GeneratedPost record
        5. Optionally dispatches directly to Christian's email for review.
        """
        logger.info(f"Starting content generation: category={category}, type={post_type}, dispatch_email={dispatch_email}")

        # 1. Fetch active prompt if not provided
        if not prompt_instance:
            prompt_instance = ContentPrompt.objects.filter(category=category, is_active=True).first()

        instructions = custom_instructions
        if not instructions and prompt_instance:
            instructions = prompt_instance.prompt_text

        # 2. Ingest structured LLM reflection
        reflection: ReflectionOutput = self.llm.generate_reflection(
            category=category,
            custom_instructions=instructions
        )

        # 3. Determine Palette by liturgical category
        palette_idx = 0  # Marian Midnight (Default / Morning Prayer)
        if category in [ContentCategory.EVENING_BIBLE_STUDY, ContentCategory.EVENING_REFLECTION]:
            palette_idx = 1  # Cardinal Liturgical Burgundy
        elif category == ContentCategory.SCRIPTURE:
            palette_idx = 2  # Sacred Trinity Forest Green
        elif category == ContentCategory.SUNDAY_HOMILY:
            palette_idx = 3  # Sacred Charcoal & Bronze

        # 4. Synthesize Media Artifacts
        media_asset: Optional[MediaAsset] = None

        if post_type == PostType.IMAGE_QUOTE:
            logger.info(f"Synthesizing branded Quote Card image (Palette {palette_idx})...")
            media_asset = self.image_gen.generate_quote_card(
                quote_text=reflection.quote_summary or reflection.caption[:250],
                scripture_citation=reflection.scripture_citation,
                title=reflection.title,
                author_name="Rev. Fr. Ejiogu Chukwuemeka",
                palette_index=palette_idx
            )

        elif post_type == PostType.VERTICAL_REEL:
            logger.info("Synthesizing voiceover and 9:16 vertical video reel...")
            audio_asset = self.tts.generate_voiceover(
                text=reflection.speech_text or reflection.caption,
                title=f"Reel Voiceover: {reflection.title}"
            )
            media_asset = self.video_gen.generate_reel(
                quote_text=reflection.quote_summary or reflection.title,
                audio_asset=audio_asset,
                scripture_citation=reflection.scripture_citation,
                title=reflection.title,
                author_name="Rev. Fr. Ejiogu Chukwuemeka"
            )

        # 5. Determine Initial Post Status
        initial_status = PostStatus.SCHEDULED if scheduled_time else PostStatus.DRAFT

        # 6. Save GeneratedPost
        post = GeneratedPost.objects.create(
            title=reflection.title,
            category=category,
            post_type=post_type,
            prompt=prompt_instance,
            caption=reflection.caption,
            scripture_citation=reflection.scripture_citation,
            hashtags=reflection.hashtags,
            media=media_asset,
            scheduled_time=scheduled_time,
            status=initial_status,
            is_published=False,
            is_emailed=False,
            facebook_posted=False
        )

        # 7. Optional Review Email Dispatch
        if dispatch_email:
            try:
                self.email_service.send_post_for_review(post, recipient=recipient_email)
                logger.info(f"Post #{post.id} automatically dispatched to review email.")
            except Exception as e:
                logger.error(f"Post #{post.id} was generated but email dispatch failed: {e}", exc_info=True)

        logger.info(f"Post #{post.id} successfully created (category={category}, status={post.status})")
        return post

    def generate_and_email_morning_prayer(self, recipient: Optional[str] = None) -> GeneratedPost:
        """
        Specialized 3:00 AM pipeline: Curates morning reflection & quote card,
        then immediately emails to Christian for morning review.
        """
        return self.generate_post(
            category=ContentCategory.MORNING_PRAYER,
            post_type=PostType.IMAGE_QUOTE,
            scheduled_time=timezone.now(),
            dispatch_email=True,
            recipient_email=recipient
        )

    def generate_and_email_evening_bible_study(self, recipient: Optional[str] = None) -> GeneratedPost:
        """
        Specialized Evening pipeline: Curates deep Bible study reflection & graphic card,
        then immediately emails to Christian for evening review and posting.
        """
        return self.generate_post(
            category=ContentCategory.EVENING_BIBLE_STUDY,
            post_type=PostType.IMAGE_QUOTE,
            scheduled_time=timezone.now(),
            dispatch_email=True,
            recipient_email=recipient
        )
