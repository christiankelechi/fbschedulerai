import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class ReflectionOutput:
    title: str
    caption: str
    scripture_citation: str
    hashtags: str
    quote_summary: str
    speech_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'caption': self.caption,
            'scripture_citation': self.scripture_citation,
            'hashtags': self.hashtags,
            'quote_summary': self.quote_summary,
            'speech_text': self.speech_text,
        }


class LLMService:
    """
    Service responsible for prompting zero-cost LLM endpoints via OpenRouter.
    Enforces Catholic pastoral voice tailored for Rev. Fr. Ejiogu Chukwuemeka,
    structured JSON output extraction, and fallback to curated local reflections.
    """

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_FREE_MODELS = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "meta-llama/llama-3-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free",
        "openrouter/free",
    ]

    BUILTIN_PROMPTS = {
        'morning_prayer': (
            "Compose a devout, uplifting Catholic Morning Prayer from Rev. Fr. Ejiogu Chukwuemeka. "
            "Focus on thanksgiving for life, surrender of the day's labors to Christ, and invoking the Holy Spirit. "
            "Include an inspiring scripture verse, a warm blessing, and relevant hashtags."
        ),
        'daily_reflection': (
            "Write a practical Catholic daily reflection from Rev. Fr. Ejiogu Chukwuemeka. "
            "Address everyday faith, perseverance through trials, acts of charity, and living the Gospel. "
            "Tie the message to a clear biblical citation and provide an actionable spiritual takeaway."
        ),
        'evening_reflection': (
            "Craft an evening examen and reflective prayer for the faithful at the close of day. "
            "Include gratitude for God's mercies, asking for forgiveness and peaceful rest under Mary's maternal mantle. "
            "Include scripture and an evening blessing from Rev. Fr. Ejiogu Chukwuemeka."
        ),
        'evening_bible_study': (
            "Conduct an engaging, spiritually deep Catholic Evening Bible Study reflection by Rev. Fr. Ejiogu Chukwuemeka. "
            "Focus on unpacking a specific biblical passage or theme with clear verse-by-verse theological insight, "
            "historical/liturgical context, and practical faith lessons for evening personal or family devotion. "
            "Conclude with an evening blessing and thought-provoking study questions or spiritual challenge."
        ),
        'scripture': (
            "Elaborate on a profound biblical passage with clear theological clarity and practical application for Christians today. "
            "Reverent, thought-provoking, pastoral tone by Rev. Fr. Ejiogu Chukwuemeka."
        ),
        'saint_of_the_day': (
            "Highlight the life and virtuous example of a Catholic Saint or Church Doctor. "
            "Extract practical virtues of humility, courage, and prayer for modern believers."
        ),
        'sunday_homily': (
            "Deliver an encouraging Sunday homily reflection breaking open the Word of God with pastoral warmth, "
            "spiritual depth, and hope in Christ Jesus."
        )
    }

    CURATED_FALLBACK_BANK = [
        ReflectionOutput(
            title="The Peace of Christ That Surpasses All Understanding",
            caption=(
                "Grace and peace be unto you, beloved of God.\n\n"
                "In moments when life’s storms threaten your tranquility, remember that Christ’s peace is not the absence "
                "of trouble, but the presence of God within the trouble. Do not carry tomorrow's burdens with today's grace. "
                "Cast your anxieties at the foot of the Cross, for the Lord is near and He sustains the weary soul.\n\n"
                "May God's heavenly countenance shine upon you, your home, and all the works of your hands this day."
            ),
            scripture_citation="Philippians 4:6-7",
            hashtags="#DailyReflection #CatholicFaith #FrEjioguReflections #PeaceInChrist #MorningPrayer #GraceAndMercy",
            quote_summary="Christ's peace is not the absence of trouble, but the abiding presence of God within the storm.",
            speech_text=(
                "Grace and peace be unto you, beloved of God. In moments when life's storms threaten your tranquility, "
                "remember that Christ's peace is not the absence of trouble, but the presence of God within the trouble. "
                "Do not carry tomorrow's burdens with today's grace. Cast your anxieties upon the Lord, for He cares for you."
            )
        ),
        ReflectionOutput(
            title="Walking by Faith, Anchored in Hope",
            caption=(
                "Beloved in Christ,\n\n"
                "Faith does not mean knowing where every road leads; it means trusting the One who guides your footsteps. "
                "When you cannot see what lies ahead, cling to God’s promises. He who began a good work in you will surely "
                "bring it to fulfillment. Step forward today in courage, knowing that you are never abandoned.\n\n"
                "Remain blessed in His holy presence."
            ),
            scripture_citation="2 Corinthians 5:7",
            hashtags="#FaithOverFear #CatholicDaily #WordOfGod #RevFrEjiogu #TrustInGod #SpiritualHope",
            quote_summary="Faith does not mean knowing where every road leads; it means trusting the One who guides your footsteps.",
            speech_text=(
                "Beloved in Christ, faith does not mean knowing where every road leads. It means trusting the One who guides "
                "your footsteps. When you cannot see what lies ahead, cling firmly to God's unfailing promises. Step forward "
                "today in divine courage."
            )
        ),
        ReflectionOutput(
            title="Divine Mercy and the Power of Forgiveness",
            caption=(
                "May the abundant mercy of Jesus Christ envelop your heart.\n\n"
                "Unforgiveness is a heavy chain that imprisons the soul, but mercy sets us free. As God has generously "
                "pardoned our shortcomings, let us extend that same healing grace to those who may have hurt us. "
                "Let love triumph over resentment today, and let the peace of Christ rule in your hearts.\n\n"
                "I pray God's sanctifying grace over you always."
            ),
            scripture_citation="Colossians 3:13",
            hashtags="#DivineMercy #Forgiveness #CatholicReflections #FrEjiogu #ChristOurPeace #CatholicLife",
            quote_summary="Unforgiveness is a heavy chain, but mercy sets the soul free to love like Christ.",
            speech_text=(
                "May the abundant mercy of Jesus Christ envelop your heart. Unforgiveness is a heavy chain that imprisons "
                "the soul, but mercy sets us free. As God has generously pardoned us, let us extend that same healing grace "
                "to others today."
            )
        ),
        ReflectionOutput(
            title="Thy Word Is a Lamp Unto My Feet: Evening Bible Study",
            caption=(
                "Good evening and peace of Christ be with you, beloved family of God.\n\n"
                "As the day draws to a gentle close, let us gather around the living Word of God. "
                "Psalm 119:105 declares: 'Your word is a lamp for my feet, a light on my path.' "
                "In ancient times, a traveler carried a small oil lamp that illuminated only the very next step, not the "
                "miles ahead. God's Word works the same way in our daily walk. He does not always reveal the entire "
                "destination at once, but He provides exact light and wisdom for every single step you must take today.\n\n"
                "Tonight, reflect upon where you need God's divine illumination in your family, your career, and your "
                "spiritual walk. Surrender your plans to Him in quiet prayer before you rest.\n\n"
                "May Almighty God bless and protect you tonight: Father, Son, and Holy Spirit. Amen."
            ),
            scripture_citation="Psalm 119:105",
            hashtags="#EveningBibleStudy #WordOfGod #CatholicScripture #FrEjiogu #NightPrayer #LampUntoMyFeet",
            quote_summary="God's Word is a lamp for your next step. Trust Him for tomorrow, and walk faithfully in His light tonight.",
            speech_text=(
                "Good evening and peace of Christ be with you, beloved family of God. As the day draws to a gentle close, "
                "let us gather around the living Word of God. Psalm 119 declares that His word is a lamp unto our feet. "
                "Trust Him for tomorrow, and walk faithfully in His holy light tonight."
            )
        )
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'OPENROUTER_API_KEY', '') or os.environ.get('OPENROUTER_API_KEY', '')

    def generate_reflection(
        self,
        category: str = 'daily_reflection',
        custom_instructions: Optional[str] = None
    ) -> ReflectionOutput:
        """
        Generates structured Catholic reflection content.
        Uses OpenRouter free models if API key is configured; otherwise uses curated fallback.
        """
        if not self.api_key:
            logger.warning("No OpenRouter API key provided. Using curated theological reflection bank.")
            return self._get_fallback_reflection(category)

        system_prompt = (
            "You are the theological and editorial assistant to Rev. Fr. Ejiogu Chukwuemeka, a Catholic Catholic Priest. "
            "Your writing is deeply reverent, uplifting, spiritually mature, intellectually sound, and pastoral. "
            "You must output STRICT JSON with no surrounding commentary or markdown backticks.\n\n"
            "The JSON must have this exact schema:\n"
            "{\n"
            '  "title": "A short compelling title (5-10 words)",\n'
            '  "caption": "The full pastoral reflection for Facebook (150-250 words, warm greeting, deep spiritual message, concluding pastoral blessing)",\n'
            '  "scripture_citation": "Book Chapter:Verse (e.g. Matthew 11:28-30)",\n'
            '  "hashtags": "5-8 relevant hashtags separated by spaces (e.g. #DailyReflection #CatholicFaith #FrEjioguReflections)",\n'
            '  "quote_summary": "A punchy, memorable 1-2 sentence quote extracted from the message for visual cards",\n'
            '  "speech_text": "Spoken transcript for a 30-45 second video reel voiceover (approx 60-80 words, spoken cadence)"\n'
            "}"
        )

        user_content = custom_instructions or self.BUILTIN_PROMPTS.get(
            category,
            self.BUILTIN_PROMPTS['daily_reflection']
        )
        user_prompt = f"Category: {category}\nPrompt Guidelines: {user_content}\n\nGenerate the reflection in the specified JSON format."

        for model in self.DEFAULT_FREE_MODELS:
            try:
                logger.info(f"Attempting LLM generation using model: {model}")
                result = self._call_openrouter(model, system_prompt, user_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}. Trying next available free model.")

        logger.error("All OpenRouter models failed. Returning curated reflection fallback.")
        return self._get_fallback_reflection(category)

    def _call_openrouter(self, model: str, system_prompt: str, user_prompt: str) -> Optional[ReflectionOutput]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://fbscheduler.frejiogu.org",
            "X-Title": "Rev Fr Ejiogu FB Content Scheduler",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }

        response = requests.post(self.OPENROUTER_URL, headers=headers, json=payload, timeout=45)
        if response.status_code != 200:
            logger.warning(f"OpenRouter HTTP {response.status_code}: {response.text}")
            return None

        data = response.json()
        raw_text = data['choices'][0]['message']['content'].strip()
        return self._parse_json_response(raw_text)

    def _parse_json_response(self, text: str) -> Optional[ReflectionOutput]:
        cleaned = text.strip()
        # Remove markdown code fence if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            return ReflectionOutput(
                title=str(parsed.get('title', 'Daily Catholic Reflection')).strip(),
                caption=str(parsed.get('caption', '')).strip(),
                scripture_citation=str(parsed.get('scripture_citation', '')).strip(),
                hashtags=str(parsed.get('hashtags', '#CatholicFaith #FrEjioguReflections')).strip(),
                quote_summary=str(parsed.get('quote_summary', parsed.get('title', ''))).strip(),
                speech_text=str(parsed.get('speech_text', parsed.get('caption', ''))).strip()
            )
        except json.JSONDecodeError as err:
            logger.warning(f"JSON decode failed on LLM output: {err}. Attempting regex recovery.")
            return self._regex_fallback_parse(text)

    def _regex_fallback_parse(self, text: str) -> Optional[ReflectionOutput]:
        def extract(field: str, default: str = "") -> str:
            match = re.search(rf'"{field}"\s*:\s*"((?:\\.|[^"\\])*)"', text)
            if match:
                return match.group(1).encode().decode('unicode_escape').strip()
            return default

        title = extract("title", "Daily Spiritual Reflection")
        caption = extract("caption", text[:300])
        citation = extract("scripture_citation", "Psalm 23:1")
        hashtags = extract("hashtags", "#DailyReflection #CatholicFaith #FrEjiogu")
        quote_summary = extract("quote_summary", title)
        speech_text = extract("speech_text", caption)

        if caption:
            return ReflectionOutput(
                title=title,
                caption=caption,
                scripture_citation=citation,
                hashtags=hashtags,
                quote_summary=quote_summary,
                speech_text=speech_text
            )
        return None

    def _get_fallback_reflection(self, category: str) -> ReflectionOutput:
        import random
        selected = random.choice(self.CURATED_FALLBACK_BANK)
        # Adapt title slightly if specific category
        if category == 'morning_prayer':
            return ReflectionOutput(
                title="Morning Offering & Blessing",
                caption=(
                    "Good morning and welcome to a brand new day of grace.\n\n"
                    "O Lord Jesus Christ, through the Immaculate Heart of Mary, I offer You my prayers, works, joys, and "
                    "sufferings of this day. Give our families peace, shield our going out and coming in, and grant us "
                    "the strength to reflect Your divine love in all we do today.\n\n"
                    "May Almighty God bless and protect you: Father, Son, and Holy Spirit. Amen."
                ),
                scripture_citation="Psalm 143:8",
                hashtags="#MorningPrayer #CatholicBlessing #FrEjioguReflections #NewDayNewGrace #DailyPrayer",
                quote_summary="Let the morning bring me word of Your unfailing love, for in You I have put my trust.",
                speech_text=(
                    "Good morning and welcome to a brand new day of divine grace. O Lord Jesus Christ, we offer You our "
                    "prayers, labors, and joys of this day. Shield our footsteps, bless our families, and may God's peace "
                    "be with you now and always. Amen."
                )
            )
        return selected
