import os
import asyncio
import logging
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Tuple
from django.core.files.base import ContentFile
from django.conf import settings
from content.models import MediaAsset

logger = logging.getLogger(__name__)


class TTSService:
    """
    Zero-Cost Voiceover Audio Synthesis Service.
    Primary Engine: Microsoft Edge Neural TTS (edge-tts) for studio-quality voices.
    Secondary Fallback: Offline pyttsx3 + FFmpeg conversion to ensure 100% uptime
    even if the host experiences temporary DNS or network restrictions.
    """

    DEFAULT_VOICE = "en-US-ChristopherNeural"  # Reverent, deep, pastoral priest voice
    ALTERNATIVE_VOICES = [
        "en-US-GuyNeural",
        "en-GB-RyanNeural",
        "en-NG-AbeoNeural",
    ]

    def __init__(self, voice: Optional[str] = None):
        self.voice = voice or getattr(settings, 'EDGE_TTS_VOICE', self.DEFAULT_VOICE)

    def generate_voiceover(
        self,
        text: str,
        title: str = "Voiceover Audio",
        voice: Optional[str] = None
    ) -> MediaAsset:
        """
        Synthesizes voiceover from text, computes duration, and persists as MediaAsset.
        """
        selected_voice = voice or self.voice
        clean_text = self._clean_speech_text(text)

        audio_bytes, duration = self._synthesize_with_edge_tts(clean_text, selected_voice)
        engine_used = "edge-tts"

        if not audio_bytes:
            logger.warning("edge-tts synthesis failed or unavailable. Falling back to offline pyttsx3 engine.")
            audio_bytes, duration = self._synthesize_with_pyttsx3(clean_text)
            engine_used = "pyttsx3-offline"

        if not audio_bytes:
            raise RuntimeError("All TTS engines failed to synthesize audio.")

        filename = f"voiceover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        asset = MediaAsset(
            title=f"{title} ({engine_used})",
            asset_type='audio',
            duration_seconds=round(duration, 2),
            transcript=clean_text
        )
        asset.file_path.save(filename, ContentFile(audio_bytes), save=False)
        asset.save()

        logger.info(f"TTS audio generated successfully ({engine_used}, {duration:.1f}s): {asset.file_path.name}")
        return asset

    def _clean_speech_text(self, text: str) -> str:
        # Strip hashtags, urls, and emojis that sound awkward when spoken
        import re
        no_urls = re.sub(r'https?://\S+', '', text)
        no_tags = re.sub(r'#\w+', '', no_urls)
        no_bracket = re.sub(r'\[.*?\]', '', no_tags)
        cleaned = " ".join(no_bracket.split()).strip()
        return cleaned

    def _synthesize_with_edge_tts(self, text: str, voice: str) -> Tuple[Optional[bytes], float]:
        import edge_tts

        async def _run():
            communicate = edge_tts.Communicate(text, voice)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            await communicate.save(tmp_path)
            return tmp_path

        try:
            # Run async function safely within sync code
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                # If inside another running event loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    tmp_path = pool.submit(asyncio.run, _run()).result(timeout=60)
            else:
                tmp_path = loop.run_until_complete(_run())

            duration = self._probe_audio_duration(tmp_path)
            with open(tmp_path, "rb") as f:
                data = f.read()

            try:
                os.remove(tmp_path)
            except OSError:
                pass

            return data, duration
        except Exception as e:
            logger.warning(f"edge-tts failed: {e}")
            return None, 0.0

    def _synthesize_with_pyttsx3(self, text: str) -> Tuple[Optional[bytes], float]:
        try:
            import pyttsx3
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                wav_path = tmp_wav.name
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                mp3_path = tmp_mp3.name

            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # Slower, reverent pastoral cadence
            engine.save_to_file(text, wav_path)
            engine.runAndWait()

            # Convert WAV to MP3 using ffmpeg
            cmd = ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            duration = self._probe_audio_duration(mp3_path)
            with open(mp3_path, "rb") as f:
                data = f.read()

            for p in (wav_path, mp3_path):
                try:
                    os.remove(p)
                except OSError:
                    pass

            return data, duration
        except Exception as e:
            logger.error(f"pyttsx3 offline engine failed: {e}")
            return None, 0.0

    def _probe_audio_duration(self, file_path: str) -> float:
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(result.stdout.strip())
        except Exception:
            return 30.0  # Safe default estimate
