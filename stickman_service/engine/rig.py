import math
from typing import Tuple, Dict, Any, List, Optional
from PIL import ImageDraw

def normalize_x_offset(value: Any) -> float:
    """Validates finite numeric offset and clamps to safe staging bounds [-0.6, 0.6]."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        print(f"  [WARN] Invalid non-numeric x_offset '{value!r}', falling back to center (0.0)")
        return 0.0
    orig = float(value)
    clamped = max(-0.6, min(0.6, orig))
    if clamped != orig:
        print(f"  [WARN] Clamped out-of-bounds x_offset: {orig} -> {clamped}")
    return clamped

def normalize_speed(value: Any) -> float:
    """Guarantees character motion speed remains within realistic physical limits [0.5, 1.5]."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return 1.0
    return max(0.5, min(1.5, float(value)))

# Curated Modular Caricature Color Palettes
SKIN_TONES = {
    "fair": (255, 224, 189),
    "pale": (255, 238, 227),
    "tan": (224, 172, 105),
    "dark": (141, 85, 36),
    "bone_white": (245, 245, 250),
    "green": (115, 190, 115),
    "blue": (130, 180, 240)
}

HAIR_COLORS = {
    "blonde": (252, 220, 65),
    "green": (48, 180, 78),
    "purple": (165, 65, 225),
    "black": (25, 25, 32),
    "white": (245, 245, 250),
    "brown": (115, 65, 35),
    "orange": (245, 115, 35),
    "blue": (45, 145, 245),
    "red": (225, 45, 45),
    "pink": (245, 135, 175)
}

CLOTHING_COLORS = {
    "black": (25, 27, 36),
    "purple": (130, 42, 180),
    "crimson": (215, 32, 48),
    "blue": (32, 95, 215),
    "white": (242, 244, 250),
    "gold": (238, 192, 42),
    "green": (38, 145, 68),
    "navy": (26, 38, 78),
    "pink": (232, 92, 145),
    "gray": (85, 95, 110)
}

class StickmanRig:
    """
    Parametric 2D stickman with deterministic joint kinematics.
    Never hallucinates extra limbs, disembodied heads, or impossible angles.
    """
    def __init__(self, base_x: float, base_y: float, scale: float = 1.0, color: Tuple[int, int, int] = (255, 255, 255)):
        self.base_x = base_x
        self.base_y = base_y
        self.scale = scale
        self.color = color
        
        # Anatomical proportions (scaled)
        self.head_radius = 32 * scale
        self.torso_len = 110 * scale
        self.arm_upper = 55 * scale
        self.arm_lower = 50 * scale
        self.leg_upper = 65 * scale
        self.leg_lower = 60 * scale
        self.shoulder_width = 30 * scale
        self.hip_width = 25 * scale
        self.line_width = max(3, int(4 * scale))

    def _draw_caricature_head(self, draw: ImageDraw.ImageDraw, hx: float, hy: float, facing: int,
                              expr: str, skin_tone: str = "fair", hair_style: str = "bald",
                              hair_color: str = "black", face_traits: Optional[List[str]] = None,
                              t: float = 0.0):
        """
        Cinema-Grade Modular Caricature Head Engine:
        Renders solid flesh-filled head, giant expressive Flash cartoon eyes,
        iconic hair silhouettes, and signature facial traits (Sanji curly brow/cigarette,
        Ivankov eyelashes/lipstick, Zoro scar/earrings, noble wavy hair).
        """
        scale = self.scale
        r = self.head_radius * 1.12
        traits = face_traits or []
        skin_col = SKIN_TONES.get(skin_tone.lower(), (255, 224, 189))
        hair_col = HAIR_COLORS.get(hair_color.lower(), (25, 25, 32))

        # 1. Back hair volume layer (for massive afro, twin tails, long locks, or regal waves behind head)
        if hair_style == "massive_afro":
            afro_r = r * 1.7
            draw.ellipse([hx - afro_r, hy - afro_r - 10 * scale, hx + afro_r, hy + afro_r * 0.7], fill=hair_col, outline=(15, 15, 20), width=max(2, int(3 * scale)))
            for angle_deg in range(0, 360, 40):
                rad = math.radians(angle_deg)
                px = hx + math.cos(rad) * (afro_r * 0.85)
                py = (hy - 5 * scale) + math.sin(rad) * (afro_r * 0.7)
                draw.ellipse([px - 14 * scale, py - 14 * scale, px + 14 * scale, py + 14 * scale], fill=hair_col)
        elif hair_style == "twin_tails":
            # Anime twin pigtails flanking both sides (Gunko Signature)
            draw.polygon([
                (hx - r * 0.85, hy - r * 0.2),
                (hx - r * 1.45, hy + r * 0.6),
                (hx - r * 1.6, hy + r * 1.8),
                (hx - r * 1.25, hy + r * 1.8),
                (hx - r * 0.95, hy + r * 0.7)
            ], fill=hair_col, outline=(20, 20, 25))
            draw.polygon([
                (hx + r * 0.85, hy - r * 0.2),
                (hx + r * 1.45, hy + r * 0.6),
                (hx + r * 1.6, hy + r * 1.8),
                (hx + r * 1.25, hy + r * 1.8),
                (hx + r * 0.95, hy + r * 0.7)
            ], fill=hair_col, outline=(20, 20, 25))
            # Scrunchies / hair ties at base
            draw.ellipse([hx - r * 1.05, hy - r * 0.35, hx - r * 0.65, hy - r * 0.05], fill=(235, 45, 65))
            draw.ellipse([hx + r * 0.65, hy - r * 0.35, hx + r * 1.05, hy - r * 0.05], fill=(235, 45, 65))
        elif hair_style == "long_hair":
            draw.polygon([
                (hx - r * 1.05, hy - r * 0.3),
                (hx - r * 1.3, hy + r * 2.0),
                (hx + r * 1.3, hy + r * 2.0),
                (hx + r * 1.05, hy - r * 0.3)
            ], fill=hair_col, outline=(20, 20, 25))
        elif hair_style == "ponytail":
            pony_pts = [
                (hx - facing * r * 0.6, hy - r * 0.6),
                (hx - facing * r * 1.6, hy - r * 0.1),
                (hx - facing * r * 1.8, hy + r * 1.1),
                (hx - facing * r * 1.4, hy + r * 0.9),
                (hx - facing * r * 0.8, hy - r * 0.2)
            ]
            draw.polygon(pony_pts, fill=hair_col, outline=(20, 20, 25))
            draw.ellipse([hx - facing * r * 0.8 - 4 * scale, hy - r * 0.6 - 4 * scale, hx - facing * r * 0.8 + 4 * scale, hy - r * 0.6 + 4 * scale], fill=(235, 45, 65))
        elif hair_style == "regal_wavy":
            w_pts_l = [
                (hx - r * 0.85, hy - r * 0.4),
                (hx - r * 1.35, hy + r * 0.6),
                (hx - r * 1.2, hy + r * 1.5),
                (hx - r * 0.6, hy + r * 1.2),
                (hx - r * 0.7, hy + r * 0.3)
            ]
            w_pts_r = [
                (hx + r * 0.85, hy - r * 0.4),
                (hx + r * 1.35, hy + r * 0.6),
                (hx + r * 1.2, hy + r * 1.5),
                (hx + r * 0.6, hy + r * 1.2),
                (hx + r * 0.7, hy + r * 0.3)
            ]
            draw.polygon(w_pts_l, fill=hair_col, outline=(20, 20, 25))
            draw.polygon(w_pts_r, fill=hair_col, outline=(20, 20, 25))

        # 2. Solid Flesh-Filled Head Ellipse or Skeletal Bone Skull (Brook)
        is_skeleton = (skin_tone == "bone_white" or "skull" in traits or "skeleton" in traits)
        if is_skeleton:
            # Skull Cranium
            draw.ellipse([hx - r, hy - r, hx + r, hy + r * 0.55], fill=(245, 245, 250), outline=(20, 20, 25), width=max(2, int(3 * scale)))
            # Angular cheekbones and jaw
            jaw_w = r * 0.62
            draw.polygon([
                (hx - jaw_w, hy + r * 0.3),
                (hx + jaw_w, hy + r * 0.3),
                (hx + jaw_w * 0.85, hy + r * 1.05),
                (hx - jaw_w * 0.85, hy + r * 1.05)
            ], fill=(245, 245, 250), outline=(20, 20, 25), width=max(2, int(2.5 * scale)))
        else:
            draw.ellipse([hx - r, hy - r, hx + r, hy + r], fill=skin_col, outline=(20, 20, 25), width=max(2, int(3 * scale)))

        # 3. Big Expressive Cartoon Eyes (or Hollow Bone Sockets for Skull)
        eye_y = hy - 2 * scale
        lead_eye_x = hx + (9 * facing) * scale
        rear_eye_x = hx - (7 * facing) * scale
        lead_w, lead_h = 9 * scale, 13 * scale
        rear_w, rear_h = 7 * scale, 10 * scale

        # Bangs occlusion rule: Sanji's sweep bangs always cover the rear side of face
        hide_rear_eye = (hair_style == "blonde_sweep" and facing == 1)
        hide_lead_eye = (hair_style == "blonde_sweep" and facing == -1)

        def draw_cartoon_eye(ex, ey, ew, eh, is_lead=True):
            # Crisp white sclera
            draw.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], fill=(255, 255, 255), outline=(20, 20, 25), width=max(1, int(2 * scale)))
            # Expression lid modifications
            if expr == "deadpan":
                draw.rectangle([ex - ew - 1, ey - eh - 1, ex + ew + 1, ey], fill=skin_col, outline=(20, 20, 25), width=max(1, int(1.5 * scale)))
            elif expr == "angry":
                brow_pts = [(ex - ew - 2, ey - eh - 2), (ex + ew + 2, ey - eh * 0.2), (ex - ew - 2, ey - eh * 0.2)] if facing == 1 else [(ex + ew + 2, ey - eh - 2), (ex - ew - 2, ey - eh * 0.2), (ex + ew + 2, ey - eh * 0.2)]
                draw.polygon(brow_pts, fill=skin_col)
                draw.line([brow_pts[0], brow_pts[1]], fill=(20, 20, 25), width=max(2, int(2.5 * scale)))

            # Pupil with catchlight glint
            pupil_r = max(2, int(3.5 * scale)) if expr != "shocked" else max(1, int(1.8 * scale))
            pupil_x = ex + (2.5 * facing) * scale
            pupil_y = ey + (1.0 if expr == "deadpan" else 0.0) * scale
            draw.ellipse([pupil_x - pupil_r, pupil_y - pupil_r, pupil_x + pupil_r, pupil_y + pupil_r], fill=(20, 20, 25))
            glint_r = max(1, int(1.2 * scale))
            draw.ellipse([pupil_x - glint_r + 1, pupil_y - glint_r - 1, pupil_x + glint_r + 1, pupil_y + glint_r - 1], fill=(255, 255, 255))

            # Queen Lashes trait
            if "queen_eyelashes" in traits:
                lash_dir = facing if is_lead else -facing
                top_x = ex + (ew * lash_dir) * 0.8
                top_y = ey - eh * 0.7
                draw.line([top_x, top_y, top_x + 8 * lash_dir * scale, top_y - 8 * scale], fill=(15, 15, 20), width=max(2, int(2.5 * scale)))
                draw.line([top_x, top_y + 2, top_x + 10 * lash_dir * scale, top_y - 2 * scale], fill=(15, 15, 20), width=max(2, int(2.5 * scale)))
                draw.line([top_x, top_y + 5, top_x + 9 * lash_dir * scale, top_y + 4 * scale], fill=(15, 15, 20), width=max(2, int(2.5 * scale)))

            # Eye scar trait
            if "eye_scar" in traits and not is_lead:
                draw.line([ex, ey - eh * 1.6, ex, ey + eh * 1.6], fill=(140, 40, 40), width=max(2, int(2.5 * scale)))

        def draw_skull_socket(ex, ey, ew, eh):
            # Hollow dark bone sockets for skull
            draw.ellipse([ex - ew, ey - eh * 0.9, ex + ew, ey + eh * 0.9], fill=(20, 20, 25), outline=(15, 15, 20), width=1)

        if is_skeleton:
            if not hide_rear_eye:
                draw_skull_socket(rear_eye_x, eye_y, rear_w * 1.05, rear_h * 1.05)
            if not hide_lead_eye:
                draw_skull_socket(lead_eye_x, eye_y, lead_w * 1.05, lead_h * 1.05)
        else:
            if not hide_rear_eye:
                draw_cartoon_eye(rear_eye_x, eye_y, rear_w, rear_h, is_lead=False)
            if not hide_lead_eye:
                draw_cartoon_eye(lead_eye_x, eye_y, lead_w, lead_h, is_lead=True)

        # 4. Eyebrows & Signature Brow Traits
        brow_y = eye_y - lead_h - (3 * scale)
        if is_skeleton:
            # Brook's signature diagonal forehead bone fissure
            draw.line([(hx + 4 * facing * scale, hy - r * 0.65), (hx + 9 * facing * scale, hy - r * 0.4), (hx + 5 * facing * scale, hy - r * 0.15)], fill=(30, 30, 35), width=max(1, int(2 * scale)))
        elif "curly_eyebrow" in traits:
            eb_start_x = lead_eye_x - (6 * facing) * scale
            eb_end_x = lead_eye_x + (9 * facing) * scale
            draw.line([eb_start_x, brow_y, eb_end_x, brow_y], fill=(20, 20, 25), width=max(2, int(2.5 * scale)))
            swirl_cx = eb_end_x
            draw.arc([swirl_cx - 4 * scale, brow_y - 5 * scale, swirl_cx + 4 * scale, brow_y + 3 * scale], start=0, end=270, fill=(20, 20, 25), width=max(2, int(2 * scale)))
        elif expr not in ("angry",):
            if expr == "shocked":
                draw.arc([lead_eye_x - 7 * scale, brow_y - 6 * scale, lead_eye_x + 7 * scale, brow_y], start=180, end=0, fill=(20, 20, 25), width=max(2, int(2 * scale)))
            elif expr == "smirk":
                draw.line([lead_eye_x - 6 * scale, brow_y + 2 * scale, lead_eye_x + 8 * scale, brow_y - 3 * scale], fill=(20, 20, 25), width=max(2, int(2 * scale)))
            else:
                draw.line([lead_eye_x - 6 * scale, brow_y, lead_eye_x + 7 * scale, brow_y], fill=(20, 20, 25), width=max(2, int(2 * scale)))

        # 5. Minimalist Anime Nose (or Triangular Skull Cavity)
        nose_x = hx + (12 * facing) * scale
        nose_y = hy + 6 * scale
        if is_skeleton:
            draw.polygon([
                (nose_x - 3 * scale, nose_y + 3 * scale),
                (nose_x + 3 * scale, nose_y + 3 * scale),
                (nose_x, nose_y - 4 * scale)
            ], fill=(20, 20, 25))
        else:
            draw.line([nose_x - 3 * facing * scale, nose_y - 4 * scale, nose_x, nose_y], fill=(20, 20, 25), width=max(1, int(1.8 * scale)))

        # 6. Mouth, Lips & Skeletal Teeth Grin / Predatory Sharp Teeth Grin
        mouth_x = hx + (9 * facing) * scale
        mouth_y = hy + (18 * scale if is_skeleton else 16 * scale)
        if is_skeleton:
            # Iconic skeletal grin: horizontal dental band with vertical tooth dividers
            jaw_mw = 13 * scale
            draw.rectangle([mouth_x - jaw_mw, mouth_y - 4 * scale, mouth_x + jaw_mw, mouth_y + 5 * scale], fill=(20, 20, 25), outline=(20, 20, 25), width=1)
            for t_step in range(-3, 4):
                tx = mouth_x + (t_step * 3.6 * scale)
                draw.line([tx, mouth_y - 4 * scale, tx, mouth_y + 5 * scale], fill=(245, 245, 250), width=max(1, int(1.8 * scale)))
            draw.line([mouth_x - jaw_mw - 2, mouth_y, mouth_x + jaw_mw + 2, mouth_y], fill=(245, 245, 250), width=max(1, int(1.5 * scale)))
        elif "sharp_teeth" in traits or "sinister_smile" in traits:
            # God's Knight Saint Killingham Predatory Grin with Sharp Jagged Fangs
            mw, mh = 14 * scale, 9 * scale
            draw.polygon([
                (mouth_x - mw, mouth_y - 3 * scale),
                (mouth_x + mw, mouth_y - 3 * scale),
                (mouth_x + mw * 0.7, mouth_y + mh),
                (mouth_x - mw * 0.7, mouth_y + mh)
            ], fill=(15, 12, 20), outline=(20, 20, 25), width=max(1, int(2 * scale)))
            # Sharp triangular fangs top & bottom
            fang_count = 5
            fw = (mw * 1.8) / fang_count
            for f_i in range(fang_count):
                fx_base = mouth_x - mw * 0.85 + (f_i * fw)
                # Upper fangs pointing down
                draw.polygon([
                    (fx_base, mouth_y - 3 * scale),
                    (fx_base + fw, mouth_y - 3 * scale),
                    (fx_base + fw * 0.5, mouth_y + mh * 0.55)
                ], fill=(250, 250, 255))
                # Lower fangs pointing up
                draw.polygon([
                    (fx_base, mouth_y + mh),
                    (fx_base + fw, mouth_y + mh),
                    (fx_base + fw * 0.5, mouth_y + mh * 0.4)
                ], fill=(250, 250, 255))
        elif "lipstick" in traits:
            lip_w, lip_h = 12 * scale, 7 * scale
            draw.ellipse([mouth_x - lip_w, mouth_y - lip_h, mouth_x + lip_w, mouth_y + lip_h], fill=(185, 30, 110), outline=(20, 20, 25), width=max(1, int(2 * scale)))
            draw.line([mouth_x - lip_w + 2, mouth_y, mouth_x + lip_w - 2, mouth_y], fill=(30, 10, 20), width=max(1, int(1.5 * scale)))
        elif expr in ("smile", "confident"):
            draw.arc([mouth_x - 9 * scale, mouth_y - 4 * scale, mouth_x + 9 * scale, mouth_y + 8 * scale], start=0, end=180, fill=(20, 20, 25), width=max(2, int(2.5 * scale)))
        elif expr == "shocked":
            draw.ellipse([mouth_x - 5 * scale, mouth_y - 4 * scale, mouth_x + 5 * scale, mouth_y + 8 * scale], fill=(30, 20, 25), outline=(20, 20, 25), width=max(1, int(2 * scale)))
        elif expr in ("smirk", "menacing"):
            draw.arc([mouth_x - 4 * scale, mouth_y - 2 * scale, mouth_x + 10 * scale, mouth_y + 8 * scale], start=0, end=180, fill=(20, 20, 25), width=max(2, int(2.5 * scale)))
        elif expr in ("angry", "furious"):
            draw.line([mouth_x - 8 * scale, mouth_y + 4 * scale, mouth_x + 8 * scale, mouth_y - 2 * scale], fill=(20, 20, 25), width=max(2, int(3 * scale)))
        else:
            draw.line([mouth_x - 5 * scale, mouth_y, mouth_x + 7 * scale, mouth_y], fill=(20, 20, 25), width=max(2, int(2 * scale)))

        # Mustache trait (Majestic Curved Aristocratic Handlebar Mustache for God's Knights)
        if "mustache" in traits and not is_skeleton:
            must_y = mouth_y - 4 * scale
            # Left wing swooping out and curving up
            m_l = [
                (mouth_x, must_y),
                (mouth_x - 8 * scale, must_y - 2 * scale),
                (mouth_x - 18 * scale, must_y - 6 * scale),
                (mouth_x - 22 * scale, must_y - 12 * scale),
                (mouth_x - 17 * scale, must_y - 7 * scale),
                (mouth_x - 10 * scale, must_y + 2 * scale)
            ]
            draw.polygon(m_l, fill=(20, 20, 25), outline=(15, 15, 20))
            # Right wing swooping out and curving up
            m_r = [
                (mouth_x, must_y),
                (mouth_x + 8 * scale, must_y - 2 * scale),
                (mouth_x + 18 * scale, must_y - 6 * scale),
                (mouth_x + 22 * scale, must_y - 12 * scale),
                (mouth_x + 17 * scale, must_y - 7 * scale),
                (mouth_x + 10 * scale, must_y + 2 * scale)
            ]
            draw.polygon(m_r, fill=(20, 20, 25), outline=(15, 15, 20))

        # Cigarette trait (Sanji Signature with Pulsing Cherry & Animated Rising Smoke Waves)
        if "cigarette" in traits:
            cg_x = mouth_x + (5 * facing) * scale
            cg_y = mouth_y + 1 * scale
            cg_end_x = cg_x + (17 * facing) * scale
            cg_end_y = cg_y + 4 * scale
            draw.line([cg_x, cg_y, cg_end_x, cg_end_y], fill=(250, 250, 250), width=max(2, int(3 * scale)))
            # Pulsing glowing cherry ember
            ember_intensity = 0.5 + 0.5 * math.sin(t * 5.0)
            cherry_col = (255, int(60 + 50 * ember_intensity), 20)
            draw.ellipse([cg_end_x - 2.5 * scale, cg_end_y - 2.5 * scale, cg_end_x + 2.5 * scale, cg_end_y + 2.5 * scale], fill=cherry_col)
            # Animated rising curling smoke wisps over time t
            wisp_1_x = cg_end_x + math.sin(t * 3.5) * 4 * scale
            wisp_1_y = cg_end_y - 10 * scale - (t * 12 * scale) % (20 * scale)
            draw.arc([wisp_1_x - 4 * scale, wisp_1_y - 6 * scale, wisp_1_x + 6 * scale, wisp_1_y + 6 * scale], start=180, end=330, fill=(210, 220, 235), width=max(1, int(1.5 * scale)))
            wisp_2_x = cg_end_x + math.cos(t * 2.8) * 7 * scale
            wisp_2_y = cg_end_y - 22 * scale - (t * 10 * scale) % (24 * scale)
            draw.arc([wisp_2_x - 6 * scale, wisp_2_y - 8 * scale, wisp_2_x + 8 * scale, wisp_2_y + 8 * scale], start=160, end=310, fill=(190, 205, 225), width=max(1, int(1.5 * scale)))

        # Triple Earring trait (Zoro Signature)
        if "triple_earring" in traits:
            ear_x = hx - (r * 0.95 * facing)
            ear_y = hy + 6 * scale
            for e_i in range(3):
                offset_x = (e_i * 3.5 * facing) * scale
                draw.ellipse([ear_x + offset_x - 1.5 * scale, ear_y + 2 * scale, ear_x + offset_x + 1.5 * scale, ear_y + 8 * scale], fill=(255, 215, 0), outline=(120, 100, 10))

        # 7. Foreground Hair Silhouette Layer
        if hair_style == "blonde_sweep":
            draw.pieslice([hx - r, hy - r, hx + r, hy + r], start=180, end=0, fill=hair_col)
            bang_pts = [
                (hx - r * 0.8, hy - r * 0.5),
                (hx + (r * 0.2 * facing), hy - r * 0.9),
                (hx + (r * 0.9 * facing), hy - r * 0.2),
                (hx + (r * 1.25 * facing), hy + r * 0.45),
                (hx + (r * 0.85 * facing), hy + r * 0.2),
                (hx + (r * 1.15 * facing), hy + r * 0.75),
                (hx + (r * 0.5 * facing), hy + r * 0.5),
                (hx - (r * 0.2 * facing), hy + r * 0.1)
            ]
            draw.polygon(bang_pts, fill=hair_col, outline=(20, 20, 25))

        elif hair_style == "green_crop":
            draw.pieslice([hx - r, hy - r, hx + r, hy + r], start=180, end=0, fill=hair_col)
            for sp_i in range(-3, 4):
                sp_x = hx + (sp_i * 7 * scale)
                sp_y = hy - r - 2 * scale
                draw.polygon([(sp_x - 4 * scale, sp_y + 5 * scale), (sp_x, sp_y - 6 * scale), (sp_x + 4 * scale, sp_y + 5 * scale)], fill=hair_col)

        elif hair_style == "spiky_black":
            draw.pieslice([hx - r, hy - r, hx + r, hy + r], start=180, end=0, fill=hair_col)
            for sp_i in range(-4, 5):
                sp_x = hx + (sp_i * 6 * scale)
                sp_y = hy - r - 2 * scale
                spike_len = 10 * scale if abs(sp_i) in (1, 3) else 7 * scale
                draw.polygon([(sp_x - 5 * scale, sp_y + 6 * scale), (sp_x, sp_y - spike_len), (sp_x + 5 * scale, sp_y + 6 * scale)], fill=hair_col, outline=(20, 20, 25))

        elif hair_style in ("curly_short", "wavy_short"):
            # Natural layered waves hugging head contours (No chef-hat puffy spheres!)
            draw.pieslice([hx - r * 1.05, hy - r * 1.05, hx + r * 1.05, hy + r * 0.95], start=180, end=0, fill=hair_col, outline=(20, 20, 25), width=1)
            for w_i in range(-3, 4):
                wx = hx + (w_i * 7.5 * scale)
                wy = hy - r * 0.75 + (abs(w_i) * 2 * scale)
                outline_shade = (30, 30, 35) if hair_color == "white" else (240, 240, 245)
                draw.arc([wx - 6 * scale, wy - 6 * scale, wx + 6 * scale, wy + 6 * scale], start=160, end=340, fill=outline_shade, width=max(1, int(1.8 * scale)))
            draw.polygon([(hx - r * 0.95, hy - r * 0.3), (hx - r * 1.05, hy + r * 0.35), (hx - r * 0.75, hy)], fill=hair_col, outline=(20, 20, 25))
            draw.polygon([(hx + r * 0.95, hy - r * 0.3), (hx + r * 1.05, hy + r * 0.35), (hx + r * 0.75, hy)], fill=hair_col, outline=(20, 20, 25))

        elif hair_style == "regal_wavy":
            # Crown hair cap - Guarantees NO BALD SPOTS for Killingham or nobles
            draw.pieslice([hx - r, hy - r, hx + r, hy + r], start=180, end=0, fill=hair_col)
            draw.polygon([
                (hx - r * 0.8, hy - r * 0.4),
                (hx, hy - r * 0.1),
                (hx + r * 0.8, hy - r * 0.4),
                (hx, hy - r * 0.9)
            ], fill=hair_col, outline=(20, 20, 25))

        elif hair_style == "twin_tails":
            # Gunko front bangs and crown cap
            draw.pieslice([hx - r, hy - r, hx + r, hy + r], start=180, end=0, fill=hair_col)
            draw.polygon([
                (hx - r * 0.85, hy - r * 0.35),
                (hx - r * 0.4, hy + r * 0.15),
                (hx, hy - r * 0.25),
                (hx + r * 0.4, hy + r * 0.15),
                (hx + r * 0.85, hy - r * 0.35),
                (hx, hy - r * 0.9)
            ], fill=hair_col, outline=(20, 20, 25))

        elif hair_style == "long_hair":
            draw.pieslice([hx - r, hy - r, hx + r, hy + r], start=180, end=0, fill=hair_col)
            draw.polygon([(hx - r * 0.9, hy - r * 0.3), (hx - r * 0.6, hy + r * 0.5), (hx - r * 0.4, hy - r * 0.2)], fill=hair_col, outline=(20, 20, 25))
            draw.polygon([(hx + r * 0.9, hy - r * 0.3), (hx + r * 0.6, hy + r * 0.5), (hx + r * 0.4, hy - r * 0.2)], fill=hair_col, outline=(20, 20, 25))

        elif hair_style == "ponytail":
            draw.pieslice([hx - r, hy - r, hx + r, hy + r], start=180, end=0, fill=hair_col)
            draw.line([hx - r * 0.6, hy - r * 0.5, hx - facing * r * 0.7, hy - r * 0.8], fill=(30, 30, 35), width=max(1, int(1.5 * scale)))
            draw.line([hx + r * 0.6, hy - r * 0.5, hx - facing * r * 0.7, hy - r * 0.8], fill=(30, 30, 35), width=max(1, int(1.5 * scale)))

        elif hair_style == "bob_cut":
            draw.pieslice([hx - r * 1.05, hy - r * 1.05, hx + r * 1.05, hy + r * 1.05], start=180, end=0, fill=hair_col)
            bob_pts = [
                (hx - r * 1.05, hy - r * 0.3),
                (hx - r * 1.15, hy + r * 0.8),
                (hx - r * 0.7, hy + r * 0.85),
                (hx - r * 0.6, hy + r * 0.1),
                (hx + r * 0.6, hy + r * 0.1),
                (hx + r * 0.7, hy + r * 0.85),
                (hx + r * 1.15, hy + r * 0.8),
                (hx + r * 1.05, hy - r * 0.3)
            ]
            draw.polygon(bob_pts, fill=hair_col, outline=(20, 20, 25))

        elif hair_style == "high_bun":
            draw.pieslice([hx - r, hy - r, hx + r, hy + r], start=180, end=0, fill=hair_col)
            bun_y = hy - r - 12 * scale
            draw.ellipse([hx - 10 * scale, bun_y - 10 * scale, hx + 10 * scale, bun_y + 10 * scale], fill=hair_col, outline=(20, 20, 25), width=max(1, int(2 * scale)))

    def _draw_clothing_torso(self, draw: ImageDraw.ImageDraw, hx: float, hy: float,
                             pelvis_x: float, pelvis_y: float, shoulder_x: float, shoulder_y: float,
                             facing: int, clothing_type: str = "shirt", clothing_color: str = "white"):
        """
        Cinema-Grade Torso Clothing Engine:
        Renders colored tailored garments (suit, corset, officer coat, robe, vest, shirt)
        fitting perfectly over parametric stickman skeletal kinematics.
        """
        scale = self.scale
        col = CLOTHING_COLORS.get(clothing_color.lower(), (242, 244, 250))
        sh_w = self.shoulder_width
        hip_w = self.hip_width

        sh_l = (shoulder_x - sh_w, shoulder_y)
        sh_r = (shoulder_x + sh_w, shoulder_y)
        hip_l = (pelvis_x - hip_w, pelvis_y)
        hip_r = (pelvis_x + hip_w, pelvis_y)

        if clothing_type == "suit":
            # Sanji Tailored Dark Suit
            draw.polygon([sh_l, sh_r, hip_r, hip_l], fill=col, outline=(15, 15, 20), width=max(1, int(2 * scale)))
            v_bottom_y = shoulder_y + (pelvis_y - shoulder_y) * 0.45
            draw.polygon([(shoulder_x - 9 * scale, shoulder_y), (shoulder_x + 9 * scale, shoulder_y), (shoulder_x, v_bottom_y)], fill=(250, 250, 250))
            draw.polygon([(shoulder_x - 3 * scale, shoulder_y), (shoulder_x + 3 * scale, shoulder_y), (shoulder_x + 4 * scale, v_bottom_y + 15 * scale), (shoulder_x, v_bottom_y + 22 * scale), (shoulder_x - 4 * scale, v_bottom_y + 15 * scale)], fill=(20, 20, 25))
            draw.line([sh_l[0] + 6 * scale, sh_l[1], shoulder_x, v_bottom_y], fill=(40, 42, 52), width=max(1, int(1.5 * scale)))
            draw.line([sh_r[0] - 6 * scale, sh_r[1], shoulder_x, v_bottom_y], fill=(40, 42, 52), width=max(1, int(1.5 * scale)))

        elif clothing_type == "corset":
            # Ivankov Hourglass Corset
            waist_y = shoulder_y + (pelvis_y - shoulder_y) * 0.55
            cinch_w = hip_w * 0.65
            c_sh_l = (shoulder_x - sh_w * 0.9, shoulder_y + 5 * scale)
            c_sh_r = (shoulder_x + sh_w * 0.9, shoulder_y + 5 * scale)
            w_l = (shoulder_x - cinch_w, waist_y)
            w_r = (shoulder_x + cinch_w, waist_y)
            draw.polygon([c_sh_l, c_sh_r, w_r, hip_r, hip_l, w_l], fill=col, outline=(20, 20, 25), width=max(1, int(2 * scale)))
            draw.arc([shoulder_x - 14 * scale, shoulder_y - 2 * scale, shoulder_x + 14 * scale, shoulder_y + 14 * scale], start=0, end=180, fill=(20, 20, 25), width=max(1, int(1.8 * scale)))
            for ly_i in range(1, 4):
                ly = shoulder_y + 12 * scale + (ly_i * 9 * scale)
                draw.line([shoulder_x - 6 * scale, ly, shoulder_x + 6 * scale, ly], fill=(235, 195, 40), width=max(1, int(2 * scale)))

        elif clothing_type == "knight_armor":
            # Saint Killingham / God's Knight Battle Armor with Winged Golden Pauldrons & Flowing Mantle
            mantle_bottom_y = pelvis_y + 36 * scale
            # 1. Noble dark mantle/cape flowing behind torso
            mantle_l = (shoulder_x - sh_w * 1.35, mantle_bottom_y)
            mantle_r = (shoulder_x + sh_w * 1.35, mantle_bottom_y)
            draw.polygon([sh_l, sh_r, mantle_r, (shoulder_x, mantle_bottom_y - 8 * scale), mantle_l], fill=(16, 14, 22), outline=(10, 10, 15))
            # 2. Metallic cuirass / breastplate
            draw.polygon([sh_l, sh_r, hip_r, hip_l], fill=col, outline=(255, 215, 0), width=max(1, int(2.5 * scale)))
            # Gold filigree chest crest
            chest_mid_y = shoulder_y + (pelvis_y - shoulder_y) * 0.45
            draw.line([shoulder_x, shoulder_y + 4 * scale, shoulder_x, pelvis_y - 6 * scale], fill=(255, 215, 0), width=max(1, int(2 * scale)))
            draw.line([shoulder_x - 12 * scale, chest_mid_y, shoulder_x + 12 * scale, chest_mid_y], fill=(255, 215, 0), width=max(1, int(2 * scale)))
            draw.polygon([(shoulder_x - 8 * scale, chest_mid_y - 8 * scale), (shoulder_x + 8 * scale, chest_mid_y - 8 * scale), (shoulder_x, chest_mid_y + 6 * scale)], outline=(255, 215, 0), fill=(40, 35, 15))
            # 3. Spiked / Winged Golden Pauldrons
            paul_l = [(sh_l[0] - 12 * scale, sh_l[1] - 8 * scale), (sh_l[0] + 4 * scale, sh_l[1] - 4 * scale), (sh_l[0] + 2 * scale, sh_l[1] + 10 * scale), (sh_l[0] - 14 * scale, sh_l[1] + 4 * scale)]
            paul_r = [(sh_r[0] + 12 * scale, sh_r[1] - 8 * scale), (sh_r[0] - 4 * scale, sh_r[1] - 4 * scale), (sh_r[0] - 2 * scale, sh_r[1] + 10 * scale), (sh_r[0] + 14 * scale, sh_r[1] + 4 * scale)]
            draw.polygon(paul_l, fill=(235, 195, 35), outline=(20, 20, 25), width=max(1, int(1.5 * scale)))
            draw.polygon(paul_r, fill=(235, 195, 35), outline=(20, 20, 25), width=max(1, int(1.5 * scale)))

        elif clothing_type == "centaur_cloak":
            # Saint Sommers Centaur Cloak & Armor
            draw.polygon([sh_l, sh_r, (pelvis_x + hip_w * 1.5, pelvis_y + 20 * scale), (pelvis_x - hip_w * 1.5, pelvis_y + 20 * scale)], fill=col, outline=(20, 20, 25), width=max(1, int(2 * scale)))
            draw.line([sh_l[0], sh_l[1], sh_r[0], sh_r[1]], fill=(225, 45, 60), width=max(2, int(4 * scale)))

        elif clothing_type == "officer_coat":
            # Aristocratic Noble Trench Coat with Epaulets & Gold Buttons
            coat_flare = 8 * scale
            coat_bottom_y = pelvis_y + 24 * scale
            epaulet_l = (shoulder_x - sh_w - coat_flare, shoulder_y - 2 * scale)
            epaulet_r = (shoulder_x + sh_w + coat_flare, shoulder_y - 2 * scale)
            tail_l = (pelvis_x - hip_w - 6 * scale, coat_bottom_y)
            tail_r = (pelvis_x + hip_w + 6 * scale, coat_bottom_y)
            draw.polygon([epaulet_l, epaulet_r, tail_r, (pelvis_x, coat_bottom_y - 4 * scale), tail_l], fill=col, outline=(20, 20, 25), width=max(1, int(2 * scale)))
            draw.line([epaulet_l[0], epaulet_l[1], sh_l[0], sh_l[1]], fill=(255, 215, 0), width=max(2, int(4 * scale)))
            draw.line([epaulet_r[0], epaulet_r[1], sh_r[0], sh_r[1]], fill=(255, 215, 0), width=max(2, int(4 * scale)))
            for b_i in range(3):
                by = shoulder_y + 12 * scale + (b_i * 12 * scale)
                draw.ellipse([shoulder_x - 7 * scale - 2, by - 2, shoulder_x - 7 * scale + 2, by + 2], fill=(255, 215, 0))
                draw.ellipse([shoulder_x + 7 * scale - 2, by - 2, shoulder_x + 7 * scale + 2, by + 2], fill=(255, 215, 0))

        elif clothing_type == "robe":
            # Zoro Samurai Martial Arts Gi with Obi Sash
            draw.polygon([sh_l, sh_r, hip_r, hip_l], fill=col, outline=(20, 20, 25), width=max(1, int(2 * scale)))
            draw.line([sh_l[0] + 5 * scale, sh_l[1], pelvis_x + 4 * scale, pelvis_y - 12 * scale], fill=(30, 30, 35), width=max(2, int(2.5 * scale)))
            draw.line([sh_r[0] - 5 * scale, sh_r[1], pelvis_x - 6 * scale, pelvis_y - 6 * scale], fill=(30, 30, 35), width=max(2, int(2.5 * scale)))
            obi_y = pelvis_y - 15 * scale
            draw.rectangle([pelvis_x - hip_w - 2, obi_y, pelvis_x + hip_w + 2, pelvis_y], fill=(35, 120, 50), outline=(20, 20, 25), width=1)

        elif clothing_type == "vest":
            # Luffy Vest
            draw.polygon([sh_l, sh_r, hip_r, hip_l], fill=col, outline=(20, 20, 25), width=max(1, int(2 * scale)))
            draw.line([shoulder_x, shoulder_y, shoulder_x, pelvis_y - 10 * scale], fill=(224, 172, 105), width=max(2, int(4 * scale)))

        else:
            draw.polygon([sh_l, sh_r, hip_r, hip_l], fill=col, outline=(20, 20, 25), width=max(1, int(2 * scale)))

    def _draw_expression(self, draw: ImageDraw.ImageDraw, hx: float, hy: float, expr: str, facing: int):
        r = self.head_radius
        if expr == "neutral":
            draw.ellipse([hx + (6 * facing) - 3, hy - 4 - 3, hx + (6 * facing) + 3, hy - 4 + 3], fill=self.color)
        elif expr == "smirk":
            x_a = hx + (2 * facing)
            x_b = hx + (14 * facing)
            draw.line([x_a, hy - 10, x_b, hy - 7], fill=self.color, width=2)
            x_c = hx + (16 * facing)
            draw.arc([min(x_a, x_c), hy + 2, max(x_a, x_c), hy + 14], start=0, end=180, fill=self.color, width=2)
        elif expr == "shocked":
            draw.ellipse([hx + (4 * facing) - 4, hy - 8 - 4, hx + (4 * facing) + 4, hy - 8 + 4], fill=self.color)
            draw.ellipse([hx + (8 * facing) - 4, hy + 4 - 4, hx + (8 * facing) + 4, hy + 4 + 4], outline=self.color, width=2)
            draw.line([hx + (20 * facing), hy - 18, hx + (25 * facing), hy - 10], fill=(0, 220, 255), width=3)
        elif expr == "deadpan":
            draw.line([hx + (2 * facing), hy - 5, hx + (12 * facing), hy - 5], fill=self.color, width=3)
        elif expr == "smile":
            draw.arc([hx - 10, hy - 2, hx + 10, hy + 16], start=0, end=180, fill=self.color, width=3)
        elif expr == "angry":
            # Fierce focused eyes and brows
            draw.line([hx + (2 * facing), hy - 6, hx + (14 * facing), hy - 11], fill=self.color, width=2)
            draw.ellipse([hx + (7 * facing) - 3, hy - 4 - 2, hx + (7 * facing) + 3, hy - 4 + 2], fill=self.color)
            draw.line([hx + (2 * facing), hy + 8, hx + (12 * facing), hy + 5], fill=self.color, width=2)
        else:
            # Safe default fallback
            draw.ellipse([hx + (6 * facing) - 3, hy - 4 - 3, hx + (6 * facing) + 3, hy - 4 + 3], fill=self.color)

    def _draw_head_accessory(self, draw: ImageDraw.ImageDraw, hx: float, hy: float, facing: int, accessory: str):
        if not accessory or accessory == "none":
            return
        r = self.head_radius * 1.12
        scale = self.scale

        if accessory == "straw_hat":
            # Gold brim
            brim_y = hy - r * 0.75
            draw.line([hx - 46 * scale, brim_y, hx + 46 * scale, brim_y], fill=(255, 215, 0), width=max(3, int(6 * scale)))
            # Dome / Crown
            draw.pieslice([hx - 25 * scale, brim_y - 28 * scale, hx + 25 * scale, brim_y + 10 * scale], start=180, end=0, fill=(245, 210, 35), outline=(20, 20, 25), width=1)
            # Red ribbon
            draw.line([hx - 24 * scale, brim_y - 3 * scale, hx + 24 * scale, brim_y - 3 * scale], fill=(255, 45, 85), width=max(2, int(5 * scale)))

        elif accessory == "red_beanie":
            # Crimson folded beanie
            draw.arc([hx - 30 * scale, hy - 34 * scale, hx + 30 * scale, hy - 6 * scale], start=180, end=0, fill=(255, 45, 85), width=max(4, int(7 * scale)))

        elif accessory == "headphones":
            # Cyan headband arc over head
            draw.arc([hx - r - 6 * scale, hy - r - 8 * scale, hx + r + 6 * scale, hy + 4 * scale], start=160, end=20, fill=(0, 220, 255), width=max(2, int(4 * scale)))
            # Ear cups
            cup_w, cup_h = 7 * scale, 12 * scale
            draw.ellipse([hx - r - 6 * scale - cup_w, hy - cup_h, hx - r - 6 * scale + cup_w, hy + cup_h], fill=(0, 220, 255))
            draw.ellipse([hx + r + 6 * scale - cup_w, hy - cup_h, hx + r + 6 * scale + cup_w, hy + cup_h], fill=(0, 220, 255))

        elif accessory == "glasses":
            # Frames and bridge
            gw = 12 * scale
            draw.rectangle([hx - gw - 2, hy - 10 * scale, hx - 2, hy + 2 * scale], outline=(0, 220, 255), width=2)
            draw.rectangle([hx + 2, hy - 10 * scale, hx + gw + 2, hy + 2 * scale], outline=(0, 220, 255), width=2)
            draw.line([hx - 2, hy - 4 * scale, hx + 2, hy - 4 * scale], fill=(0, 220, 255), width=2)

        elif accessory == "crown":
            # Gold royal crown with points
            cy_top = hy - r - 16 * scale
            pts = [
                (hx - 25 * scale, hy - r + 2),
                (hx - 28 * scale, cy_top),
                (hx - 10 * scale, cy_top + 10 * scale),
                (hx, cy_top - 4 * scale),
                (hx + 10 * scale, cy_top + 10 * scale),
                (hx + 28 * scale, cy_top),
                (hx + 25 * scale, hy - r + 2)
            ]
            draw.polygon(pts, outline=(255, 215, 0), fill=(40, 35, 10))

        elif accessory == "headband":
            # Ninja forehead protector
            hb_y = hy - 10 * scale
            draw.line([hx - r - 2, hb_y, hx + r + 2, hb_y], fill=(30, 30, 40), width=max(3, int(6 * scale)))
            draw.rectangle([hx - 12 * scale, hb_y - 4 * scale, hx + 12 * scale, hb_y + 4 * scale], fill=(200, 215, 230), outline=(255, 255, 255), width=1)

        elif accessory == "tie":
            # Corporate necktie
            neck_y = hy + r
            draw.polygon([
                (hx - 4 * scale, neck_y + 10 * scale),
                (hx + 4 * scale, neck_y + 10 * scale),
                (hx + 8 * scale, neck_y + 55 * scale),
                (hx, neck_y + 68 * scale),
                (hx - 8 * scale, neck_y + 55 * scale)
            ], fill=(255, 45, 85))

        elif accessory == "horns":
            # Beast horns on head anchored to upper temples
            horn_col = (235, 225, 205)
            draw.line([hx - 18 * scale, hy - r * 0.7, hx - 34 * scale, hy - r - 12 * scale], fill=horn_col, width=max(3, int(5 * scale)))
            draw.line([hx - 34 * scale, hy - r - 12 * scale, hx - 22 * scale, hy - r - 22 * scale], fill=horn_col, width=max(2, int(4 * scale)))
            draw.line([hx + 18 * scale, hy - r * 0.7, hx + 34 * scale, hy - r - 12 * scale], fill=horn_col, width=max(3, int(5 * scale)))
            draw.line([hx + 34 * scale, hy - r - 12 * scale, hx + 22 * scale, hy - r - 22 * scale], fill=horn_col, width=max(2, int(4 * scale)))

        elif accessory == "top_hat":
            # Elegant gentleman top hat (Brook signature)
            brim_y = hy - r * 0.95
            draw.line([hx - 36 * scale, brim_y, hx + 36 * scale, brim_y], fill=(30, 32, 40), width=max(3, int(5 * scale)))
            hat_top_y = brim_y - 40 * scale
            draw.polygon([
                (hx - 20 * scale, brim_y),
                (hx - 22 * scale, hat_top_y),
                (hx + 22 * scale, hat_top_y),
                (hx + 20 * scale, brim_y)
            ], fill=(25, 27, 35), outline=(15, 15, 20), width=1)
            # Crimson silk ribbon band
            draw.line([hx - 20 * scale, brim_y - 7 * scale, hx + 20 * scale, brim_y - 7 * scale], fill=(225, 35, 60), width=max(2, int(5 * scale)))

    def _draw_socket_attachment(self, draw: ImageDraw.ImageDraw, socket: str, item: str,
                               pos: Tuple[float, float], facing: int, action: str,
                               hx: float, hy: float, lead_knee: Tuple[float, float]):
        """
        Universal Socket Drawing Engine:
        Renders any item mounted to any named socket on the stickman.
        Universal, dynamic, and directed by Gemini without hardcoded character names.
        """
        if not item or item == "none":
            return
        scale = self.scale
        r = self.head_radius

        if socket == "head":
            self._draw_head_accessory(draw, hx, hy, facing, item)

        elif socket == "mouth":
            mx, my = pos[0], pos[1]
            if item == "cigarette":
                # Realistic stickman cigarette: white cylinder, cherry ember & smoke wisp
                cig_len = 13 * scale
                tip_x = mx + (cig_len * facing)
                tip_y = my + 3 * scale
                draw.line([mx, my, tip_x, tip_y], fill=(245, 245, 245), width=max(2, int(3 * scale)))
                # Glowing cherry ember
                draw.ellipse([tip_x - 1.5 * scale, tip_y - 1.5 * scale, tip_x + 1.5 * scale, tip_y + 1.5 * scale], fill=(255, 80, 0))
                # Rising smoke curls
                draw.arc([tip_x - 3 * scale, tip_y - 12 * scale, tip_x + 8 * scale, tip_y], start=200, end=340, fill=(210, 220, 235), width=1)
                draw.arc([tip_x + 2 * scale, tip_y - 20 * scale, tip_x + 14 * scale, tip_y - 8 * scale], start=180, end=320, fill=(190, 205, 220), width=1)

            elif item == "blade":
                # Katana held horizontally in mouth
                blade_len = 75 * scale
                bx_tip = mx + (blade_len * facing)
                draw.line([mx - (25 * facing) * scale, my, bx_tip, my - 4 * scale], fill=(220, 235, 255), width=max(3, int(4 * scale)))
                draw.line([mx + 4 * facing * scale, my - 6 * scale, mx + 4 * facing * scale, my + 6 * scale], fill=(255, 215, 0), width=3)
                draw.line([mx - (25 * facing) * scale, my, mx, my], fill=(200, 35, 35), width=max(3, int(5 * scale)))

            elif item == "smoke":
                smk_col = (200, 210, 225)
                draw.ellipse([mx + 5 * facing * scale, my - 8 * scale, mx + 20 * facing * scale, my + 4 * scale], outline=smk_col, width=1)

        elif socket in ("lead_hand", "rear_hand"):
            hx1, hy1 = pos[0], pos[1]
            if item == "spear":
                # Spear of Longinus (Killingham God's Knight Polearm)
                shaft_len = 135 * scale
                shaft_w = max(3, int(4 * scale))
                if action in ("spear_thrust", "punch", "point", "barrage"):
                    sp_x2 = hx1 + (shaft_len * facing)
                    sp_y2 = hy1 - 4 * scale
                    sp_x1 = hx1 - (45 * facing) * scale
                    sp_y1 = hy1 + 6 * scale
                else:
                    sp_x2 = hx1 + (22 * facing) * scale
                    sp_y2 = hy1 - 100 * scale
                    sp_x1 = hx1 - (18 * facing) * scale
                    sp_y1 = hy1 + 50 * scale
                # Dark obsidian / steel pole shaft
                draw.line([sp_x1, sp_y1, sp_x2, sp_y2], fill=(42, 45, 55), width=shaft_w)
                # Golden ferrules / rings along shaft
                draw.line([hx1 - 4 * facing * scale, hy1, hx1 + 4 * facing * scale, hy1], fill=(255, 215, 0), width=shaft_w + 2)
                # Imposing ornate Spear of Longinus dual-pronged or diamond tip
                tip_len = 34 * scale
                tip_w = 10 * scale
                s_ang = math.atan2(sp_y2 - sp_y1, sp_x2 - sp_x1)
                t_tip = (sp_x2 + math.cos(s_ang) * tip_len, sp_y2 + math.sin(s_ang) * tip_len)
                t_left = (sp_x2 + math.cos(s_ang + 2.3) * tip_w, sp_y2 + math.sin(s_ang + 2.3) * tip_w)
                t_right = (sp_x2 + math.cos(s_ang - 2.3) * tip_w, sp_y2 + math.sin(s_ang - 2.3) * tip_w)
                # Crimson / golden glowing blade head
                draw.polygon([t_left, t_tip, t_right, (sp_x2, sp_y2)], fill=(225, 35, 50), outline=(255, 215, 0), width=max(1, int(1.5 * scale)))
                draw.line([(sp_x2, sp_y2), t_tip], fill=(255, 240, 240), width=max(1, int(2 * scale)))

            elif item in ("blade", "rapier"):
                blade_len = 82 * scale
                bx2 = hx1 + (blade_len * facing)
                by2 = hy1 - 10 * scale if action in ("punch", "point") else hy1 + 45 * scale
                # Slender rapier steel vs heavier katana blade
                blade_w = max(2, int(3 * scale if item == "rapier" else 5 * scale))
                draw.line([hx1, hy1, bx2, by2], fill=(230, 240, 255), width=blade_w)
                if item == "rapier":
                    # Aristocratic cup hilt and knuckle bow
                    draw.arc([hx1 - 8 * scale, hy1 - 8 * scale, hx1 + 8 * scale, hy1 + 8 * scale], start=0, end=360, fill=(255, 215, 0), width=max(2, int(2.5 * scale)))
                    draw.line([hx1 - (12 * facing) * scale, hy1 + 4 * scale, hx1, hy1], fill=(40, 42, 50), width=max(2, int(4 * scale)))
                else:
                    draw.line([hx1 - (12 * facing) * scale, hy1 + 6 * scale, hx1, hy1], fill=(200, 35, 35), width=max(4, int(6 * scale)))
                    draw.line([hx1 - 4 * scale, hy1 - 6 * scale, hx1 + 4 * scale, hy1 + 6 * scale], fill=(255, 215, 0), width=3)

            elif item == "flame":
                # Fire fist strike
                if action not in ("punch", "point", "run", "celebrate", "barrage"):
                    return
                pts = [
                    (hx1 - (15 * facing) * scale, hy1 - 16 * scale),
                    (hx1 + (45 * facing) * scale, hy1 - 14 * scale),
                    (hx1 + (32 * facing) * scale, hy1),
                    (hx1 + (48 * facing) * scale, hy1 + 14 * scale),
                    (hx1 - (12 * facing) * scale, hy1 + 16 * scale),
                ]
                draw.polygon(pts, fill=(255, 120, 0))
                pts_core = [
                    (hx1 - (6 * facing) * scale, hy1 - 8 * scale),
                    (hx1 + (30 * facing) * scale, hy1),
                    (hx1 - (6 * facing) * scale, hy1 + 8 * scale),
                ]
                draw.polygon(pts_core, fill=(255, 240, 50))

            elif item == "shield":
                draw.ellipse([hx1 - 18 * scale, hy1 - 18 * scale, hx1 + 18 * scale, hy1 + 18 * scale], outline=(0, 220, 255), width=3, fill=(15, 25, 40))
                draw.ellipse([hx1 - 9 * scale, hy1 - 9 * scale, hx1 + 9 * scale, hy1 + 9 * scale], outline=(255, 215, 0), width=2)

        elif socket in ("lead_foot", "rear_foot"):
            fx, fy = pos[0], pos[1]
            if item == "flame":
                # Diable / Ifrit Jambe Flames (Active in kicks, flame strikes, and locked_in stance)
                if action in ("kick", "flame_strike", "run", "barrage"):
                    if lead_knee:
                        draw.line([lead_knee[0], lead_knee[1], fx, fy], fill=(255, 120, 0), width=max(6, int(10 * scale)))
                        draw.line([lead_knee[0], lead_knee[1], fx, fy], fill=(255, 240, 40), width=max(3, int(5 * scale)))
                    pts_burst = [
                        (fx - (14 * facing) * scale, fy - 20 * scale),
                        (fx + (50 * facing) * scale, fy - 28 * scale),
                        (fx + (35 * facing) * scale, fy - 4 * scale),
                        (fx + (60 * facing) * scale, fy + 8 * scale),
                        (fx + (28 * facing) * scale, fy + 22 * scale),
                        (fx - (12 * facing) * scale, fy + 18 * scale),
                    ]
                    draw.polygon(pts_burst, fill=(255, 90, 0))
                    pts_core = [
                        (fx - (6 * facing) * scale, fy - 12 * scale),
                        (fx + (32 * facing) * scale, fy - 14 * scale),
                        (fx + (40 * facing) * scale, fy + 2 * scale),
                        (fx + (24 * facing) * scale, fy + 14 * scale),
                        (fx - (6 * facing) * scale, fy + 10 * scale),
                    ]
                    draw.polygon(pts_core, fill=(255, 240, 50))
                elif action == "locked_in":
                    # Concentrated heat aura and ground flames licking up the planted shin
                    if lead_knee:
                        draw.line([lead_knee[0], lead_knee[1], fx, fy], fill=(255, 110, 20), width=max(4, int(7 * scale)))
                        draw.line([lead_knee[0], lead_knee[1], fx, fy], fill=(255, 230, 60), width=max(2, int(3 * scale)))
                    ground_flame_pts = [
                        (fx - 16 * scale, fy + 4 * scale),
                        (fx - 10 * scale, fy - 18 * scale),
                        (fx - 2 * scale, fy - 6 * scale),
                        (fx + 6 * scale, fy - 24 * scale),
                        (fx + 12 * scale, fy - 8 * scale),
                        (fx + 18 * scale, fy + 4 * scale)
                    ]
                    draw.polygon(ground_flame_pts, fill=(255, 100, 0))
                    draw.polygon([(fx - 8 * scale, fy + 4 * scale), (fx, fy - 14 * scale), (fx + 8 * scale, fy + 4 * scale)], fill=(255, 240, 50))
                elif action in ("flying", "air_dash"):
                    # High-velocity horizontal rocket thruster flame streaming behind trailing foot
                    if lead_knee:
                        draw.line([lead_knee[0], lead_knee[1], fx, fy], fill=(255, 130, 0), width=max(4, int(7 * scale)))
                    pts_jet = [
                        (fx, fy - 10 * scale),
                        (fx - (68 * facing) * scale, fy - 18 * scale),
                        (fx - (45 * facing) * scale, fy - 2 * scale),
                        (fx - (82 * facing) * scale, fy + 8 * scale),
                        (fx - (35 * facing) * scale, fy + 14 * scale),
                        (fx, fy + 12 * scale),
                    ]
                    draw.polygon(pts_jet, fill=(255, 90, 0))
                    draw.polygon([(fx, fy - 6 * scale), (fx - (45 * facing) * scale, fy), (fx, fy + 6 * scale)], fill=(255, 240, 50))


            elif item == "smoke":
                trail_x = fx - (20 * facing) * scale
                draw.ellipse([trail_x - 12 * scale, fy - 14 * scale, trail_x + 12 * scale, fy + 2 * scale], outline=(195, 205, 220), width=2)

        elif socket == "torso":
            tx, ty = pos[0], pos[1]
            if item == "cape":
                cape_col = (220, 35, 65)
                pts = [
                    (tx - 18 * scale, ty),
                    (tx + 18 * scale, ty),
                    (tx - (45 * facing) * scale, ty + 120 * scale),
                    (tx - (15 * facing) * scale, ty + 110 * scale),
                    (tx - (60 * facing) * scale, ty + 135 * scale),
                ]
                draw.polygon(pts, fill=cape_col)
            elif item == "tie":
                neck_y = ty - 15 * scale
                draw.polygon([
                    (tx - 4 * scale, neck_y + 10 * scale),
                    (tx + 4 * scale, neck_y + 10 * scale),
                    (tx + 8 * scale, neck_y + 55 * scale),
                    (tx, neck_y + 68 * scale),
                    (tx - 8 * scale, neck_y + 55 * scale)
                ], fill=(255, 45, 85))

    def _draw_name_hud(self, draw: ImageDraw.ImageDraw, hx: float, hy: float, name: str, has_tall_headwear: bool = False):
        if not name or name.strip().lower() in ("none", "", "thinker", "character_1", "character_2"):
            return
        scale = self.scale
        r = self.head_radius
        clean_name = name.strip().upper()[:16]

        from .layout import get_font
        font_tag = get_font(max(11, int(14 * scale)), bold=True)
        bbox = draw.textbbox((0, 0), clean_name, font=font_tag)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        # Clearance for horns, crown, or tall hats
        line_top_offset = (58 * scale) if has_tall_headwear else (38 * scale)
        line_start_y = hy - r - (12 * scale if has_tall_headwear else 2 * scale)
        tag_center_y = hy - r - line_top_offset

        # 1. Sleek vertical indicator line
        draw.line([hx, line_start_y, hx, tag_center_y + th // 2 + 5 * scale], fill=(130, 145, 170), width=max(1, int(1.5 * scale)))
        # Anchor pip on head
        draw.ellipse([hx - 2 * scale, line_start_y - 2 * scale, hx + 2 * scale, line_start_y + 2 * scale], fill=(0, 220, 255))

        # 2. Sleek gamer HUD glass tag
        pad_x = 8 * scale
        pad_y = 3 * scale
        tx = hx - tw // 2
        ty = tag_center_y - th // 2

        tag_outline = (0, 220, 255) if self.color == (255, 255, 255) else (255, 120, 40)
        draw.rounded_rectangle(
            [tx - pad_x, ty - pad_y, tx + tw + pad_x, ty + th + pad_y],
            radius=4 * scale,
            fill=(15, 18, 26),
            outline=tag_outline,
            width=1
        )
        draw.text((tx, ty), clean_name, font=font_tag, fill=(245, 245, 250))

    def draw(self, draw: ImageDraw.ImageDraw, t: float, action: str = "idle", expr: str = "neutral",
             direction: str = "right", speed: float = 1.0, accessory: str = "none", visual_trait: str = "none",
             attachments: Optional[Dict[str, str]] = None, custom_params: Dict[str, Any] = None,
             name: Optional[str] = None,
             skin_tone: str = "fair", hair_style: str = "bald", hair_color: str = "black",
             clothing_type: str = "shirt", clothing_color: str = "white",
             face_traits: Optional[List[str]] = None,
             motion_style: str = "combat_idle"):
        facing = 1 if direction == "right" else -1
        spd = normalize_speed(speed)

        hx = self.base_x
        hy = self.base_y - (self.torso_len + self.leg_upper + self.leg_lower + self.head_radius)
        torso_tilt = 0.0

        # Continuous alive body rhythm (breathing bob & subtle combat sway on all poses)
        base_breath = math.sin(t * 3.0 * spd) * (2.8 * self.scale)
        hy += base_breath

        if action == "idle":
            breath = math.sin(t * 2.5 * spd) * 3
            hy += breath
            chest_y = hy + self.head_radius + 20
            pelvis_x = hx
            pelvis_y = chest_y + self.torso_len - 20

            elbow_l = (hx - self.shoulder_width, chest_y + self.arm_upper)
            hand_l = (hx - self.shoulder_width - 5, elbow_l[1] + self.arm_lower)
            elbow_r = (hx + self.shoulder_width, chest_y + self.arm_upper)
            hand_r = (hx + self.shoulder_width + 5, elbow_r[1] + self.arm_lower)

            knee_l = (pelvis_x - 15, pelvis_y + self.leg_upper)
            foot_l = (pelvis_x - 15, knee_l[1] + self.leg_lower)
            knee_r = (pelvis_x + 15, pelvis_y + self.leg_upper)
            foot_r = (pelvis_x + 15, knee_r[1] + self.leg_lower)

        elif action == "walk":
            gait = t * 6.0 * spd
            bob = math.sin(gait * 2) * 5
            hy += bob
            chest_y = hy + self.head_radius + 20
            pelvis_x = hx
            pelvis_y = chest_y + self.torso_len - 20

            ang_l = math.sin(gait) * 0.45
            ang_r = math.sin(gait + math.pi) * 0.45

            knee_l = (pelvis_x - 10 + math.sin(ang_l) * self.leg_upper, pelvis_y + math.cos(ang_l) * self.leg_upper)
            foot_l = (knee_l[0] + math.sin(ang_l * 0.8) * self.leg_lower, knee_l[1] + math.cos(ang_l * 0.8) * self.leg_lower)
            knee_r = (pelvis_x + 10 + math.sin(ang_r) * self.leg_upper, pelvis_y + math.cos(ang_r) * self.leg_upper)
            foot_r = (knee_r[0] + math.sin(ang_r * 0.8) * self.leg_lower, knee_r[1] + math.cos(ang_r * 0.8) * self.leg_lower)

            elbow_l = (hx - self.shoulder_width + math.sin(-ang_l) * self.arm_upper, chest_y + math.cos(-ang_l) * self.arm_upper)
            hand_l = (elbow_l[0] + math.sin(-ang_l * 1.2) * self.arm_lower, elbow_l[1] + math.cos(-ang_l * 1.2) * self.arm_lower)
            elbow_r = (hx + self.shoulder_width + math.sin(-ang_r) * self.arm_upper, chest_y + math.cos(-ang_r) * self.arm_upper)
            hand_r = (elbow_r[0] + math.sin(-ang_r * 1.2) * self.arm_lower, elbow_r[1] + math.cos(-ang_r * 1.2) * self.arm_lower)

        elif action == "run":
            cadence = t * 14.0 * spd
            torso_tilt = 0.25 * facing
            bob = abs(math.sin(cadence)) * 12
            hy += bob
            chest_y = hy + self.head_radius + 15
            pelvis_x = hx - math.sin(torso_tilt) * self.torso_len
            pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len

            ang_l = math.sin(cadence) * 0.85
            ang_r = math.sin(cadence + math.pi) * 0.85

            knee_l = (pelvis_x + math.sin(ang_l) * self.leg_upper, pelvis_y + math.cos(ang_l) * self.leg_upper)
            foot_l = (knee_l[0] + math.sin(ang_l + 0.6) * self.leg_lower, knee_l[1] + math.cos(ang_l + 0.6) * self.leg_lower)
            knee_r = (pelvis_x + math.sin(ang_r) * self.leg_upper, pelvis_y + math.cos(ang_r) * self.leg_upper)
            foot_r = (knee_r[0] + math.sin(ang_r + 0.6) * self.leg_lower, knee_r[1] + math.cos(ang_r + 0.6) * self.leg_lower)

            elbow_l = (hx + math.sin(-ang_l) * self.arm_upper, chest_y + 10 + math.cos(-ang_l) * self.arm_upper)
            hand_l = (elbow_l[0] + math.sin(-ang_l + 0.9) * self.arm_lower, elbow_l[1] + math.cos(-ang_l + 0.9) * self.arm_lower)
            elbow_r = (hx + math.sin(-ang_r) * self.arm_upper, chest_y + 10 + math.cos(-ang_r) * self.arm_upper)
            hand_r = (elbow_r[0] + math.sin(-ang_r + 0.9) * self.arm_lower, elbow_r[1] + math.cos(-ang_r + 0.9) * self.arm_lower)

        elif action == "sit":
            hy = self.base_y - (self.torso_len + self.leg_lower + self.head_radius)
            chest_y = hy + self.head_radius + 15
            pelvis_x = hx
            pelvis_y = chest_y + self.torso_len - 15

            knee_l = (pelvis_x + (self.leg_upper * facing), pelvis_y)
            foot_l = (knee_l[0], knee_l[1] + self.leg_lower)
            knee_r = (pelvis_x + ((self.leg_upper - 5) * facing), pelvis_y)
            foot_r = (knee_r[0], knee_r[1] + self.leg_lower)

            elbow_l = (hx + (25 * facing), chest_y + 35)
            hand_l = (hx + (45 * facing), chest_y + 20)
            elbow_r = (hx + (15 * facing), chest_y + 40)
            hand_r = (hx + (35 * facing), chest_y + 35)

        elif action == "point":
            point_pulse = math.sin(t * 3.5 * spd) * 4
            chest_y = hy + self.head_radius + 20
            pelvis_x = hx
            pelvis_y = chest_y + self.torso_len - 20

            knee_l = (pelvis_x - 30, pelvis_y + self.leg_upper)
            foot_l = (pelvis_x - 40, knee_l[1] + self.leg_lower)
            knee_r = (pelvis_x + 30, pelvis_y + self.leg_upper)
            foot_r = (pelvis_x + 40, knee_r[1] + self.leg_lower)

            elbow_l = (hx - 45, chest_y + 35)
            hand_l = (hx - 15, pelvis_y - 5)
            elbow_r = (hx + 40, chest_y + 15)
            hand_r = (hx + 75 + point_pulse, chest_y + 10)

        elif action == "celebrate":
            bob = abs(math.sin(t * 7.5 * spd)) * 14
            hy -= bob
            chest_y = hy + self.head_radius + 20
            pelvis_x = hx
            pelvis_y = chest_y + self.torso_len - 20

            knee_l = (pelvis_x - 40, pelvis_y + self.leg_upper - 5)
            foot_l = (pelvis_x - 48, knee_l[1] + self.leg_lower + 5)
            knee_r = (pelvis_x + 40, pelvis_y + self.leg_upper - 5)
            foot_r = (pelvis_x + 48, knee_r[1] + self.leg_lower + 5)

            arm_pump = math.sin(t * 8.0 * spd) * 12
            elbow_l = (hx - 50, chest_y - 30 + arm_pump)
            hand_l = (hx - 75, chest_y - 75 + arm_pump * 1.4)
            elbow_r = (hx + 50, chest_y - 30 - arm_pump)
            hand_r = (hx + 75, chest_y - 75 - arm_pump * 1.4)

        elif action == "shrug":
            chest_y = hy + self.head_radius + 15
            pelvis_x = hx
            pelvis_y = chest_y + self.torso_len - 20

            knee_l = (pelvis_x - 20, pelvis_y + self.leg_upper)
            foot_l = (pelvis_x - 25, knee_l[1] + self.leg_lower)
            knee_r = (pelvis_x + 20, pelvis_y + self.leg_upper)
            foot_r = (pelvis_x + 25, knee_r[1] + self.leg_lower)

            elbow_l = (hx - 45, chest_y + 20)
            hand_l = (hx - 65, chest_y)
            elbow_r = (hx + 45, chest_y + 20)
            hand_r = (hx + 65, chest_y)

        elif action in ("kick", "flame_strike"):
            # Dynamic martial snap-kick strike cycle over time t
            cycle_freq = 2.2 * spd if motion_style == "snap_strike" else (3.5 * spd if motion_style == "flurry" else 1.6 * spd)
            phase = (t * cycle_freq) % 1.0

            if phase < 0.22:
                # Stage 1: Chambering knee high up towards torso
                prog = phase / 0.22
                torso_tilt = (-0.05 - 0.15 * prog) * facing
                chest_y = hy + self.head_radius + 20
                pelvis_x = hx - math.sin(torso_tilt) * self.torso_len
                pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len
                # Planted leg
                knee_l = (pelvis_x - (12 * facing), pelvis_y + self.leg_upper)
                foot_l = (knee_l[0] - (4 * facing), knee_l[1] + self.leg_lower)
                # Chambering kicking leg
                knee_r = (pelvis_x + (30 * prog * facing), pelvis_y - (20 * prog))
                foot_r = (knee_r[0] - (10 * facing), knee_r[1] + (25 * (1.0 - prog) + 15))
                # Guard hands
                elbow_l = (hx - (25 * facing), chest_y + 20)
                hand_l = (hx - (10 * facing), chest_y + 40)
                elbow_r = (hx + (20 * facing), chest_y + 15)
                hand_r = (hx + (35 * facing), chest_y)

            elif phase < 0.65:
                # Stage 2: Explosive martial snap extension & high whip strike
                prog = min(1.0, (phase - 0.22) / 0.18)
                torso_tilt = (-0.20 - 0.05 * prog) * facing
                chest_y = hy + self.head_radius + 20
                pelvis_x = hx - math.sin(torso_tilt) * self.torso_len
                pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len
                # Planted supporting leg
                knee_l = (pelvis_x - (18 * facing), pelvis_y + self.leg_upper)
                foot_l = (knee_l[0] - (6 * facing), knee_l[1] + self.leg_lower)
                # Full high-kick extension with impact micro-shudder
                shudder = math.sin(t * 60.0) * (2.0 * self.scale) if prog > 0.8 else 0.0
                kick_reach = 55 + (35 * prog)
                knee_r = (pelvis_x + (kick_reach * 0.55 * facing), pelvis_y - (20 + 10 * prog) + shudder)
                foot_r = (pelvis_x + (kick_reach * facing), pelvis_y - (25 + 15 * prog) + shudder)
                # Counter-balancing martial arms
                elbow_l = (hx - (35 * facing), chest_y + 10)
                hand_l = (hx - (25 * facing), chest_y + 35)
                elbow_r = (hx + (35 * facing), chest_y + 5)
                hand_r = (hx + (50 * facing), chest_y - 15)

            else:
                # Stage 3: Smooth chamber recovery and return to combat stance
                prog = (phase - 0.65) / 0.35
                torso_tilt = (-0.20 + 0.15 * prog) * facing
                chest_y = hy + self.head_radius + 20
                pelvis_x = hx - math.sin(torso_tilt) * self.torso_len
                pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len
                knee_l = (pelvis_x - (15 * facing), pelvis_y + self.leg_upper)
                foot_l = (knee_l[0] - (5 * facing), knee_l[1] + self.leg_lower)
                knee_r = (pelvis_x + ((45 - 25 * prog) * facing), pelvis_y - (10 - 20 * prog))
                foot_r = (knee_r[0] + ((40 - 30 * prog) * facing), knee_r[1] + (10 + 35 * prog))
                elbow_l = (hx - (30 * facing), chest_y + 15)
                hand_l = (hx - (15 * facing), chest_y + 40)
                elbow_r = (hx + (30 * facing), chest_y + 10)
                hand_r = (hx + (40 * facing), chest_y)

        elif action in ("punch", "lunge_dash"):
            # Forward lunging strike thrust cycle over time t
            cycle_freq = 2.4 * spd if motion_style == "snap_strike" else 1.8 * spd
            phase = (t * cycle_freq) % 1.0
            thrust_prog = math.sin(phase * math.pi)

            chest_y = hy + self.head_radius + 15
            torso_tilt = (0.15 + 0.20 * thrust_prog) * facing
            pelvis_x = hx - math.sin(torso_tilt) * self.torso_len
            pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len

            # Lower body lunging stance
            knee_l = (pelvis_x - ((30 + 10 * thrust_prog) * facing), pelvis_y + self.leg_upper - 5)
            foot_l = (knee_l[0] - (20 * facing), knee_l[1] + self.leg_lower + 5)
            knee_r = (pelvis_x + ((20 + 15 * thrust_prog) * facing), pelvis_y + self.leg_upper - 15)
            foot_r = (knee_r[0] + (10 * facing), knee_r[1] + self.leg_lower + 15)

            # Punching arms: lead fist drives forward, rear hand guards chin
            elbow_l = (hx - (12 * facing), chest_y + 25)
            hand_l = (hx + (10 * facing), chest_y + 15)
            fist_extension = 45 + (65 * thrust_prog)
            elbow_r = (hx + ((fist_extension * 0.5) * facing), chest_y + 12 - (5 * thrust_prog))
            hand_r = (hx + (fist_extension * facing), chest_y + 5 - (10 * thrust_prog))

        elif action == "spear_thrust":
            # Saint Killingham Spear of Longinus driving pierce cycle
            cycle_freq = 1.8 * spd
            phase = (t * cycle_freq) % 1.0
            thrust_prog = math.sin(phase * math.pi)

            chest_y = hy + self.head_radius + 18
            torso_tilt = (0.10 + 0.22 * thrust_prog) * facing
            pelvis_x = hx - math.sin(torso_tilt) * self.torso_len
            pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len

            knee_l = (pelvis_x - ((28 + 12 * thrust_prog) * facing), pelvis_y + self.leg_upper - 5)
            foot_l = (knee_l[0] - (18 * facing), knee_l[1] + self.leg_lower + 5)
            knee_r = (pelvis_x + ((25 + 15 * thrust_prog) * facing), pelvis_y + self.leg_upper - 12)
            foot_r = (knee_r[0] + (12 * facing), knee_r[1] + self.leg_lower + 12)

            # Two-handed heavy spear pierce forward
            spear_reach = 40 + (75 * thrust_prog)
            elbow_l = (hx + ((spear_reach * 0.3) * facing), chest_y + 20)
            hand_l = (hx + ((spear_reach * 0.5) * facing), chest_y + 12)
            elbow_r = (hx + ((spear_reach * 0.65) * facing), chest_y + 10)
            hand_r = (hx + (spear_reach * facing), chest_y + 4)

        elif action == "barrage":
            # Rapid alternating flurry strikes
            alt_freq = 16.0 * spd
            strike_alt = math.sin(t * alt_freq)
            chest_y = hy + self.head_radius + 18
            torso_tilt = (0.12 + 0.08 * strike_alt) * facing
            pelvis_x = hx - math.sin(torso_tilt) * self.torso_len
            pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len

            knee_l = (pelvis_x - (25 * facing), pelvis_y + self.leg_upper - 5)
            foot_l = (knee_l[0] - (20 * facing), knee_l[1] + self.leg_lower + 5)
            knee_r = (pelvis_x + (25 * facing), pelvis_y + self.leg_upper - 10)
            foot_r = (knee_r[0] + (15 * facing), knee_r[1] + self.leg_lower + 10)

            reach_a = 50 + 40 * max(0.0, strike_alt)
            reach_b = 50 + 40 * max(0.0, -strike_alt)
            elbow_l = (hx + (reach_b * 0.5 * facing), chest_y + 18)
            hand_l = (hx + (reach_b * facing), chest_y + 10)
            elbow_r = (hx + (reach_a * 0.5 * facing), chest_y + 12)
            hand_r = (hx + (reach_a * facing), chest_y + 4)

        elif action == "locked_in":
            # Sanji Locked-In Ready Stance: Low center of gravity, deep breathing, deadly calm
            breath = math.sin(t * 3.2 * spd) * (3.0 * self.scale)
            stance_sway = math.cos(t * 1.8 * spd) * (1.8 * self.scale) * facing
            hy += breath
            chest_y = hy + self.head_radius + 24
            torso_tilt = 0.08 * facing
            pelvis_x = hx - math.sin(torso_tilt) * self.torso_len + stance_sway
            pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len + 8  # lowered crouch

            # Wide martial base
            knee_l = (pelvis_x - (32 * facing), pelvis_y + self.leg_upper - 8)
            foot_l = (knee_l[0] - (16 * facing), knee_l[1] + self.leg_lower + 8)
            knee_r = (pelvis_x + (34 * facing), pelvis_y + self.leg_upper - 8)
            foot_r = (knee_r[0] + (16 * facing), knee_r[1] + self.leg_lower + 8)

            # Hands casual in suit pockets / low ready combat guard
            elbow_l = (hx - (28 * facing), chest_y + 35)
            hand_l = (pelvis_x - (12 * facing), pelvis_y - 2)
            elbow_r = (hx + (28 * facing), chest_y + 35)
            hand_r = (pelvis_x + (12 * facing), pelvis_y - 2)

        elif action == "channel_pose":
            # ── Universal Sorcerer / Aura / Magic / Ki Channeling Pose ─────────────
            # Used for ANY technique that is NOT a physical martial strike:
            # Imu's Stigma (void black flames), Gojo's Infinity / Hollow Purple,
            # Blackbeard's darkness, Madara's wood release, Yhwach's Almighty, etc.
            # The VFX is rendered separately by _draw_vfx_overlay from kinetic dict.
            # Pose: upright, arms extended forward channeling power, slight hover bob.
            hover_bob = math.sin(t * 4.0 * spd) * (4.5 * self.scale)
            sway = math.sin(t * 1.5 * spd) * (2.0 * self.scale) * facing
            hy += hover_bob
            chest_y = hy + self.head_radius + 15
            torso_tilt = (0.04 * math.sin(t * 2.5)) * facing  # slow ominous sway
            pelvis_x = hx - math.sin(torso_tilt) * self.torso_len + sway
            pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len - 8  # slightly elevated

            # Legs: straight, relaxed hover (no ground contact needed)
            knee_l = (pelvis_x - (14 * facing), pelvis_y + self.leg_upper - 5)
            foot_l = (knee_l[0] - (8 * facing), knee_l[1] + self.leg_lower)
            knee_r = (pelvis_x + (14 * facing), pelvis_y + self.leg_upper - 5)
            foot_r = (knee_r[0] + (8 * facing), knee_r[1] + self.leg_lower)

            # Arms: outstretched forward, palms open and channeling energy
            arm_reach_phase = math.sin(t * 3.5 * spd) * 8  # pulsing arm reach
            elbow_l = (hx - (22 * facing), chest_y + 20)
            hand_l = (hx + ((48 + arm_reach_phase) * facing), chest_y + 12)
            elbow_r = (hx + (22 * facing), chest_y + 25)
            hand_r = (hx + ((52 + arm_reach_phase) * facing), chest_y + 18)

        elif action == "defend":
            # Solid defensive cross-guard stance with impact micro-recoil
            guard_bob = math.sin(t * 4.0 * spd) * 2.0
            hy += guard_bob
            chest_y = hy + self.head_radius + 25
            pelvis_x = hx
            pelvis_y = chest_y + self.torso_len - 25
            knee_l = (pelvis_x - 35, pelvis_y + self.leg_upper - 10)
            foot_l = (pelvis_x - 45, knee_l[1] + self.leg_lower)
            knee_r = (pelvis_x + 35, pelvis_y + self.leg_upper - 10)
            foot_r = (pelvis_x + 45, knee_r[1] + self.leg_lower)
            elbow_l = (hx + (15 * facing), chest_y + 30)
            hand_l = (hx + (25 * facing), chest_y - 10)
            elbow_r = (hx + (20 * facing), chest_y + 35)
            hand_r = (hx + (30 * facing), chest_y - 5)

        elif action == "kneel":
            # Tactical / humbled kneeling posture with breathing
            chest_y = hy + self.head_radius + 35
            pelvis_x = hx
            pelvis_y = chest_y + self.torso_len - 30
            knee_l = (pelvis_x - (10 * facing), pelvis_y + self.leg_upper)
            foot_l = (knee_l[0] - (35 * facing), knee_l[1])
            knee_r = (pelvis_x + (30 * facing), pelvis_y + 15)
            foot_r = (knee_r[0] + (5 * facing), knee_l[1])
            elbow_l = (hx - (15 * facing), chest_y + 35)
            hand_l = (pelvis_x + (25 * facing), knee_r[1] - 5)
            elbow_r = (hx + (15 * facing), chest_y + 35)
            hand_r = (hx + (5 * facing), knee_l[1] - 5)

        elif action in ("fall", "recoil"):
            # Knocked back in mid-air from impact with dynamic flailing recovery
            recoil_cycle = math.sin(t * 3.5 * spd) * 6.0
            chest_y = hy + self.head_radius + 20 + recoil_cycle
            torso_tilt = (-0.45 - 0.10 * math.sin(t * 4.0)) * facing
            pelvis_x = hx - math.sin(torso_tilt) * self.torso_len
            pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len
            knee_l = (pelvis_x - (30 * facing), pelvis_y + self.leg_upper - 20)
            foot_l = (knee_l[0] - (30 * facing), knee_l[1] + 15)
            knee_r = (pelvis_x - (10 * facing), pelvis_y + self.leg_upper - 10)
            foot_r = (knee_r[0] - (20 * facing), knee_r[1] + 25)
            elbow_l = (hx - (45 * facing), chest_y - 20)
            hand_l = (hx - (75 * facing), chest_y - 45)
            elbow_r = (hx - (25 * facing), chest_y - 10)
            hand_r = (hx - (55 * facing), chest_y - 30)

        elif action in ("flying", "air_dash"):
            # High-velocity aerial flight kinematics: aerodynamic horizontal body tilt and streamlined limbs
            fly_sway = math.sin(t * 8.0 * spd) * (3.5 * self.scale)
            chest_y = hy + self.head_radius + 15
            torso_tilt = (1.12 + 0.06 * math.sin(t * 6.0)) * facing
            pelvis_x = hx - math.sin(torso_tilt) * self.torso_len
            pelvis_y = chest_y + math.cos(torso_tilt) * self.torso_len + fly_sway

            # Trailing aerodynamic legs
            knee_r = (pelvis_x - (42 * facing), pelvis_y + 8)
            foot_r = (pelvis_x - (92 * facing), pelvis_y + 14)
            knee_l = (pelvis_x - (28 * facing), pelvis_y + 22)
            foot_l = (pelvis_x - (68 * facing), pelvis_y + 32)

            # Leading arm slicing forward through the sky, rear arm tucked alongside flank
            elbow_r = (hx + (44 * facing), chest_y - 8)
            hand_r = (hx + (86 * facing), chest_y - 16)
            elbow_l = (pelvis_x - (10 * facing), pelvis_y - 12)
            hand_l = (pelvis_x - (32 * facing), pelvis_y - 4)

        else:
            chest_y = hy + self.head_radius + 20
            pelvis_x = hx
            pelvis_y = chest_y + self.torso_len - 20
            elbow_l, hand_l = (hx - 30, chest_y + 50), (hx - 30, chest_y + 100)
            elbow_r, hand_r = (hx + 30, chest_y + 50), (hx + 30, chest_y + 100)
            knee_l, foot_l = (pelvis_x - 20, pelvis_y + 60), (pelvis_x - 20, pelvis_y + 120)
            knee_r, foot_r = (pelvis_x + 20, pelvis_y + 60), (pelvis_x + 20, pelvis_y + 120)

        r = self.head_radius
        neck_y = hy + r
        shoulder_x = hx
        shoulder_y = neck_y + 15

        # 1. Torso Garment Rendering (Layered smoothly under limbs)
        self._draw_clothing_torso(
            draw=draw,
            hx=hx,
            hy=hy,
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            shoulder_x=shoulder_x,
            shoulder_y=shoulder_y,
            facing=facing,
            clothing_type=clothing_type,
            clothing_color=clothing_color
        )

        # 2. Skeletal Stick Limbs (Arms & Legs with responsive IK joints)
        draw.line([shoulder_x, shoulder_y, elbow_l[0], elbow_l[1]], fill=self.color, width=self.line_width)
        draw.line([elbow_l[0], elbow_l[1], hand_l[0], hand_l[1]], fill=self.color, width=self.line_width)
        draw.line([shoulder_x, shoulder_y, elbow_r[0], elbow_r[1]], fill=self.color, width=self.line_width)
        draw.line([elbow_r[0], elbow_r[1], hand_r[0], hand_r[1]], fill=self.color, width=self.line_width)

        draw.line([pelvis_x, pelvis_y, knee_l[0], knee_l[1]], fill=self.color, width=self.line_width)
        draw.line([knee_l[0], knee_l[1], foot_l[0], foot_l[1]], fill=self.color, width=self.line_width)
        draw.line([pelvis_x, pelvis_y, knee_r[0], knee_r[1]], fill=self.color, width=self.line_width)
        draw.line([knee_r[0], knee_r[1], foot_r[0], foot_r[1]], fill=self.color, width=self.line_width)

        # 3. Modular Caricature Head (Big Cartoon Eyes, Skin Tone, Hair, Facial Traits)
        self._draw_caricature_head(
            draw=draw,
            hx=hx,
            hy=hy,
            facing=facing,
            expr=expr,
            skin_tone=skin_tone,
            hair_style=hair_style,
            hair_color=hair_color,
            face_traits=face_traits,
            t=t
        )

        # Determine lead vs rear limbs based on facing direction
        lead_hand = hand_r if facing == 1 else hand_l
        rear_hand = hand_l if facing == 1 else hand_r
        lead_foot = foot_r if facing == 1 else foot_l
        rear_foot = foot_l if facing == 1 else foot_r
        lead_knee = knee_r if facing == 1 else knee_l

        # Compute dynamic joint sockets
        sockets: Dict[str, Tuple[float, float]] = {
            "head": (hx, hy - r),
            "mouth": (hx + (10 * facing) * self.scale, hy + 4 * self.scale),
            "lead_hand": lead_hand,
            "rear_hand": rear_hand,
            "lead_foot": lead_foot,
            "rear_foot": rear_foot,
            "torso": (shoulder_x, shoulder_y)
        }

        # Resolve active attachments (merging sockets with backward compatibility)
        active_attachments = dict(attachments or {})
        if accessory and accessory != "none" and "head" not in active_attachments:
            active_attachments["head"] = accessory
        if visual_trait and visual_trait != "none":
            if visual_trait in ("straw_hat", "red_beanie", "headphones", "glasses", "crown", "headband", "horns") and "head" not in active_attachments:
                active_attachments["head"] = visual_trait
            elif visual_trait in ("cape", "tie") and "torso" not in active_attachments:
                active_attachments["torso"] = visual_trait
            elif visual_trait == "flame" and "lead_foot" not in active_attachments and "lead_hand" not in active_attachments:
                sock = "lead_hand" if action == "punch" else "lead_foot"
                active_attachments[sock] = "flame"
            elif visual_trait == "blade" and "lead_hand" not in active_attachments:
                active_attachments["lead_hand"] = "blade"
            elif visual_trait == "smoke" and "lead_foot" not in active_attachments:
                active_attachments["lead_foot"] = "smoke"

        # Universal Socket Attachment Dispatch
        for socket_name, item_name in active_attachments.items():
            pos = sockets.get(socket_name)
            if pos and item_name and item_name != "none":
                self._draw_socket_attachment(
                    draw=draw,
                    socket=socket_name,
                    item=item_name,
                    pos=pos,
                    facing=facing,
                    action=action,
                    hx=hx,
                    hy=hy,
                    lead_knee=lead_knee
                )

        # Character Name HUD Tag (Auto-elevates above horns, crowns, top hats, or massive afros)
        if name:
            has_tall = (active_attachments.get("head") in ("horns", "crown", "straw_hat", "top_hat")) or (hair_style in ("massive_afro", "high_bun", "twin_tails"))
            self._draw_name_hud(draw, hx, hy, name, has_tall_headwear=has_tall)

    @staticmethod
    def _hex_to_rgb(hex_str: str, fallback=(80, 0, 120)) -> tuple:
        """Convert #RRGGBB hex string to (R, G, B) tuple safely."""
        try:
            h = hex_str.strip().lstrip("#")
            if len(h) == 3:
                h = h[0]*2 + h[1]*2 + h[2]*2
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            return fallback

    @staticmethod
    def draw_vfx_overlay(draw: ImageDraw.ImageDraw, char_x: int, char_y: int,
                         t: float, kinetic: dict, canvas_w: int, canvas_h: int):
        """
        Generative Procedural VFX Engine — Gemini Edition.

        Renders any power, technique, or ability that Gemini freely describes
        via the kinetic.vfx dict. No hardcoded technique names required.
        Imu's Stigma, Gojo's Hollow Purple, Blackbeard's Yami Yami,
        Madara's Susanoo — all rendered from hex colors + vfx type alone.
        """
        vfx = kinetic.get("vfx", {})
        if not vfx:
            return

        vfx_type   = str(vfx.get("type", "aura_field")).lower()
        origin_key = str(vfx.get("origin", "body_core")).lower()
        intensity  = max(0.1, min(1.0, float(vfx.get("intensity", 0.7))))
        scale_fac  = max(0.3, min(3.0, float(vfx.get("scale", 1.0))))
        p_col      = StickmanRig._hex_to_rgb(str(vfx.get("primary_color", "#440088")))
        s_col      = StickmanRig._hex_to_rgb(str(vfx.get("secondary_color", "#cc0033")))

        # Resolve VFX origin point relative to character
        ox, oy = char_x, char_y
        if origin_key == "ground":
            oy = char_y  # ground level is char_y in this coord system
        elif origin_key == "palms":
            oy = char_y - int(canvas_h * 0.12)  # roughly chest-arm height
        elif origin_key == "eyes":
            oy = char_y - int(canvas_h * 0.18)
        elif origin_key == "body_core":
            oy = char_y - int(canvas_h * 0.10)
        elif origin_key == "lead_hand":
            oy = char_y - int(canvas_h * 0.12)
            ox = char_x + int(canvas_w * 0.08)
        elif origin_key == "all_around":
            ox, oy = char_x, char_y - int(canvas_h * 0.10)

        radius_base = int(80 * scale_fac * intensity)

        # ── VFX TYPE DISPATCH ────────────────────────────────────────────────

        if vfx_type == "swirling_vortex":
            # Ominous swirling spiral arms converging at origin (Imu Stigma, void, etc.)
            num_arms = max(4, int(7 * intensity))
            rot_speed = 1.4 * intensity
            rot = t * rot_speed
            for a_i in range(num_arms):
                base_ang = (a_i / num_arms) * 2 * math.pi + rot
                pts = [(ox, oy)]
                arm_len = radius_base * 2.2
                for step in range(1, 9):
                    r = step * (arm_len / 8)
                    ang = base_ang + step * 0.35
                    pts.append((ox + math.cos(ang) * r, oy + math.sin(ang) * r))
                lw = max(2, int(4 * intensity * (1.0 - a_i / num_arms * 0.4)))
                col = p_col if a_i % 2 == 0 else s_col
                draw.line(pts, fill=col, width=lw)
            # Central pulsing core
            pulse_r = int(radius_base * 0.35 * (0.7 + 0.3 * math.sin(t * 6.0)))
            draw.ellipse([ox - pulse_r, oy - pulse_r, ox + pulse_r, oy + pulse_r], fill=p_col)

        elif vfx_type == "lightning_burst":
            # Jagged conqueror's haki / thunder / electric discharge
            num_bolts = max(5, int(10 * intensity))
            for b_i in range(num_bolts):
                ang = (b_i / num_bolts) * 2 * math.pi + t * 2.5
                bolt_len = radius_base * (1.5 + 0.5 * math.sin(t * 8 + b_i))
                prev = (ox, oy)
                segments = 5
                for seg in range(segments):
                    frac = (seg + 1) / segments
                    nx = ox + math.cos(ang) * bolt_len * frac + (hash((b_i, seg, int(t * 10))) % 30 - 15)
                    ny = oy + math.sin(ang) * bolt_len * frac + (hash((b_i, seg + 1, int(t * 10))) % 30 - 15)
                    col = p_col if seg % 2 == 0 else s_col
                    draw.line([prev, (nx, ny)], fill=col, width=max(1, int(3 * intensity * (1 - frac * 0.7))))
                    prev = (nx, ny)

        elif vfx_type == "aura_field":
            # Power aura / ki glow / battle presence radiating from body
            num_rings = max(2, int(5 * intensity))
            for ring_i in range(num_rings):
                phase_offset = ring_i / num_rings
                ring_phase = (t * 2.0 + phase_offset) % 1.0
                ring_r = int(radius_base * (0.4 + ring_phase * 1.6))
                alpha_factor = 1.0 - ring_phase
                lw = max(1, int(4 * intensity * alpha_factor))
                col = p_col if ring_i % 2 == 0 else s_col
                draw.ellipse([ox - ring_r, oy - ring_r, ox + ring_r, oy + ring_r], outline=col, width=lw)

        elif vfx_type == "tendril_spears":
            # Dark impaling tendrils / Imu Stigma dark arrows / black thorns from void
            num_tendrils = max(3, int(8 * intensity))
            for td_i in range(num_tendrils):
                ang = (td_i / num_tendrils) * 2 * math.pi + t * 0.6 + (td_i * 0.8)
                # Tendrils grow outward from origin with pulse
                grow_phase = (t * 1.8 + td_i * 0.3) % 1.0
                td_len = int(radius_base * (1.0 + 0.8 * grow_phase) * 1.8)
                tip_x = int(ox + math.cos(ang) * td_len)
                tip_y = int(oy + math.sin(ang) * td_len)
                # Thick dark spear body
                draw.line([ox, oy, tip_x, tip_y], fill=p_col, width=max(3, int(6 * intensity)))
                # Sharp bright tip
                barb_x = int(tip_x + math.cos(ang) * 18)
                barb_y = int(tip_y + math.sin(ang) * 18)
                draw.line([tip_x, tip_y, barb_x, barb_y], fill=s_col, width=max(2, int(3 * intensity)))

        elif vfx_type == "dark_miasma":
            # Spreading darkness / Blackbeard's Yami Yami / shadow contamination
            num_blobs = max(4, int(9 * intensity))
            for bm_i in range(num_blobs):
                drift_ang = (bm_i / num_blobs) * 2 * math.pi + t * 0.4
                drift_r = int(radius_base * (0.6 + 0.5 * math.sin(t * 1.5 + bm_i)))
                bx = int(ox + math.cos(drift_ang) * drift_r)
                by = int(oy + math.sin(drift_ang) * drift_r)
                blob_r = int(radius_base * 0.45 * (0.5 + 0.5 * intensity))
                draw.ellipse([bx - blob_r, by - blob_r, bx + blob_r, by + blob_r], fill=p_col)
                inner_r = blob_r // 2
                draw.ellipse([bx - inner_r, by - inner_r, bx + inner_r, by + inner_r], fill=s_col)

        elif vfx_type == "energy_beam":
            # Directed beam / Kamehameha / Rasengan launch / laser
            beam_width = max(8, int(28 * intensity * scale_fac))
            beam_len = int(canvas_w * 0.55 * scale_fac)
            # Beam fires in character facing direction (horizontal)
            bx2 = ox + beam_len
            draw.line([ox, oy, bx2, oy], fill=p_col, width=beam_width)
            draw.line([ox, oy, bx2, oy], fill=s_col, width=max(3, beam_width // 3))
            # Flickering core pulse
            pulse_w = max(2, int(beam_width * 0.4 * (0.7 + 0.3 * math.sin(t * 12.0))))
            draw.line([ox, oy, bx2, oy], fill=(255, 255, 255), width=pulse_w)

        elif vfx_type == "slash_cleave":
            # Sword slash arc / Zoro San Zen Sekai / Mihawk's slash
            num_arcs = max(2, int(5 * intensity))
            for arc_i in range(num_arcs):
                arc_phase = (t * 3.0 + arc_i * 0.25) % 1.0
                arc_r = int(radius_base * (0.8 + arc_phase * 1.4))
                start_ang = -60 - arc_i * 10
                end_ang   = 60 + arc_i * 10
                alpha_lw = max(1, int(5 * intensity * (1.0 - arc_phase)))
                col = p_col if arc_i % 2 == 0 else s_col
                draw.arc([ox - arc_r, oy - arc_r, ox + arc_r, oy + arc_r],
                         start=start_ang, end=end_ang, fill=col, width=alpha_lw)

        elif vfx_type == "shockwave_ring":
            # Expanding pressure rings / Conqueror's Haki burst / domain expansion edge
            num_waves = max(2, int(4 * intensity))
            for wv_i in range(num_waves):
                wave_phase = ((t * 1.8 + wv_i * 0.5) % 1.0)
                wave_r = int(radius_base * wave_phase * 2.5)
                wave_lw = max(1, int(6 * intensity * (1.0 - wave_phase)))
                col = p_col if wv_i % 2 == 0 else s_col
                draw.ellipse([ox - wave_r, oy - wave_r, ox + wave_r, oy + wave_r],
                             outline=col, width=wave_lw)

        elif vfx_type == "particle_storm":
            # Dense particle field / Yhwach / Demon lord radiating chaos
            num_particles = max(20, int(60 * intensity))
            for p_i in range(num_particles):
                ang = (p_i / num_particles) * 2 * math.pi + t * (0.5 + p_i * 0.03)
                dist = radius_base * (0.2 + (p_i % 7) / 7.0 * 1.8) * (0.8 + 0.2 * math.sin(t * 4 + p_i))
                px = int(ox + math.cos(ang) * dist)
                py = int(oy + math.sin(ang) * dist)
                sz = max(1, (p_i % 3) + 1)
                col = p_col if p_i % 3 != 0 else s_col
                draw.ellipse([px - sz, py - sz, px + sz, py + sz], fill=col)
