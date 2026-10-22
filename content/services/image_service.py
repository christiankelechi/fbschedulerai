import os
import math
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from django.core.files.base import ContentFile
from django.conf import settings
from content.models import MediaAsset

logger = logging.getLogger(__name__)


class QuoteCardGenerator:
    """
    Synthesizes branded, visually stunning Catholic quote cards and social media
    graphics using Pillow. Implements elegant typography, liturgical color themes,
    and reverent visual framing for Rev. Fr. Ejiogu Chukwuemeka.
    """

    COLOR_PALETTES = [
        # (Background Top, Background Bottom, Accent Gold, Primary Text, Muted Text)
        ("#0B132B", "#1C2541", "#D4AF37", "#FFFFFF", "#C5D0E6"),  # Marian Midnight
        ("#1A0910", "#2E0E1B", "#E5B94E", "#FFF8F0", "#E0B7C6"),  # Cardinal Liturgical Burgundy
        ("#081C15", "#1B4332", "#DFBA58", "#F7FFF7", "#B7E4C7"),  # Sacred Forest / Trinity Green
        ("#161A1D", "#0B090A", "#E0A96D", "#F5F3F4", "#B1A7A6"),  # Sacred Charcoal & Bronze
    ]

    def __init__(self, width: int = 1080, height: int = 1080):
        self.width = width
        self.height = height

    def generate_quote_card(
        self,
        quote_text: str,
        scripture_citation: str = "",
        title: str = "DAILY REFLECTION",
        author_name: str = "Rev. Fr. Ejiogu Chukwuemeka",
        palette_index: int = 0
    ) -> MediaAsset:
        """
        Renders the quote card, generates a thumbnail, and persists to MediaAsset.
        """
        palette = self.COLOR_PALETTES[palette_index % len(self.COLOR_PALETTES)]
        bg_top, bg_bottom, gold_color, text_color, muted_color = palette

        # 1. Create Base Gradient Canvas
        image = self._create_vertical_gradient(bg_top, bg_bottom)
        draw = ImageDraw.Draw(image, 'RGBA')

        # 2. Draw Decorative Sacred Frame & Cross Watermark
        self._draw_sacred_accents(draw, gold_color)

        # 3. Load Fonts
        font_header, font_title, font_quote, font_citation, font_footer = self._get_font_hierarchy()

        # 4. Header: Author & Date
        date_str = datetime.now().strftime("%B %d, %Y").upper()
        draw.text(
            (self.width // 2, 90),
            f"✝  {author_name.upper()}  ✝",
            fill=gold_color,
            font=font_header,
            anchor="mm"
        )
        draw.text(
            (self.width // 2, 130),
            f"• {title.upper()} — {date_str} •",
            fill=muted_color,
            font=font_title,
            anchor="mm"
        )

        # 5. Quote Mark
        draw.text(
            (self.width // 2, 230),
            "“",
            fill=(212, 175, 55, 90),
            font=ImageFont.load_default(),
            anchor="mm"
        )

        # 6. Wrapped Body Text (Auto-scaling font)
        clean_quote = quote_text.strip().strip('"').strip('“').strip('”')
        lines = self._wrap_text(clean_quote, max_width=self.width - 240, font=font_quote, draw=draw)
        
        # Center the text block vertically in the middle area
        line_height = int(font_quote.size * 1.4)
        total_text_height = len(lines) * line_height
        start_y = (self.height // 2) - (total_text_height // 2) + 20

        for idx, line in enumerate(lines):
            draw.text(
                (self.width // 2, start_y + (idx * line_height)),
                line,
                fill=text_color,
                font=font_quote,
                anchor="mm"
            )

        # 7. Scripture Badge
        citation_y = start_y + total_text_height + 60
        if scripture_citation:
            citation_text = f"📖  {scripture_citation.strip()}"
            self._draw_scripture_badge(draw, citation_text, font_citation, gold_color, citation_y)

        # 8. Footer
        draw.text(
            (self.width // 2, self.height - 75),
            "PRAYER  •  WORD OF GOD  •  FELLOWSHIP",
            fill=muted_color,
            font=font_footer,
            anchor="mm"
        )

        # 9. Save to Bytes and MediaAsset
        output_io = BytesIO()
        image.save(output_io, format='JPEG', quality=95)
        output_io.seek(0)

        # Create thumbnail
        thumb_image = image.copy()
        thumb_image.thumbnail((320, 320))
        thumb_io = BytesIO()
        thumb_image.save(thumb_io, format='JPEG', quality=85)
        thumb_io.seek(0)

        filename = f"quote_card_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        thumb_filename = f"thumb_{filename}"

        asset = MediaAsset(
            title=f"Quote Card: {title[:40]}",
            asset_type='image',
            aspect_ratio='1:1',
            transcript=clean_quote
        )
        asset.file_path.save(filename, ContentFile(output_io.getvalue()), save=False)
        asset.thumbnail.save(thumb_filename, ContentFile(thumb_io.getvalue()), save=False)
        asset.save()

        logger.info(f"Quote card generated successfully: {asset.id} -> {asset.file_path.name}")
        return asset

    def _create_vertical_gradient(self, color_top: str, color_bottom: str) -> Image.Image:
        base = Image.new('RGB', (self.width, self.height), color_top)
        top_rgb = ImageDraw.ImageColor.getrgb(color_top)
        bottom_rgb = ImageDraw.ImageColor.getrgb(color_bottom)

        gradient = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(gradient)

        for y in range(self.height):
            ratio = y / self.height
            r = int(top_rgb[0] * (1 - ratio) + bottom_rgb[0] * ratio)
            g = int(top_rgb[1] * (1 - ratio) + bottom_rgb[1] * ratio)
            b = int(top_rgb[2] * (1 - ratio) + bottom_rgb[2] * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        return gradient

    def _draw_sacred_accents(self, draw: ImageDraw.ImageDraw, gold: str):
        # Outer delicate border
        pad = 40
        draw.rectangle(
            [(pad, pad), (self.width - pad, self.height - pad)],
            outline=(212, 175, 55, 120),
            width=2
        )
        # Inner fine inset border
        inset = 50
        draw.rectangle(
            [(inset, inset), (self.width - inset, self.height - inset)],
            outline=(212, 175, 55, 60),
            width=1
        )
        # Corner gold corner accents
        c_len = 25
        for x, y in [(inset, inset), (self.width - inset, inset), (inset, self.height - inset), (self.width - inset, self.height - inset)]:
            dx = c_len if x == inset else -c_len
            dy = c_len if y == inset else -c_len
            draw.line([(x, y), (x + dx, y)], fill=gold, width=3)
            draw.line([(x, y), (x, y + dy)], fill=gold, width=3)

    def _draw_scripture_badge(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, gold: str, y: int):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        pad_x = 28
        pad_y = 12

        box_x1 = (self.width - text_w) // 2 - pad_x
        box_x2 = (self.width + text_w) // 2 + pad_x
        box_y1 = y - pad_y
        box_y2 = y + text_h + pad_y

        draw.rounded_rectangle(
            [(box_x1, box_y1), (box_x2, box_y2)],
            radius=12,
            fill=(212, 175, 55, 25),
            outline=gold,
            width=2
        )
        draw.text((self.width // 2, y + text_h // 2), text, fill=gold, font=font, anchor="mm")

    def _get_font_hierarchy(self):
        # Attempt to load elegant system fonts, fallback to default if not present
        font_names = ["georgia.ttf", "times.ttf", "arial.ttf", "segoeui.ttf"]
        
        def load(size: int):
            for name in font_names:
                try:
                    return ImageFont.truetype(name, size)
                except Exception:
                    continue
            return ImageFont.load_default()

        return (
            load(28),  # Header
            load(20),  # Title
            load(38),  # Quote Body
            load(26),  # Scripture
            load(18)   # Footer
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
