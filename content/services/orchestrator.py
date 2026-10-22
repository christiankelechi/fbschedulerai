import logging
from datetime import datetime
from typing import Optional
from django.utils import timezone
from content.models import GeneratedPost, ContentPrompt, MediaAsset, ContentCategory, PostType, PostStatus
from .llm_service import LLMService, ReflectionOutput
from .image_service import QuoteCardGenerator
from .tts_service import TTSService
from .video_service import ReelVideoGenerator

logger = logging.getLogger(__name__)


class ContentPipelineOrchestrator:
    """
    High-level orchestrator for autonomous content ideation and synthesis.
    Integrates LLM text generation, Quote Card design, TTS voiceover synthesis,
    and Reel video assembly into a unified OOP workflow.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        image_generator: Optional[QuoteCardGenerator] = None,
        tts_service: Optional[TTSService] = None,
        video_generator: Optional[ReelVideoGenerator] = None
    ):
        self.llm = llm_service or LLMService()
        self.image_gen = image_generator or QuoteCardGenerator()
        self.tts = tts_service or TTSService()
        self.video_gen = video_generator or ReelVideoGenerator()

    def generate_post(
        self,
        category: str = ContentCategory.DAILY_REFLECTION,
        post_type: str = PostType.IMAGE_QUOTE,
        scheduled_time: Optional[datetime] = None,
        custom_instructions: Optional[str] = None,
        prompt_instance: Optional[ContentPrompt] = None
    ) -> GeneratedPost:
        """
        Executes end-to-end post generation:
        1. Selects or records prompt
        2. Queries LLM for structured theological content
        3. Generates required media (Quote Card or Vertical Reel)
        4. Persists GeneratedPost record ready for scheduling/publishing.
        """
        logger.info(f"Starting content generation: category={category}, type={post_type}")

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

        # 3. Synthesize Media Artifacts
        media_asset: Optional[MediaAsset] = None

        if post_type == PostType.IMAGE_QUOTE:
            logger.info("Synthesizing branded Quote Card image...")
            media_asset = self.image_gen.generate_quote_card(
                quote_text=reflection.quote_summary or reflection.caption[:250],
                scripture_citation=reflection.scripture_citation,
                title=reflection.title,
                author_name="Rev. Fr. Ejiogu Chukwuemeka"
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

        # 4. Determine Post Status
        initial_status = PostStatus.SCHEDULED if scheduled_time else PostStatus.DRAFT

        # 5. Save GeneratedPost
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
            is_published=False
        )

        logger.info(f"Post #{post.id} successfully generated and saved with status={initial_status}")
        return post
