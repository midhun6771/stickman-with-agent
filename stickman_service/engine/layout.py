from typing import Tuple, List
from PIL import ImageDraw, ImageFont

def get_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    font_names = ["arialbd.ttf", "calibrib.ttf", "segoeuib.ttf"] if bold else ["arial.ttf", "calibri.ttf", "segoeui.ttf"]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except:
            continue
    return ImageFont.load_default()

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
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
    if current_line:
        lines.append(" ".join(current_line))
    return lines

class LayoutEngine:
    """
    Guarantees deterministic, clean layout for 9:16 vertical video.
    Handles bounding box calculations, text centering, and safe zones.
    """
    def __init__(self, width: int = 720, height: int = 1280):
        self.width = width
        self.height = height
        self.font_badge = get_font(24, bold=True)
        self.font_overlay = get_font(32, bold=True)
        self.font_sub = get_font(20, bold=False)

    def draw_progress_bar(self, draw: ImageDraw.ImageDraw, progress: float):
        # Progress bar disabled for cinema-grade anime immersion
        pass

    def draw_badge(self, draw: ImageDraw.ImageDraw, badge_text: str, color: Tuple[int, int, int] = (255, 45, 85), t: float = 0.5, scene_dur: float = 5.0):
        if not badge_text or badge_text.strip().upper() in ("NONE", ""):
            return
        
        # Cinema entrance timing: appears at t=0.3s, displays for up to 2.2s, then cleanly fades/exits
        max_display = min(2.4, scene_dur * 0.5)
        if t < 0.25 or t > max_display:
            return

        clean_text = badge_text.strip().upper()
        bbox = draw.textbbox((0, 0), clean_text, font=self.font_badge)
        bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bx = (self.width - bw) // 2
        by = 55

        # Sleek anime clash banner: dark glass backing with accent outline
        draw.rounded_rectangle(
            [bx - 22, by - 8, bx + bw + 22, by + bh + 10],
            radius=8,
            fill=(18, 22, 32),
            outline=color,
            width=2
        )
        draw.text((bx, by), clean_text, font=self.font_badge, fill=(255, 255, 255))

    def draw_overlay_card(self, draw: ImageDraw.ImageDraw, overlay_text: str, outline_color: Tuple[int, int, int] = (0, 220, 255)):
        # Replaced by V7 Cinema-Grade .ASS Karaoke Subtitle Engine
        pass
