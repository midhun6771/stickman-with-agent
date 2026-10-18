import sys
import math
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List
from PIL import Image, ImageDraw

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .rig import StickmanRig
from .props import PROP_REGISTRY
from .layout import LayoutEngine, get_font
from ..schema import VideoStorySpec, SceneSpec, CharacterState

COLOR_MAP = {
    "cyan": (0, 220, 255),
    "crimson": (255, 45, 85),
    "gold": (255, 215, 0),
    "emerald": (46, 204, 113),
    "violet": (155, 89, 182),
    "amber": (243, 156, 18),
    "orange": (255, 120, 40),
    "white": (255, 255, 255)
}

class VideoRenderer:
    def __init__(self, output_dir: Path, width: int = 720, height: int = 1280):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.width = width
        self.height = height
        self.layout = LayoutEngine(width, height)
        self.font_medium = get_font(20, bold=True)

    async def prepare_audio(self, story: VideoStorySpec) -> float:
        import edge_tts
        soundtrack = self.output_dir / "soundtrack.mp3"
        if soundtrack.exists() and all(hasattr(sc, "params") and "duration" in sc.params for sc in story.scenes):
            return sum(sc.params["duration"] for sc in story.scenes)

        scene_durations = []
        for sc in story.scenes:
            audio_path = self.output_dir / f"scene_{sc.scene_id}.mp3"
            communicate = edge_tts.Communicate(sc.vo_text, story.voice_name, rate="+5%", boundary="WordBoundary")
            word_timestamps = []
            with open(audio_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        s_time = chunk["offset"] / 10_000_000.0
                        e_time = s_time + (chunk["duration"] / 10_000_000.0)
                        word_timestamps.append({
                            "word": chunk["text"],
                            "start": round(s_time, 3),
                            "end": round(e_time, 3)
                        })

            # Measure exact duration using ffprobe
            cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
            measured_dur = float(res.stdout.strip())
            # Exact duration aligned with audio file (0ms cumulative drift across scenes)
            dur = measured_dur
            sc.params = getattr(sc, "params", {})
            sc.params["duration"] = dur
            sc.params["audio_path"] = str(audio_path)
            sc.params["word_timestamps"] = word_timestamps
            scene_durations.append(dur)

        # Concatenate master audio
        concat_list = self.output_dir / "concat_audio.txt"
        with open(concat_list, "w") as f:
            for sc in story.scenes:
                f.write(f"file '{Path(sc.params['audio_path']).name}'\n")

        master_voice = self.output_dir / "master_voice.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list), "-c", "copy", str(master_voice)
        ], check=True)

        total_duration = sum(scene_durations)
        
        # Synthesize subtle rhythmic BGM
        bgm_file = self.output_dir / "bgm.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"sine=frequency=110:duration={total_duration}[b];sine=frequency=440:duration={total_duration}[h];[b]volume=0.12[vb];[h]volume=0.03[vh];[vb][vh]amix=inputs=2",
            "-c:a", "libmp3lame", str(bgm_file)
        ], check=True)

        # Mix voice + bgm
        final_soundtrack = self.output_dir / "soundtrack.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(master_voice), "-i", str(bgm_file),
            "-filter_complex", "[0:a]volume=1.0[v0];[1:a]volume=0.25[v1];[v0][v1]amix=inputs=2:duration=first",
            "-c:a", "libmp3lame", str(final_soundtrack)
        ], check=True)

        return total_duration

    def _draw_dynamic_background(self, draw: ImageDraw.ImageDraw, bg_style: str, accent: Tuple[int, int, int],
                                 t: float, scene_dur: float, chars: list, cx: int, cy: int):
        """
        Cinema-Grade Dynamic Background Engine:
        Directly driven by Gemini Creative Director choices based on narrative situation.
        Procedurally renders fire storms, manga speed lines, clash shockwaves,
        ominous dark vortexes, 3D battle arena grids, or dramatic spotlights.
        """
        w, h = self.width, self.height

        if bg_style == "fire_storm":
            # 1. Molten heat gradient from bottom
            horizon_glow_y = int(h * 0.45)
            band_h = 8
            for y_i in range(horizon_glow_y, h, band_h):
                prog = (y_i - horizon_glow_y) / float(h - horizon_glow_y)
                r_val = int(22 + 95 * (prog ** 1.8))
                g_val = int(10 + 35 * (prog ** 2.2))
                b_val = int(14 + 10 * prog)
                draw.rectangle([0, y_i, w, y_i + band_h], fill=(r_val, g_val, b_val))

            # 2. Rising glowing ember particles
            num_embers = 38
            for i in range(num_embers):
                ember_spd = 120 + ((i * 37) % 180)
                ex = int((i * 97.3 + math.sin(t * 2.5 + i * 1.5) * 35) % w)
                ey = int((h - (t * ember_spd + i * 42)) % h)
                sz = max(1, (i % 3) + 1)
                ember_col = (255, 130 + (i * 28) % 115, 25)
                draw.ellipse([ex - sz, ey - sz, ex + sz, ey + sz], fill=ember_col)

            # 3. Dynamic dancing flame tongues along ground
            flame_cols = 14
            col_w = w // flame_cols
            for f_i in range(flame_cols):
                fx = f_i * col_w
                f_h = int(28 + math.sin(t * 7.5 + f_i * 1.8) * 16)
                draw.polygon([(fx, h), (fx + col_w * 0.5, h - f_h), (fx + col_w, h)], fill=(210, 55, 15))

        elif bg_style == "speed_lines":
            # Dynamic radiating manga action lines streaming from center
            num_lines = 44
            open_r = 175  # Keeps center combat area clear
            max_r = max(w, h) * 0.95
            for i in range(num_lines):
                ang = (i / float(num_lines)) * 2 * math.pi + (t * 0.4)
                pulse = math.sin(t * 16.0 + i * 2.8) * 28
                r1 = open_r + pulse
                x1 = cx + math.cos(ang) * r1
                y1 = cy + math.sin(ang) * r1
                x2 = cx + math.cos(ang) * max_r
                y2 = cy + math.sin(ang) * max_r
                line_w = max(1, 2 if i % 3 == 0 else 1)
                draw.line([x1, y1, x2, y2], fill=accent, width=line_w)

        elif bg_style == "clash_burst":
            # Expanding shockwave rings and explosive spark fragments
            blast_period = 1.2
            prog_1 = (t % blast_period) / blast_period
            prog_2 = ((t + 0.6) % blast_period) / blast_period
            max_radius = max(w, h) * 0.85

            r1 = prog_1 * max_radius
            alpha_w1 = max(1, int(5 * (1.0 - prog_1)))
            draw.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], outline=accent, width=alpha_w1)

            r2 = prog_2 * max_radius
            alpha_w2 = max(1, int(4 * (1.0 - prog_2)))
            draw.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=(255, 235, 140), width=alpha_w2)

            # Impact sparks
            num_sparks = 24
            for s_i in range(num_sparks):
                ang = (s_i / float(num_sparks)) * 2 * math.pi
                s_dist = 60 + ((t * 400 + s_i * 35) % (max_radius * 0.7))
                sx1 = cx + math.cos(ang) * s_dist
                sy1 = cy + math.sin(ang) * s_dist
                sx2 = sx1 + math.cos(ang) * 16
                sy2 = sy1 + math.sin(ang) * 16
                draw.line([sx1, sy1, sx2, sy2], fill=(255, 245, 175), width=2)

        elif bg_style == "dark_vortex":
            # Swirling ominous purple / abyssal conqueror's pressure
            num_arms = 8
            rot = t * 1.0
            max_r = max(w, h) * 0.75
            for a_i in range(num_arms):
                base_ang = (a_i / float(num_arms)) * 2 * math.pi + rot
                pts = [(cx, cy)]
                for step in range(1, 7):
                    step_r = step * (max_r / 6.0)
                    step_ang = base_ang + (step * 0.32)
                    pts.append((cx + math.cos(step_ang) * step_r, cy + math.sin(step_ang) * step_r))
                draw.line(pts, fill=(75, 18, 95), width=max(2, int(3)))

        elif bg_style == "arena_ground":
            # 3D perspective battle grid floor
            horizon_y = int(h * 0.58)
            # Horizontal depth lines
            for l_i in range(1, 9):
                depth_prog = (l_i / 9.0) ** 2.2
                ly = horizon_y + int((h - horizon_y) * depth_prog)
                draw.line([0, ly, w, ly], fill=(32, 38, 54), width=1)
            # Converging perspective grid lines
            for col_i in range(-6, 7):
                bx = cx + int(col_i * (w * 0.15))
                draw.line([cx, horizon_y, bx, h], fill=(26, 32, 46), width=1)
            # Soft top spotlight cone
            draw.polygon([(cx - 45, 0), (cx + 45, 0), (cx + int(w * 0.40), h), (cx - int(w * 0.40), h)], fill=(18, 22, 34))

        elif bg_style == "spotlight":
            # High-contrast theatrical spotlight cone
            draw.polygon([(cx - 35, 0), (cx + 35, 0), (cx + int(w * 0.36), int(h * 0.88)), (cx - int(w * 0.36), int(h * 0.88))], fill=(24, 28, 44))
            draw.ellipse([cx - int(w * 0.36), int(h * 0.76), cx + int(w * 0.36), int(h * 0.88)], fill=(30, 36, 56))

        else:
            # Minimal clean gradient
            draw.rectangle([0, 0, w, h], fill=(10, 12, 16))

    def _calculate_character_spatial_pose(
        self,
        ch: CharacterState,
        t: float,
        scene_dur: float,
        cx: int,
        ground_y: int,
        c_idx: int,
        total_chars: int,
        scale: float
    ) -> Tuple[int, int, int, int, float]:
        """
        True Cinematic Character Motion & Spatial Traversal Engine:
        Calculates real spatial traversal across the screen as a function of time t.
        Characters physically WALK across the stage, SPRINT in from the flanks,
        SOAR through the air at high altitudes with aerodynamic postures,
        LUNGE forward into martial kicks, strikes, and spear thrusts,
        and SLIDE backwards upon knockback impacts.
        NO ARTIFICIAL CAMERA SHAKE OR JITTER IS APPLIED TO CHARACTERS.
        Returns: (char_x, char_y, shadow_x, shadow_y, shadow_scale)
        """
        from .rig import normalize_x_offset
        p = min(1.0, max(0.0, t / max(0.1, scene_dur)))
        direction_str = str(getattr(ch, "direction", "right") or "right").lower().strip()
        facing = 1 if direction_str == "right" else -1
        action = str(getattr(ch, "action", "idle") or "idle").lower().strip()
        m_path = str(getattr(ch, "motion_path", "auto") or "auto").lower().strip()
        
        try:
            spd = max(0.5, min(1.5, float(getattr(ch, "speed", 1.0) or 1.0)))
        except (ValueError, TypeError):
            spd = 1.0

        raw_x = getattr(ch, "x_offset", 0.0)
        target_norm_x = normalize_x_offset(raw_x)

        try:
            altitude = max(0.0, min(1.0, float(getattr(ch, "altitude", 0.0) or 0.0)))
        except (ValueError, TypeError):
            altitude = 0.0

        start_x = getattr(ch, "start_x", None)
        end_x = getattr(ch, "end_x", None)

        # 1. Determine Horizontal Stage Coordinate X(t)
        if start_x is not None and end_x is not None:
            # Explicit Director Directed Spatial Interpolation
            cur_norm_x = float(start_x) + (float(end_x) - float(start_x)) * p
            base_x = cx + int(cur_norm_x * (self.width * 0.42))

        elif action == "walk" or m_path in ("cross_screen", "stalk_forward"):
            # Walking across the stage
            if m_path == "stalk_forward":
                stalk_dist = 0.16 * facing
                cur_norm_x = (target_norm_x - stalk_dist) + stalk_dist * p
            elif total_chars <= 1:
                # Solo character walks across stage in facing direction
                cur_norm_x = (-0.32 * facing) + (0.64 * facing) * p
            else:
                # Multi-character: advances from flank entrance towards combat mark
                walk_dist = 0.22 * facing
                cur_norm_x = (target_norm_x - walk_dist) + walk_dist * p
            base_x = cx + int(cur_norm_x * (self.width * 0.42))

        elif action == "run" or m_path == "charge_in":
            # Sprinting rapidly into battle from off-stage/flanks
            p_run = min(1.0, p / 0.55)
            ease_run = 1.0 - (1.0 - p_run) ** 2
            start_flank = -0.58 * facing
            cur_norm_x = start_flank + (target_norm_x - start_flank) * ease_run
            base_x = cx + int(cur_norm_x * (self.width * 0.42))

        elif action in ("flying", "air_dash") or m_path in ("flying", "aerial_dive"):
            # Soaring through the air horizontally across the screen
            fly_start = target_norm_x - (0.34 * facing)
            fly_end = target_norm_x + (0.34 * facing)
            cur_norm_x = fly_start + (fly_end - fly_start) * p
            base_x = cx + int(cur_norm_x * (self.width * 0.42))

        elif action in ("kick", "flame_strike", "punch", "spear_thrust", "barrage") or m_path == "lunge_clash":
            # Physical strike surge / lunge into the opponent's space
            base_combat_x = cx + int(target_norm_x * (self.width * 0.42))
            dash_dx = 0
            if m_path == "lunge_clash":
                dash_p = min(1.0, p / 0.35)
                dash_dx = int((self.width * 0.10 * facing) * dash_p)

            strike_lunge = 0
            if action in ("kick", "flame_strike"):
                cycle_freq = 2.2 * spd
                phase = (t * cycle_freq) % 1.0
                if 0.20 <= phase <= 0.65:
                    lunge_factor = math.sin((phase - 0.20) / 0.45 * math.pi)
                    strike_lunge = int(48 * scale * facing * lunge_factor)
            elif action in ("punch", "spear_thrust"):
                thrust_prog = math.sin(((t * 2.0 * spd) % 1.0) * math.pi)
                strike_lunge = int(42 * scale * facing * thrust_prog)
            elif action == "barrage":
                strike_lunge = int((16 + 10 * math.sin(t * 16.0 * spd)) * scale * facing)

            base_x = base_combat_x + dash_dx + strike_lunge

        elif action in ("fall", "recoil") or m_path == "knockback_slide":
            # Blasted backward across the floor upon impact
            slide_prog = 1.0 - (1.0 - min(1.0, p / 0.85)) ** 2
            slide_dx = int(-facing * (self.width * 0.16) * slide_prog)
            base_x = cx + int(target_norm_x * (self.width * 0.42)) + slide_dx

        else:
            # Grounded stationary or combat stance (breathing sway handled in rig)
            base_x = cx + int(target_norm_x * (self.width * 0.42))

        # 2. Determine Vertical Altitude Y(t) and Drop Shadow
        is_airborne = action in ("flying", "air_dash") or m_path in ("flying", "aerial_dive") or altitude > 0.1
        if is_airborne:
            eff_alt = max(0.35, altitude) if action in ("flying", "air_dash") or m_path == "flying" else altitude
            alt_px = int(self.height * (0.20 + 0.25 * min(1.0, eff_alt)))
            fly_bob = int(math.sin(p * math.pi) * (self.height * 0.035) + math.sin(t * 7.0) * 8)
            if m_path == "aerial_dive":
                dive_factor = 1.0 - min(1.0, p / 0.75)
                alt_px = int(alt_px * dive_factor)
            char_y = ground_y - alt_px + fly_bob
            shadow_x = base_x
            shadow_y = ground_y
            shadow_scale = max(0.30, 1.0 - (alt_px / (self.height * 0.45)))
        else:
            char_y = ground_y
            shadow_x = base_x
            shadow_y = ground_y
            shadow_scale = 1.0

        return base_x, char_y, shadow_x, shadow_y, shadow_scale

    def render_frame(self, t: float, scene_dur: float, sc: SceneSpec, global_p: float, story_accessory: str = "none") -> Image.Image:
        bg_style = getattr(sc, "background_style", "arena_ground") or "arena_ground"
        accent = COLOR_MAP.get(sc.accent_color, (0, 220, 255))

        # Base canvas
        img = Image.new("RGB", (self.width, self.height), (10, 12, 16))
        draw = ImageDraw.Draw(img)

        cx = self.width // 2
        cy = self.height // 2

        # 0. Dynamic Background directed by Gemini based on narrative situation
        chars_to_render = sc.characters if sc.characters else ([sc.character] if sc.character else [])
        self._draw_dynamic_background(draw, bg_style, accent, t, scene_dur, chars_to_render, cx, cy)

        # Visual Impact / Clash Intensity (Subtle screen perimeter flash, characters are NEVER shaken)
        shake_intensity = float(getattr(sc, "camera_shake", 0.0) or 0.0)
        if shake_intensity > 0.4 and t < 0.35:
            # Impact flash vignette on clash frame
            draw.rectangle([0, 0, self.width, self.height], outline=(255, 255, 255), width=max(2, int(4 * shake_intensity)))

        # 1. Draw Props (procedural or dynamic icon badge)
        from .props import get_prop_renderer
        for prop in sc.props:
            prop_fn = get_prop_renderer(prop.type)
            if prop_fn:
                prop_fn(draw, cx, cy, t, self.width, self.font_medium, prop.params)

        # 2. Draw Stickmen with true spatial locomotion, altitudes, and dynamic IK kinematics
        scale = 0.82 if len(chars_to_render) > 1 else (0.85 if self.height < 900 else 1.0)
        ground_y = int(self.height * 0.72)

        # Compute spatial coordinates and draw grounded drop shadows
        char_poses = []
        for c_idx, ch in enumerate(chars_to_render[:2]):
            char_x, char_y, sh_x, sh_y, sh_scale = self._calculate_character_spatial_pose(
                ch=ch,
                t=t,
                scene_dur=scene_dur,
                cx=cx,
                ground_y=ground_y,
                c_idx=c_idx,
                total_chars=len(chars_to_render),
                scale=scale
            )
            char_poses.append((char_x, char_y))
            # Draw grounded drop shadow below character
            shadow_w = int(38 * scale * sh_scale)
            shadow_fill = (5, 6, 10) if sh_scale > 0.6 else (15, 18, 26)
            draw.ellipse([sh_x - shadow_w, sh_y - 6, sh_x + shadow_w, sh_y + 6], fill=shadow_fill)

        # Render parametric stickmen at their exact spatial coordinates
        for c_idx, ch in enumerate(chars_to_render[:2]):
            char_x, char_y = char_poses[c_idx]
            char_color = (255, 255, 255) if c_idx == 0 else (235, 240, 255)
            rig = StickmanRig(base_x=char_x, base_y=char_y, scale=scale, color=char_color)
            acc = ch.accessory or (story_accessory if story_accessory != "none" else "none")
            vt = getattr(ch, "visual_trait", "none") or "none"
            m_style = getattr(ch, "motion_style", "combat_idle") or "combat_idle"

            rig.draw(
                draw=draw,
                t=t,
                action=ch.action,
                expr=ch.expression,
                direction=ch.direction,
                speed=ch.speed,
                accessory=acc,
                visual_trait=vt,
                attachments=getattr(ch, "attachments", {}),
                name=getattr(ch, "name", None),
                skin_tone=getattr(ch, "skin_tone", "fair"),
                hair_style=getattr(ch, "hair_style", "bald"),
                hair_color=getattr(ch, "hair_color", "black"),
                clothing_type=getattr(ch, "clothing_type", "shirt"),
                clothing_color=getattr(ch, "clothing_color", "white"),
                face_traits=getattr(ch, "face_traits", []),
                motion_style=m_style
            )

            # ── Generative Kinetic VFX Overlay ──────────────────────────────────
            # Renders any power/technique Gemini freely described via kinetic dict.
            # Completely independent of action names — Imu, Gojo, Blackbeard, etc.
            kinetic = getattr(ch, "kinetic", {})
            if kinetic:
                from .rig import StickmanRig as _Rig
                _Rig.draw_vfx_overlay(
                    draw=draw,
                    char_x=char_x,
                    char_y=char_y,
                    t=t,
                    kinetic=kinetic,
                    canvas_w=self.width,
                    canvas_h=self.height
                )


        # 3. Draw Layout (timed entrance badge only, no progress bar, no static bottom box)
        self.layout.draw_badge(draw, sc.badge, color=accent, t=t, scene_dur=scene_dur)

        return img

    async def render_video(self, story: VideoStorySpec, output_mp4: Path) -> Path:
        print(f"[*] Step 1: Synthesizing deterministic audio for '{story.title}'...")
        total_duration = await self.prepare_audio(story)
        total_frames = int(total_duration * story.fps)
        print(f"[*] Total duration: {total_duration:.2f}s ({total_frames} frames @ {story.fps} FPS)")

        soundtrack = self.output_dir / "soundtrack.mp3"

        print(f"[*] Step 2: Generating V7 Cinema-Grade .ASS karaoke subtitles...")
        from .subtitles import generate_story_karaoke_ass
        ass_path = self.output_dir / "karaoke_captions.ass"
        generate_story_karaoke_ass(story.scenes, ass_path, width=self.width, height=self.height)
        safe_ass = str(ass_path).replace("\\", "/").replace(":", "\\:")

        print(f"[*] Step 3: Streaming frames to FFmpeg with burned-in karaoke subtitles...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "rgb24",
            "-r", str(story.fps),
            "-i", "-",  # Stdin raw frames
            "-i", str(soundtrack),
            "-vf", f"subtitles='{safe_ass}'",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            str(output_mp4)
        ]
        ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        cur_time = 0.0
        for sc in story.scenes:
            dur = sc.params["duration"]
            frames_in_scene = int(dur * story.fps)
            print(f"  -> Rendering Scene {sc.scene_id} [{sc.stage}]: '{sc.overlay}' ({dur:.1f}s)")

            for f in range(frames_in_scene):
                t = f / story.fps
                global_p = min(1.0, (cur_time + t) / total_duration)
                frame = self.render_frame(t, dur, sc, global_p, story_accessory=story.accessory)
                ffmpeg_proc.stdin.write(frame.tobytes())

            cur_time += dur

        ffmpeg_proc.stdin.close()
        ffmpeg_proc.wait()

        if ffmpeg_proc.returncode != 0:
            raise RuntimeError("FFmpeg rendering failed")

        print(f"[OK] Render complete: {output_mp4}")
        return output_mp4
