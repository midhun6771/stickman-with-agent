import math
from typing import Dict, Any, Tuple, Union
from PIL import ImageDraw, ImageFont

ACCENT_RGB = {
    "cyan": (0, 220, 255),
    "crimson": (255, 45, 85),
    "gold": (255, 215, 0),
    "orange": (255, 120, 40),
    "white": (255, 255, 255)
}

def normalize_color(value: Any, default: Tuple[int, int, int] = (0, 220, 255)) -> Tuple[int, int, int]:
    """Safely converts color strings or legacy RGB tuples into valid RGB tuples."""
    if isinstance(value, str):
        clean = value.strip().lower()
        return ACCENT_RGB.get(clean, default)
    if isinstance(value, (list, tuple)) and len(value) == 3:
        if all(isinstance(c, (int, float)) and 0 <= c <= 255 for c in value):
            return tuple(int(c) for c in value)
    return default

def draw_treadmill(draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float, width: int, font: ImageFont.ImageFont, params: Dict[str, Any]):
    track_y = cy + 180
    color = normalize_color(params.get("color"), default=(0, 220, 255))
    draw.line([80, track_y, width - 80, track_y], fill=color, width=6)
    offset = int((t * 300) % 60)
    for x in range(80, width - 80, 60):
        draw.line([x - offset, track_y, x - offset - 20, track_y + 25], fill=color, width=3)

def draw_tv(draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float, width: int, font: ImageFont.ImageFont, params: Dict[str, Any]):
    tv_x, tv_y = cx + 80, cy - 140
    color = normalize_color(params.get("color"), default=(0, 220, 255))
    draw.rectangle([tv_x - 100, tv_y - 70, tv_x + 100, tv_y + 70], outline=color, width=4, fill=(18, 24, 38))
    draw.line([tv_x - 30, tv_y + 70, tv_x - 50, tv_y + 110], fill=color, width=4)
    draw.line([tv_x + 30, tv_y + 70, tv_x + 50, tv_y + 110], fill=color, width=4)
    
    # Antenna
    draw.line([tv_x - 20, tv_y - 70, tv_x - 60, tv_y - 110], fill=color, width=3)
    draw.line([tv_x + 20, tv_y - 70, tv_x + 60, tv_y - 110], fill=color, width=3)

    label = str(params.get("label", "TV"))
    draw.text((tv_x - 50, tv_y - 15), label, font=font, fill=(255, 215, 0))

def draw_breakdown_bar(draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float, width: int, font: ImageFont.ImageFont, params: Dict[str, Any]):
    raw_segments = params.get("segments", [
        {"label": "RECAP & INTRO", "color": "crimson"},
        {"label": "HALLWAY RUNNING", "color": "orange"},
        {"label": "REACTION GASPS", "color": "crimson"},
        {"label": "ACTUAL PLOT", "color": "cyan"}
    ])
    bx, by = 100, cy - 230
    bw = width - 200
    for i, seg in enumerate(raw_segments):
        c = normalize_color(seg.get("color"), default=(255, 45, 85))
        lbl = str(seg.get("label", "SEGMENT"))
        draw.rectangle([bx, by + (i * 45), bx + bw, by + (i * 45) + 40], fill=c)
        draw.text((bx + 20, by + (i * 45) + 8), lbl, font=font, fill=(255, 255, 255))

def draw_press(draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float, width: int, font: ImageFont.ImageFont, params: Dict[str, Any]):
    press_cycle = (math.sin(t * 5) + 1) / 2
    press_y = int(220 + press_cycle * 140)
    
    draw.rectangle([cx - 40, 120, cx + 40, press_y], fill=(90, 105, 130))
    draw.rectangle([cx - 160, press_y, cx + 160, press_y + 45], fill=(200, 215, 235), outline=(0, 220, 255), width=3)
    draw.text((cx - 80, press_y + 10), "STUDIO PRESS", font=font, fill=(10, 12, 16))
    draw.rectangle([cx - 180, 450, cx + 180, 500], fill=(45, 55, 75))

def draw_pit(draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float, width: int, font: ImageFont.ImageFont, params: Dict[str, Any]):
    draw.polygon([(0, 200), (140, 880), (0, 880)], fill=(25, 30, 42))
    draw.polygon([(width, 200), (width - 140, 880), (width, 880)], fill=(25, 30, 42))
    draw.line([140, 880, width - 140, 880], fill=(0, 220, 255), width=4)

def draw_trophy(draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float, width: int, font: ImageFont.ImageFont, params: Dict[str, Any]):
    trophy_y = int(320 + math.sin(t * 3) * 12)
    draw.line([cx, 150, cx, trophy_y], fill=(255, 215, 0), width=3)
    draw.polygon([(cx - 35, trophy_y), (cx + 35, trophy_y), (cx + 20, trophy_y + 40), (cx - 20, trophy_y + 40)], fill=(255, 215, 0))
    draw.rectangle([cx - 8, trophy_y + 40, cx + 8, trophy_y + 60], fill=(255, 215, 0))
    draw.rectangle([cx - 25, trophy_y + 60, cx + 25, trophy_y + 72], fill=(255, 215, 0))
    title = str(params.get("title", "THE TROPHY"))
    draw.text((cx - 60, trophy_y - 35), title, font=font, fill=(255, 215, 0))

def draw_energy_burst(draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float, width: int, font: ImageFont.ImageFont, params: Dict[str, Any]):
    for deg in range(0, 360, 15):
        rad = math.radians(deg + t * 40)
        x1 = cx + math.cos(rad) * 120
        y1 = cy + math.sin(rad) * 120
        x2 = cx + math.cos(rad) * 600
        y2 = cy + math.sin(rad) * 600
        col = (255, 215, 0) if deg % 30 == 0 else (255, 255, 255)
        draw.line([x1, y1, x2, y2], fill=col, width=3)

def draw_fork_paths(draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float, width: int, font: ImageFont.ImageFont, params: Dict[str, Any]):
    draw.polygon([(cx - 10, 220), (cx + 10, 220), (width - 60, 750), (width - 160, 750)], fill=(35, 20, 30), outline=(255, 45, 85), width=3)
    draw.polygon([(cx - 10, 220), (cx + 10, 220), (160, 750), (60, 750)], fill=(20, 35, 40), outline=(0, 220, 255), width=3)
    left_label = str(params.get("left_label", "OPTION A"))
    right_label = str(params.get("right_label", "OPTION B"))
    draw.text((90, 480), left_label, font=font, fill=(0, 220, 255))
    draw.text((width - 210, 480), right_label, font=font, fill=(255, 45, 85))

def draw_icon_badge(draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float, width: int, font: ImageFont.ImageFont, params: Dict[str, Any], prop_name: str = "ICON"):
    bob = math.sin(t * 3.5) * 8
    bx = cx + 80
    by = int(cy - 140 + bob)
    w_box, h_box = 200, 75
    color = normalize_color(params.get("color"), default=(0, 220, 255))
    draw.rounded_rectangle([bx - w_box//2, by - h_box//2, bx + w_box//2, by + h_box//2], radius=16, fill=(18, 24, 38), outline=color, width=3)
    display_name = prop_name.upper().replace("-", " ")[:14]
    draw.text((bx - 65, by - 14), f"✨ {display_name}", font=font, fill=(255, 215, 0))

PROP_REGISTRY = {
    "treadmill": draw_treadmill,
    "tv": draw_tv,
    "breakdown_bar": draw_breakdown_bar,
    "press": draw_press,
    "pit": draw_pit,
    "trophy": draw_trophy,
    "energy_burst": draw_energy_burst,
    "fork_paths": draw_fork_paths
}

def get_prop_renderer(prop_type: str):
    """Returns specialized procedural drawer, or None if no valid procedural prop."""
    if prop_type in PROP_REGISTRY:
        return PROP_REGISTRY[prop_type]
    return None
