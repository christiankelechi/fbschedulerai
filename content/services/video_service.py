import os
import subprocess
import tempfile
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.conf import settings
from content.models import MediaAsset

logger = logging.getLogger(__name__)


class ReelVideoGenerator:
    """
    Synthesizes vertical 9:16 (1080x1920) video reels tailored for Meta Facebook Reels.
    Combines aesthetic Catholic visual design, pastoral voiceover audio, subtle motion
    filtering, and creates compressed MP4 files ready for programmatic upload.
    """

    WIDTH = 1080
    HEIGHT = 1920

    def __init__(self):
        pass

    def generate_reel(
        self,
        quote_text: str,
        audio_asset: MediaAsset,
        scripture_citation: str = "",
        title: str = "Daily Catholic Reel",
        author_name: str = "Rev. Fr. Ejiogu Chukwuemeka"
    ) -> MediaAsset:
        """
        Assembles a vertical video reel from audio asset and quote text.
        """
        audio_path = audio_asset.file_path.path
        duration = audio_asset.duration_seconds or 30.0

        # 1. Generate High-Res 9:16 Vertical Canvas
        canvas_img = self._create_vertical_canvas(
            quote_text=quote_text,
            scripture_citation=scripture_citation,
            author_name=author_name,
            title=title
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
            img_path = tmp_img.name
            canvas_img.save(img_path, format="PNG")

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_vid:
            out_path = tmp_vid.name

        # 2. Render MP4 using FFmpeg with Ken Burns subtle zoom effect and aligned audio
        self._render_ffmpeg_reel(img_path, audio_path, out_path, duration)

        # 3. Create Thumbnail Image
        thumb_img = canvas_img.copy()
        thumb_img.thumbnail((360, 640))
        thumb_io = BytesIO()
        thumb_img.save(thumb_io, format="JPEG", quality=85)
        thumb_io.seek(0)

        # 4. Read Final MP4 and Save to MediaAsset
        with open(out_path, "rb") as f:
            video_bytes = f.read()

        filename = f"reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        thumb_filename = f"thumb_{filename}.jpg"

        asset = MediaAsset(
            title=f"Reel: {title[:40]}",
            asset_type='video',
            aspect_ratio='9:16',
            duration_seconds=round(duration, 2),
            transcript=quote_text
        )
        asset.file_path.save(filename, ContentFile(video_bytes), save=False)
        asset.thumbnail.save(thumb_filename, ContentFile(thumb_io.getvalue()), save=False)
        asset.save()

        # Clean temporary scratch files
        for p in (img_path, out_path):
            try:
                os.remove(p)
            except OSError:
                pass

        logger.info(f"Reel generated successfully: {asset.id} -> {asset.file_path.name}")
        return asset

    def _create_vertical_canvas(
        self,
        quote_text: str,
        scripture_citation: str,
        author_name: str,
        title: str
    ) -> Image.Image:
        # Base Liturgical Midnight Gradient Canvas (1080x1920)
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), "#0A1128")
        draw = ImageDraw.Draw(img, 'RGBA')

        # Draw deep vertical gradient
        top_rgb = (10, 17, 40)
        bot_rgb = (28, 37, 65)
        for y in range(self.HEIGHT):
            ratio = y / self.HEIGHT
            r = int(top_rgb[0] * (1 - ratio) + bot_rgb[0] * ratio)
            g = int(top_rgb[1] * (1 - ratio) + bot_rgb[1] * ratio)
            b = int(top_rgb[2] * (1 - ratio) + bot_rgb[2] * ratio)
            draw.line([(0, y), (self.WIDTH, y)], fill=(r, g, b))

        gold = "#E5B94E"
        muted = "#C5D0E6"

        # Frame lines
        pad = 60
        draw.rectangle([(pad, pad), (self.WIDTH - pad, self.HEIGHT - pad)], outline=(212, 175, 55, 100), width=3)
        inset = 75
        draw.rectangle([(inset, inset), (self.WIDTH - inset, self.HEIGHT - inset)], outline=(212, 175, 55, 50), width=1)

        # Fonts
        font_header, font_quote, font_citation, font_footer = self._get_fonts()

        # Top Banner & Author
        draw.text((self.WIDTH // 2, 220), f"✝  {author_name.upper()}  ✝", fill=gold, font=font_header, anchor="mm")
        draw.text((self.WIDTH // 2, 280), f"• {title.upper()} •", fill=muted, font=font_footer, anchor="mm")

        # Big quote mark watermark
        draw.text((self.WIDTH // 2, 580), "“", fill=(212, 175, 55, 80), font=ImageFont.load_default(), anchor="mm")

        # Text Body in center (wrapped)
        clean_text = quote_text.strip().strip('"')
        lines = self._wrap_text(clean_text, max_width=self.WIDTH - 260, font=font_quote, draw=draw)
        line_height = int(font_quote.size * 1.5)
        total_h = len(lines) * line_height
        start_y = (self.HEIGHT // 2) - (total_h // 2)

        for idx, line in enumerate(lines):
            draw.text((self.WIDTH // 2, start_y + (idx * line_height)), line, fill="#FFFFFF", font=font_quote, anchor="mm")

        # Scripture citation badge
        if scripture_citation:
            cit_y = start_y + total_h + 100
            cit_text = f"📖  {scripture_citation.strip()}"
            bbox = draw.textbbox((0, 0), cit_text, font=font_citation)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            bx1 = (self.WIDTH - tw) // 2 - 30
            bx2 = (self.WIDTH + tw) // 2 + 30
            draw.rounded_rectangle([(bx1, cit_y - 15), (bx2, cit_y + th + 15)], radius=15, fill=(212, 175, 55, 30), outline=gold, width=2)
            draw.text((self.WIDTH // 2, cit_y + th // 2), cit_text, fill=gold, font=font_citation, anchor="mm")

        # Bottom CTA
        draw.text((self.WIDTH // 2, self.HEIGHT - 220), "LIKE  •  SHARE  •  AMEN", fill=gold, font=font_header, anchor="mm")
        draw.text((self.WIDTH // 2, self.HEIGHT - 170), "Stay Anchored in Faith & Prayer", fill=muted, font=font_footer, anchor="mm")

        return img

    def _render_ffmpeg_reel(self, image_path: str, audio_path: str, output_path: str, duration: float):
        """
        Executes FFmpeg with smooth motion and optimal H.264/AAC encoding for Meta Reels.
        """
        # Slow, majestic zoompan filter
        fps = 25
        total_frames = int(max(duration, 5) * fps)
        vf_filter = (
            f"zoompan=z='min(zoom+0.0005,1.08)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},"
            "format=yuv420p"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration),
            "-movflags", "+faststart",
            output_path
        ]

        logger.info(f"Running FFmpeg reel assembly: duration={duration:.1f}s")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            # Fallback simple command without complex filter if zoompan fails
            fallback_cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
                "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p", "-t", str(duration), "-movflags", "+faststart",
                output_path
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def _get_fonts(self):
        font_names = ["georgia.ttf", "times.ttf", "arial.ttf", "segoeui.ttf"]
        def load(size: int):
            for name in font_names:
                try:
                    return ImageFont.truetype(name, size)
                except Exception:
                    continue
            return ImageFont.load_default()

        return (
            load(36),  # Header
            load(48),  # Quote body
            load(32),  # Citation
            load(24)   # Footer
        )

    def _wrap_text(self, text: str, max_width: int, font: ImageFont.ImageFont, draw: ImageDraw.ImageDraw) -> list:
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []
        if current_line:
            lines.append(" ".join(current_line))
        return lines
