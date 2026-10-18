import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from ..schema import VideoStorySpec, SceneSpec, CharacterState, PropSpec
from .prompts import get_director_prompt, DIRECTOR_SYSTEM_PROMPT

# Physical action library — what the rig directly animates with joint math
PHYSICAL_ACTIONS = {"idle", "walk", "run", "sit", "point", "celebrate", "shrug", "shocked", "kick", "punch", "defend", "kneel", "fall", "locked_in", "flame_strike", "spear_thrust", "barrage", "flying", "air_dash", "channel_pose"}
VALID_ACTIONS = PHYSICAL_ACTIONS  # kept for backwards compatibility
VALID_EXPRESSIONS = {"neutral", "smirk", "shocked", "deadpan", "smile", "angry", "confident", "furious", "menacing"}
VALID_PROPS = {"tv", "treadmill", "breakdown_bar", "press", "pit", "trophy", "energy_burst", "fork_paths"}
VALID_STAGES = ["hook", "disrupt", "insider_secret", "mechanism", "truth", "elevation"]
VALID_COLORS = {"cyan", "crimson", "gold", "emerald", "violet", "amber"}

# ── Semantic Action Resolver ──────────────────────────────────────────────────
# When Gemini freely invents an action name ("dark_omen", "stigma", "kamehameha",
# "hollow_purple", "bankai"), this resolver maps it to the nearest physical rig
# pose. The kinetic.vfx dict then carries the full visual effect on top.
# NO MORE CRASHING OR FALLING BACK TO IDLE. Gemini's creative direction is honoured.
def resolve_action(raw_action: str) -> str:
    """Maps any free-form action string to the nearest physical rig pose."""
    a = raw_action.lower().strip()
    # Direct match — already physical
    if a in PHYSICAL_ACTIONS:
        return a
    # Semantic keyword resolution
    if any(k in a for k in ("fly", "soar", "levitat", "float", "hover", "air", "launch")):
        return "flying"
    if any(k in a for k in ("kick", "boot", "heel", "jambe", "stomp", "sweep")):
        return "kick"
    if any(k in a for k in ("punch", "fist", "strike", "smash", "blow", "slam", "haymaker")):
        return "punch"
    if any(k in a for k in ("slash", "cut", "blade", "katana", "cleave", "thrust", "stab", "spear", "pierce")):
        return "spear_thrust"
    if any(k in a for k in ("barrage", "flurry", "rapid", "volley", "combo")):
        return "barrage"
    if any(k in a for k in ("fall", "recoil", "knockback", "blast back", "sent flying", "stagger")):
        return "fall"
    if any(k in a for k in ("defend", "block", "guard", "parry", "shield")):
        return "defend"
    if any(k in a for k in ("run", "sprint", "dash", "charge", "rush")):
        return "run"
    if any(k in a for k in ("walk", "advance", "approach", "stalk", "march")):
        return "walk"
    if any(k in a for k in ("kneel", "bow", "surrender", "submit")):
        return "kneel"
    if any(k in a for k in ("sit", "seated", "throne", "perch")):
        return "sit"
    # Magic / energy / aura / summoning / void / beam / dark arts → channel_pose
    # This is the key fix: Imu's Stigma, Gojo's Infinity, Blackbeard's darkness,
    # any ki/aura/magic technique maps here and kinetic.vfx renders the actual effect
    if any(k in a for k in (
        "magic", "cast", "channel", "summon", "conjure", "invoke", "omen", "curse",
        "aura", "vortex", "void", "dark", "shadow", "beam", "ray", "blast", "burst",
        "energy", "haki", "conqueror", "spirit", "soul", "flame", "fire", "lightning",
        "thunder", "stigma", "infinity", "hollow", "bankai", "shikai", "domain",
        "kamehame", "rasengan", "chidori", "bijuu", "menacing", "pressure", "intent",
        "malevolent", "cursed", "technique", "imbue", "radiate", "emanate"
    )):
        return "channel_pose"
    # Locked-in / resolve / powerup
    if any(k in a for k in ("locked", "focus", "resolve", "power", "gear", "transform", "mode", "awaken")):
        return "locked_in"
    # Default fallback: unknown but not passive → channel_pose (shows vfx)
    print(f"  [KINETIC] Unknown action '{raw_action}' → channel_pose (vfx will render the effect)")
    return "channel_pose"
VALID_ACCESSORIES = {"straw_hat", "red_beanie", "headphones", "glasses", "crown", "headband", "tie", "flame", "smoke", "blade", "cape", "horns", "spear", "none"}

# Modular Caricature Validation Sets
VALID_SKIN_TONES = {"fair", "pale", "tan", "dark", "bone_white", "green", "blue"}
VALID_HAIR_STYLES = {"blonde_sweep", "green_crop", "massive_afro", "curly_short", "spiky_black", "high_bun", "regal_wavy", "twin_tails", "long_hair", "ponytail", "bob_cut", "bald"}
VALID_HAIR_COLORS = {"blonde", "green", "purple", "black", "white", "brown", "orange", "blue", "red", "pink"}
VALID_CLOTHING_TYPES = {"suit", "corset", "officer_coat", "robe", "vest", "shirt", "dress", "knight_armor", "centaur_cloak"}
VALID_CLOTHING_COLORS = {"black", "purple", "crimson", "blue", "white", "gold", "green", "navy", "pink", "gray"}
VALID_FACE_TRAITS = {"curly_eyebrow", "cigarette", "queen_eyelashes", "lipstick", "eye_scar", "triple_earring", "mustache", "horns", "sharp_teeth", "sinister_smile", "skull"}

VALID_BACKGROUND_STYLES = {"arena_ground", "speed_lines", "clash_burst", "fire_storm", "dark_vortex", "spotlight", "minimal_gradient"}
VALID_MOTION_STYLES = {"combat_idle", "snap_strike", "flurry", "locked_in", "lunge_dash", "recoil"}
VALID_MOTION_PATHS = {"auto", "cross_screen", "charge_in", "lunge_clash", "aerial_dive", "flying", "knockback_slide", "stalk_forward", "stationary"}

class GeminiDirectorAgent:
    """
    Directs video narrative and translates creative topics into strict JSON specifications.
    Enforces a strict Python validation gate before returning any plan to the renderer.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        key = (api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
        self.api_key = key if key else None
        self.model = model

    def _call_gemini_prompt(self, prompt_text: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in environment")

        # 1. Primary: Use Governor / Router with automatic model rotation, RPM/TPM calculation & fallback
        try:
            from stickman_service.gemini_router_module import gemini_router
            gen_config = {"temperature": 0.7, "responseMimeType": "application/json"}
            raw_text = gemini_router.generate(
                task_type="creative",
                prompt=prompt_text,
                gen_config=gen_config,
                module_name="director"
            )
            if raw_text:
                clean = raw_text.strip()
                if clean.startswith("```json"):
                    clean = clean[7:]
                if clean.startswith("```"):
                    clean = clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                return json.loads(clean.strip())
        except Exception as r_err:
            logger.warning(f"Governor routing error in director ({r_err}), attempting direct REST fallback...")

        # 2. Secondary Direct REST Fallback
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"}
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req, timeout=35) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            clean = raw_text.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            return json.loads(clean.strip())

    def _call_gemini(self, topic: str, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        system_prompt = get_director_prompt(aspect_ratio)
        prompt_text = (
            f"{system_prompt}\n\n"
            f"Generate an exact 6-scene stickman explainer video spec for this topic:\n"
            f"TOPIC: {topic}\n"
            f"ASPECT RATIO: {aspect_ratio}\n\n"
            f"Return ONLY valid JSON matching the schema."
        )
        return self._call_gemini_prompt(prompt_text)

    def _generate_fallback(self, topic: str) -> Dict[str, Any]:
        """Dynamic structural baseline if offline or model fails."""
        clean_topic = topic.strip().title()
        stage_names = ["Hook", "Core Conflict", "Key Discovery", "Mechanism", "Resolution", "Final Discussion"]
        return {
            "title": clean_topic,
            "aspect_ratio": "9:16",
            "theme": "dark",
            "scenes": [
                {
                    "scene_id": i + 1,
                    "stage": VALID_STAGES[i],
                    "vo_text": f"Analyzing {clean_topic}: examining {stage_names[i].lower()}.",
                    "badge": VALID_STAGES[i].upper(),
                    "overlay": clean_topic.upper()[:22],
                    "accent_color": "cyan" if i % 2 == 0 else "crimson",
                    "characters": [{"name": "Presenter", "action": "idle", "expression": "neutral", "speed": 1.0, "direction": "right", "x_offset": 0.0, "visual_trait": "none"}],
                    "props": []
                }
                for i in range(6)
            ]
        }

    def validate_and_sanitize(self, raw_spec: Dict[str, Any], fallback_spec: Dict[str, Any], dossier_data: Optional[Dict[str, Any]] = None) -> List[SceneSpec]:
        """
        Python Validation Gate:
        Guarantees exactly 6 scenes, valid actions, valid expressions, and safe parameters.
        When dossier_data is provided, dynamically cross-checks and aligns matchups using
        clash_events extracted from the manga panels without any hardcoded character names.
        """
        raw_scenes = raw_spec.get("scenes", [])
        if len(raw_scenes) != 6:
            print(f"  [GATE-WARN] Model produced {len(raw_scenes)} scenes instead of 6. Merging with fallback blueprint.")
            # Pad or truncate to ensure exactly 6 scenes
            while len(raw_scenes) < 6:
                missing_idx = len(raw_scenes)
                raw_scenes.append(fallback_spec["scenes"][missing_idx])
            raw_scenes = raw_scenes[:6]

        validated_scenes = []
        # Persistent Character Identity Registry across all 6 scenes:
        # Guarantees traits (hair, skin, clothes) never swap onto other characters.
        character_registry: Dict[str, Dict[str, Any]] = {}

        # Map canonical profiles extracted by Vision if dossier is provided
        dossier_profiles: Dict[str, Dict[str, Any]] = {}
        if dossier_data and isinstance(dossier_data, dict):
            for c in dossier_data.get("characters_present", []):
                if isinstance(c, dict) and "name" in c:
                    dossier_profiles[str(c["name"]).strip().lower()] = c

        for i, s in enumerate(raw_scenes):
            scene_id = i + 1
            stage = s.get("stage", VALID_STAGES[i])
            if stage not in VALID_STAGES:
                stage = VALID_STAGES[i]

            vo_text = str(s.get("vo_text", "")).strip()
            words = vo_text.split()
            word_count = len(words)

            # Stage 6 Narration pacing guard (must fit 5 seconds: 8-12 words)
            if scene_id == 6 and word_count > 14:
                print(f"  [GATE-WARN] Stage 6 word count too high ({word_count} words). Trimming to preserve 5s pacing.")
                vo_text = " ".join(words[:11]) + "?"

            # Multi-Character Sanitization (Supports 0, 1, or 2 characters)
            raw_chars = s.get("characters")
            if raw_chars is None:
                # Backward compatibility for singular 'character' key
                single_ch = s.get("character")
                raw_chars = [single_ch] if single_ch else []

            validated_chars: List[CharacterState] = []
            for c_idx, ch_data in enumerate(raw_chars[:2]):
                if not isinstance(ch_data, dict):
                    continue
                name = str(ch_data.get("name", f"Character_{c_idx+1}")).strip()[:30]
                raw_action = str(ch_data.get("action", "idle"))
                # Semantic resolver: maps any action Gemini freely invents to
                # the nearest physical rig pose without crashing or silently
                # falling back to idle. The kinetic dict carries the real VFX.
                action = resolve_action(raw_action)

                expr = str(ch_data.get("expression", "neutral")).lower().strip()
                if expr not in VALID_EXPRESSIONS:
                    expr = "neutral"

                # Staging: if 2 characters, default char 0 right, char 1 left
                default_dir = "right" if c_idx == 0 else "left"
                direction = str(ch_data.get("direction", default_dir)).lower().strip()
                if direction not in ("left", "right"):
                    direction = default_dir

                try:
                    speed = max(0.5, min(1.5, float(ch_data.get("speed", 1.0))))
                except (ValueError, TypeError):
                    speed = 1.0

                # Staging offsets: if 2 characters and unassigned, stage them symmetrically
                default_x = 0.0 if len(raw_chars) == 1 else (-0.32 if c_idx == 0 else 0.32)
                try:
                    x_offset = max(-0.6, min(0.6, float(ch_data.get("x_offset", default_x))))
                except (ValueError, TypeError):
                    x_offset = default_x

                vt = str(ch_data.get("visual_trait", ch_data.get("accessory", "none"))).lower().strip()
                if vt not in VALID_ACCESSORIES:
                    vt = "none"

                raw_att = ch_data.get("attachments", {})
                sanitized_att = {}
                if isinstance(raw_att, dict):
                    for sock, itm in raw_att.items():
                        s_name = str(sock).lower().strip()
                        i_name = str(itm).lower().strip()
                        if s_name in ("head", "mouth", "lead_hand", "rear_hand", "lead_foot", "rear_foot", "torso"):
                            sanitized_att[s_name] = i_name

                # Parse Modular Caricature Visual Traits
                canon_key = name.lower()
                cached_profile = character_registry.get(canon_key)

                skin_tone = str(ch_data.get("skin_tone", "")).lower().strip()
                hair_style = str(ch_data.get("hair_style", "")).lower().strip()
                hair_color = str(ch_data.get("hair_color", "")).lower().strip()
                clothing_type = str(ch_data.get("clothing_type", "")).lower().strip()
                clothing_color = str(ch_data.get("clothing_color", "")).lower().strip()
                raw_ft = ch_data.get("face_traits", [])
                face_traits = [str(f).lower().strip() for f in raw_ft if str(f).lower().strip() in VALID_FACE_TRAITS] if isinstance(raw_ft, list) else []

                if cached_profile:
                    skin_tone = skin_tone if skin_tone in VALID_SKIN_TONES else cached_profile["skin_tone"]
                    hair_style = hair_style if hair_style in VALID_HAIR_STYLES else cached_profile["hair_style"]
                    hair_color = hair_color if hair_color in VALID_HAIR_COLORS else cached_profile["hair_color"]
                    clothing_type = clothing_type if clothing_type in VALID_CLOTHING_TYPES else cached_profile["clothing_type"]
                    clothing_color = clothing_color if clothing_color in VALID_CLOTHING_COLORS else cached_profile["clothing_color"]
                    face_traits = face_traits if face_traits else list(cached_profile["face_traits"])
                else:
                    # Resolve traits dynamically: prioritize Vision Dossier profiles over hardcoded rules
                    d_prof = dossier_profiles.get(canon_key)
                    if not d_prof:
                        for pk, pv in dossier_profiles.items():
                            if pk in canon_key or canon_key in pk:
                                d_prof = pv
                                break

                    if d_prof:
                        skin_tone = skin_tone if skin_tone in VALID_SKIN_TONES else d_prof.get("skin_tone", "fair")
                        hair_style = hair_style if hair_style in VALID_HAIR_STYLES and hair_style != "bald" else d_prof.get("hair_style", "short_spiky")
                        hair_color = hair_color if hair_color in VALID_HAIR_COLORS else d_prof.get("hair_color", "black")
                        clothing_type = clothing_type if clothing_type in VALID_CLOTHING_TYPES and clothing_type != "shirt" else d_prof.get("clothing_type", "coat")
                        clothing_color = clothing_color if clothing_color in VALID_CLOTHING_COLORS else d_prof.get("clothing_color", "black")
                        if not face_traits and isinstance(d_prof.get("face_traits"), list):
                            face_traits = [ft for ft in d_prof["face_traits"] if ft in VALID_FACE_TRAITS]
                        vt = d_prof.get("visual_trait", "none")
                        if vt in ("spear", "blade") and "lead_hand" not in sanitized_att:
                            sanitized_att["lead_hand"] = vt
                        elif vt in ("horns", "crown", "top_hat") and "head" not in sanitized_att:
                            sanitized_att["head"] = vt
                    else:
                        skin_tone = skin_tone if skin_tone in VALID_SKIN_TONES else "fair"
                        hair_style = hair_style if hair_style in VALID_HAIR_STYLES else "short_spiky"
                        hair_color = hair_color if hair_color in VALID_HAIR_COLORS else "black"
                        clothing_type = clothing_type if clothing_type in VALID_CLOTHING_TYPES else "shirt"
                        clothing_color = clothing_color if clothing_color in VALID_CLOTHING_COLORS else "white"

                    # Lock into registry for consistent multi-scene continuity
                    character_registry[canon_key] = {
                        "skin_tone": skin_tone,
                        "hair_style": hair_style,
                        "hair_color": hair_color,
                        "clothing_type": clothing_type,
                        "clothing_color": clothing_color,
                        "face_traits": list(face_traits)
                    }

                motion_style = str(ch_data.get("motion_style", "")).lower().strip()
                if motion_style not in VALID_MOTION_STYLES:
                    if action in ("kick", "punch", "flame_strike"):
                        motion_style = "snap_strike"
                    elif action == "spear_thrust":
                        motion_style = "lunge_dash"
                    elif action == "barrage":
                        motion_style = "flurry"
                    elif action == "locked_in":
                        motion_style = "locked_in"
                    elif action == "channel_pose":
                        motion_style = "locked_in"
                    elif action == "defend":
                        motion_style = "recoil"
                    else:
                        motion_style = "combat_idle"

                # ── Kinetic VFX Grammar parsing ───────────────────────────────
                raw_kinetic = ch_data.get("kinetic", {})
                kinetic = {}
                if isinstance(raw_kinetic, dict) and raw_kinetic:
                    kinetic = raw_kinetic
                    # If Gemini set kinetic but left action as the technique name,
                    # the resolver already converted it. Keep kinetic intact.
                elif action == "channel_pose" and not raw_kinetic:
                    # Gemini directed a magic action but forgot the kinetic block.
                    # Build a sensible default from attachments + expression.
                    vfx_color = "#1a0033" if ch_data.get("expression") in ("menacing", "furious") else "#003366"
                    kinetic = {
                        "technique_name": raw_action,
                        "pose": {"posture": "floating", "lead_arm": "outstretched_palm", "trail_arm": "behind_back", "legs": "hover_straight"},
                        "vfx": {"type": "swirling_vortex", "origin": "all_around", "primary_color": vfx_color, "secondary_color": "#550000", "intensity": 0.8, "scale": 1.2}
                    }

                m_path = str(ch_data.get("motion_path", "auto")).lower().strip()
                if m_path not in VALID_MOTION_PATHS:
                    m_path = "auto"

                try:
                    altitude = max(0.0, min(1.0, float(ch_data.get("altitude", 0.0))))
                except (ValueError, TypeError):
                    altitude = 0.0

                start_x = ch_data.get("start_x")
                if start_x is not None:
                    try:
                        start_x = max(-0.6, min(0.6, float(start_x)))
                    except (ValueError, TypeError):
                        start_x = None

                end_x = ch_data.get("end_x")
                if end_x is not None:
                    try:
                        end_x = max(-0.6, min(0.6, float(end_x)))
                    except (ValueError, TypeError):
                        end_x = None

                validated_chars.append(CharacterState(
                    name=name,
                    action=action,
                    expression=expr,
                    speed=speed,
                    direction=direction,
                    x_offset=x_offset,
                    accessory=vt if vt != "none" else None,
                    visual_trait=vt,
                    attachments=sanitized_att,
                    skin_tone=skin_tone,
                    hair_style=hair_style,
                    hair_color=hair_color,
                    clothing_type=clothing_type,
                    clothing_color=clothing_color,
                    face_traits=face_traits,
                    motion_style=motion_style,
                    motion_path=m_path,
                    altitude=altitude,
                    start_x=start_x,
                    end_x=end_x,
                    kinetic=kinetic
                ))

            # Props Sanitization (Supports all 1,500+ Lucide vector icons)
            props = []
            for p in s.get("props", []):
                p_type = str(p.get("type", "")).lower().strip()
                # Accept any valid Lucide icon name or legacy procedural prop
                if p_type and all(c.isalnum() or c == "-" for c in p_type):
                    anim = str(p.get("animation", "anim-float")).lower()
                    if anim not in {"anim-float", "anim-pulse", "anim-spin", "anim-bounce"}:
                        anim = "anim-float"
                    try:
                        size = max(60, min(120, int(p.get("size", 85))))
                    except (ValueError, TypeError):
                        size = 85
                    props.append(PropSpec(type=p_type, params=p.get("params", {}), animation=anim, size=size))
            
            if not props and len(validated_chars) <= 1 and "props" not in s:
                # Default friendly prop for single explainer stickman when props not specified
                props.append(PropSpec(type="zap", animation="anim-float", size=85))

            color = str(s.get("accent_color", "cyan")).lower()
            if color not in VALID_COLORS:
                color = "cyan"

            badge = str(s.get("badge", f"STAGE {scene_id}")).upper()[:20]
            overlay = str(s.get("overlay", "EXPLORING TOPIC")).upper()[:35]

            # Dynamic Background & Camera Shake Directed by Gemini
            bg_style = str(s.get("background_style", "")).lower().strip()
            if bg_style not in VALID_BACKGROUND_STYLES:
                # Intelligently infer from narrative drama if unspecified
                has_magic = any(ch.action == "channel_pose" or bool(ch.kinetic) for ch in validated_chars)
                if has_magic:
                    bg_style = "dark_vortex"
                elif stage in ("hook", "climax") or any(ch.action in ("kick", "punch", "flame_strike", "spear_thrust") for ch in validated_chars):
                    bg_style = "speed_lines" if i % 2 == 0 else "clash_burst"
                elif any("flame" in str(ch.attachments.values()) or ch.action == "flame_strike" for ch in validated_chars):
                    bg_style = "fire_storm"
                elif stage == "disrupt" or any(ch.expression in ("furious", "menacing") for ch in validated_chars):
                    bg_style = "dark_vortex"
                else:
                    bg_style = "arena_ground"

            try:
                cam_shake = max(0.0, min(1.0, float(s.get("camera_shake", 0.0))))
            except (ValueError, TypeError):
                cam_shake = 0.5 if bg_style in ("clash_burst", "speed_lines") else 0.0

            primary_char = validated_chars[0] if validated_chars else CharacterState()
            scene = SceneSpec(
                scene_id=scene_id,
                stage=stage,
                vo_text=vo_text,
                badge=badge,
                overlay=overlay,
                character=primary_char,
                characters=validated_chars,
                props=props,
                accent_color=color,
                background_style=bg_style,
                camera_shake=cam_shake
            )
            validated_scenes.append(scene)

        # Dynamic Chapter Dossier Matchup Guard (Zero Hardcoding):
        # Cross-checks scene pairings against clash_events dynamically extracted from the manga PDF.
        if dossier_data and isinstance(dossier_data, dict):
            clash_events = dossier_data.get("clash_events", [])
            chars_present = dossier_data.get("characters_present", [])
            
            # Map canonical profiles extracted by Vision
            dossier_profiles = {
                str(c.get("name", "")).strip().lower(): c 
                for c in chars_present if isinstance(c, dict) and "name" in c
            }

            # Map valid combat pairings dynamically from clash_events
            combat_pairings: Dict[str, str] = {}
            for evt in clash_events:
                if not isinstance(evt, dict):
                    continue
                actor = str(evt.get("actor", "")).strip()
                target = str(evt.get("target", "")).strip()
                if actor and target:
                    combat_pairings[actor.lower()] = target
                    combat_pairings[target.lower()] = actor

            # Check if any scene contains a protagonist paired with an adversary who is fighting someone else
            corrected_names_map: Dict[str, str] = {}
            for sc in validated_scenes:
                if len(sc.characters) == 2:
                    c0_name = sc.characters[0].name
                    c1_name = sc.characters[1].name
                    c0_key = c0_name.lower()
                    c1_key = c1_name.lower()

                    # Does character 0 have a designated opponent in clash_events?
                    expected_target = combat_pairings.get(c0_key)
                    if not expected_target:
                        for pk, pv in combat_pairings.items():
                            if pk in c0_key or c0_key in pk:
                                expected_target = pv
                                break

                    if expected_target and (expected_target.lower() not in c1_key and c1_key not in expected_target.lower()):
                        print(f"  [GATE-SHIELD] Dynamically detected matchup mismatch in Scene {sc.scene_id}: '{c0_name}' paired with '{c1_name}', but dossier specifies '{expected_target}'! Auto-aligning.")
                        old_wrong_name = sc.characters[1].name
                        sc.characters[1].name = expected_target
                        corrected_names_map[old_wrong_name] = expected_target

                        # Re-apply traits dynamically from dossier profile if available
                        target_prof = dossier_profiles.get(expected_target.lower())
                        if not target_prof:
                            for pk, pv in dossier_profiles.items():
                                if pk in expected_target.lower() or expected_target.lower() in pk:
                                    target_prof = pv
                                    break
                        if target_prof:
                            if target_prof.get("skin_tone") in VALID_SKIN_TONES:
                                sc.characters[1].skin_tone = target_prof["skin_tone"]
                            if target_prof.get("hair_style") in VALID_HAIR_STYLES:
                                sc.characters[1].hair_style = target_prof["hair_style"]
                            if target_prof.get("hair_color") in VALID_HAIR_COLORS:
                                sc.characters[1].hair_color = target_prof["hair_color"]
                            if target_prof.get("clothing_type") in VALID_CLOTHING_TYPES:
                                sc.characters[1].clothing_type = target_prof["clothing_type"]
                            if target_prof.get("clothing_color") in VALID_CLOTHING_COLORS:
                                sc.characters[1].clothing_color = target_prof["clothing_color"]
                            if isinstance(target_prof.get("face_traits"), list):
                                sc.characters[1].face_traits = [ft for ft in target_prof["face_traits"] if ft in VALID_FACE_TRAITS]
                            if isinstance(target_prof.get("attachments"), dict):
                                for sk, sv in target_prof["attachments"].items():
                                    if sk in ("head", "mouth", "lead_hand", "rear_hand", "lead_foot", "rear_foot", "torso"):
                                        sc.characters[1].attachments[sk] = sv
                            vt = target_prof.get("visual_trait", "none")
                            if vt in ("spear", "blade") and "lead_hand" not in sc.characters[1].attachments:
                                sc.characters[1].attachments["lead_hand"] = vt
                            elif vt in ("horns", "crown", "top_hat") and "head" not in sc.characters[1].attachments:
                                sc.characters[1].attachments["head"] = vt
                            sc.characters[1].visual_trait = vt

            # Propagate corrected names across all scene voiceover texts, overlays, and badges
            for wrong_name, true_name in corrected_names_map.items():
                for sc in validated_scenes:
                    sc.vo_text = sc.vo_text.replace(wrong_name, true_name)
                    sc.overlay = sc.overlay.replace(wrong_name.upper(), true_name.upper())
                    sc.badge = sc.badge.replace(wrong_name.upper(), true_name.upper())

        return validated_scenes

    def direct_topic(self, topic: str, aspect_ratio: str = "9:16") -> VideoStorySpec:
        """
        Directs a topic into a fully validated VideoStorySpec.
        """
        fallback_spec = self._generate_fallback(topic)
        fallback_spec["aspect_ratio"] = aspect_ratio
        raw_spec = None

        if self.api_key:
            try:
                print(f"[*] Calling Gemini ({self.model}) to structure topic: '{topic}' ({aspect_ratio})...")
                raw_spec = self._call_gemini(topic, aspect_ratio=aspect_ratio)
            except Exception as e:
                print(f"[!] Gemini API call failed or timed out ({e}). Using intelligent structural director.")

        if not raw_spec:
            raw_spec = fallback_spec

        # Resolve Accessory (Strictly directed by Gemini or none - zero hardcoded keyword heuristics)
        accessory = str(raw_spec.get("accessory", "none")).lower().strip()
        if accessory not in VALID_ACCESSORIES:
            accessory = "none"

        # Execute the Python Validation Gate
        validated_scenes = self.validate_and_sanitize(raw_spec, fallback_spec)

        return VideoStorySpec(
            title=str(raw_spec.get("title", topic)).title(),
            aspect_ratio=aspect_ratio,
            theme="dark",
            accessory=accessory,
            scenes=validated_scenes
        )

    def direct_script(self, script_text: str, aspect_ratio: str = "9:16", accessory: Optional[str] = None) -> VideoStorySpec:
        """
        Takes an exact voiceover script and choreographs it into a 6-stage stickman video spec.
        """
        system_prompt = get_director_prompt(aspect_ratio)
        prompt_text = (
            f"{system_prompt}\n\n"
            f"TASK: CHOREOGRAPH AND DIRECT THIS EXACT SCRIPT INTO A 6-SCENE STICKMAN VIDEO SPEC.\n"
            f"IMPORTANT: Use the script's lines as the voiceover ('vo_text') across the 6 stages (Hook -> Disrupt -> Secret -> Mechanism -> Truth -> Call-To-Action/Debate).\n"
            f"Choreograph character actions, expressions, Lucide vector props, and mood accent colors to visually punctuate every spoken sentence.\n\n"
            f"USER SCRIPT:\n{script_text}\n\n"
            f"ASPECT RATIO: {aspect_ratio}\n"
            f"DESIRED ACCESSORY: {accessory or 'auto'}\n\n"
            f"Return ONLY valid JSON matching the schema."
        )

        fallback_spec = self._generate_fallback("Script Explainer")
        raw_spec = None
        if self.api_key:
            try:
                print(f"[*] Calling Gemini ({self.model}) to choreograph user script ({aspect_ratio})...")
                raw_spec = self._call_gemini_prompt(prompt_text)
            except Exception as e:
                print(f"[!] Gemini direct_script failed ({e}). Using fallback choreography.")

        if not raw_spec:
            # Map script paragraphs/sentences into the 6 fallback scenes
            lines = [l.strip() for l in script_text.splitlines() if l.strip()]
            for i in range(min(6, len(lines))):
                fallback_spec["scenes"][i]["vo_text"] = lines[i][:150]
            raw_spec = fallback_spec

        acc = (accessory or raw_spec.get("accessory", "none")).lower().strip()
        if acc not in VALID_ACCESSORIES:
            acc = "none"

        validated_scenes = self.validate_and_sanitize(raw_spec, fallback_spec)

        return VideoStorySpec(
            title=str(raw_spec.get("title", "Script Breakdown")).title(),
            aspect_ratio=aspect_ratio,
            theme="dark",
            accessory=acc,
            scenes=validated_scenes
        )

    def direct_manga(self, manga_title: str, chapter_text_or_summary: str, aspect_ratio: str = "9:16", accessory: Optional[str] = None) -> VideoStorySpec:
        """
        Takes a manga title and extracted chapter text or summary dossier, directing an anime recap stickman video.
        Supports dynamic 1 or 2 character combat scenes, clashes, and visual traits (flame, blade, cape, etc.).
        """
        system_prompt = get_director_prompt(aspect_ratio)
        prompt_text = (
            f"{system_prompt}\n\n"
            f"TASK: DIRECT AN ELECTRIFYING, WITTY, AND HIGHLY ENTERTAINING 6-SCENE STICKMAN MANGA BREAKDOWN VIDEO FOR SHORTS/TIKTOK.\n"
            f"MANGA TITLE: {manga_title}\n"
            f"CHAPTER DOSSIER & SCENE DATA:\n{chapter_text_or_summary[:4000]}\n\n"
            f"VIRAL CREATOR SCRIPTWRITING & NARRATIVE INSTRUCTIONS:\n"
            f"1. CLEAR GOOD VS BAD (TAKE SIDES!):\n"
            f"   - Clearly establish the Heroes/Protagonists identified in the dossier fighting for their allies.\n"
            f"   - Clearly establish the Villains/Antagonists (the arrogant villains, oppressors, or enemy commanders identified in the dossier) as entitled bullies.\n"
            f"   - Hype the heroes' courage and ruthlessly clown the villains' arrogance!\n"
            f"2. SARCASM, ROASTING & COMEDY (BE WITTY & ENGAGING):\n"
            f"   - Roast the villain's ego, ridiculous powers, and shocking failures! (e.g., 'Bro really thought he was an untouchable god until he caught a flaming boot to the jaw', 'Imagine flexing for ten chapters only to get folded like a lawn chair').\n"
            f"   - Add comedic reactions and witty banter about the wild manga events (like fighting your own sleep paralysis demon or watching an arrogant villain panic).\n"
            f"3. ZERO ROBOTIC / ACADEMIC MONOLOGUE:\n"
            f"   - BANNED: 'inner battle', 'commenced', 'manifested', 'subsequently', 'a formidable encounter'.\n"
            f"   - INSTEAD: Write punchy, spoken conversational sentences packed with energy, attitude, and swagger.\n"
            f"4. 6-STAGE VIRAL STORYLINE:\n"
            f"   - Stage 1: The Outrageous Hook (20-24 words) -> Drop a scroll-stopping statement or sarcastic joke about the chapter.\n"
            f"   - Stage 2: The Villain's Arrogance (20-24 words) -> Show how entitled the villain acted before getting checked.\n"
            f"   - Stage 3: The Secret Counter / Powerup (20-24 words) -> The moment the hero reveals their technique or breaks the trap.\n"
            f"   - Stage 4: The Roast & Stakes (28-34 words) -> Sarcastic comedic breakdown of the villain's panic or bad decisions.\n"
            f"   - Stage 5: The Ultimate Beatdown / Payoff (20-24 words) -> The decisive strike or mic-drop declaration that broke the internet.\n"
            f"   - Stage 6: The Community Roast / Debate (STRICTLY 8-12 words) -> A funny, spicy debate question for the comments.\n"
            f"5. MANDATORY MANGA COMBAT GROUNDING & CHARACTER ACTIONS:\n"
            f"   You MUST direct each character's 'action', 'motion_style', 'motion_path', and 'altitude' strictly based on what they physically do in the chapter panels and clash events:\n"
            f"   - AIRBORNE & FLIGHT: If a character is airborne, leaping through the sky, or using flight:\n"
            f"     * 'action': 'flying' or 'air_dash'\n"
            f"     * 'motion_path': 'flying' or 'aerial_dive'\n"
            f"     * 'altitude': 0.45 to 0.75\n"
            f"     * 'attachments': {{'lead_foot': 'flame'}} if propelling with fire\n"
            f"   - SPRINTING / RUSH: If charging into battle across distance:\n"
            f"     * 'action': 'run'\n"
            f"     * 'motion_path': 'charge_in'\n"
            f"     * 'speed': 1.2 to 1.4\n"
            f"   - MARTIAL KICK & FLAME STRIKE: If executing martial kicks or flame strikes:\n"
            f"     * 'action': 'flame_strike' or 'kick'\n"
            f"     * 'motion_style': 'snap_strike'\n"
            f"     * 'motion_path': 'lunge_clash'\n"
            f"     * 'attachments': {{'lead_foot': 'flame'}}\n"
            f"     * Target's action: 'defend' or 'fall' (with 'motion_path': 'knockback_slide')\n"
            f"   - WEAPON ATTACKS (SPEAR THRUST / BLADE SLASH): If attacking with polearm spear or sword slash:\n"
            f"     * 'action': 'spear_thrust' (or 'punch')\n"
            f"     * 'motion_style': 'lunge_dash'\n"
            f"     * 'attachments': {{'lead_hand': 'spear' or 'blade'}}\n"
            f"   - TANKING / DEFENDING / RECOIL: If absorbing hits, impalement, or blocking:\n"
            f"     * 'action': 'defend' or 'recoil'\n"
            f"     * 'motion_style': 'recoil'\n"
            f"   - KNOCKBACK IMPACT: If blasted backward, sent flying, or taking heavy damage:\n"
            f"     * 'action': 'fall'\n"
            f"     * 'motion_path': 'knockback_slide'\n"
            f"     * 'expression': 'shocked'\n"
            f"   - LOCKED-IN COMBAT RESOLVE: If calmly focusing, lighting a cigarette, or breaking fear:\n"
            f"     * 'action': 'locked_in'\n"
            f"     * 'motion_style': 'locked_in'\n"
            f"     * 'expression': 'confident' or 'menacing'\n"
            f"     * 'attachments': {{'mouth': 'cigarette'}}\n"
            f"   - STRICT RULE: NEVER assign childish or generic actions like 'celebrate', 'shrug', or 'point' during combat scenes! Every action must physically mirror the real fight choreography from the chapter!\n\n"
            f"6. MULTI-CHARACTER COMBAT STAGING:\n"
            f"   - In 2-character scenes, stage the Hero on the left (x_offset: -0.32 facing right) and the Villain on the right (x_offset: 0.32 facing left).\n"
            f"   - Coordinate actions so when the attacker lunges ('lunge_clash', 'spear_thrust', 'flame_strike'), the target reacts ('defend', 'fall').\n"
            f"   - Strike effects ('flame', 'blade') belong ONLY to the active attacker, NEVER to the defending villain.\n"
            f"   - Backgrounds: Choose 'fire_storm' for intense flame strikes, 'speed_lines' for dashes/rushes, 'clash_burst' for decisive impact blows, 'arena_ground' for tactical standoffs.\n"
            f"   - ENTRANCE BANNER ('badge'): 2-3 word UPPERCASE banner (e.g. 'FRAUD ALERT', 'CLASH POINT', 'COOKED'). Appears for 2 seconds.\n\n"
            f"ASPECT RATIO: {aspect_ratio}\n"
            f"Return ONLY valid JSON matching the schema."
        )

        fallback_spec = self._generate_fallback(f"{manga_title} Chapter Breakdown")
        raw_spec = None
        if self.api_key:
            try:
                print(f"[*] Calling Gemini ({self.model}) to direct manga recap: '{manga_title}' ({aspect_ratio})...")
                raw_spec = self._call_gemini_prompt(prompt_text)

                # Tier 1: Gemini Canon Reviewer Double-Confirmation Gate
                if raw_spec and isinstance(raw_spec, dict) and "scenes" in raw_spec:
                    try:
                        print(f"[*] Double-confirming script with Gemini Canon Reviewer (checking matchups & anti-hallucination)...")
                        reviewed_spec = self._review_and_verify_manga_spec(raw_spec, chapter_text_or_summary, manga_title)
                        if reviewed_spec and isinstance(reviewed_spec, dict) and "scenes" in reviewed_spec:
                            raw_spec = reviewed_spec
                            print(f"[OK] Script reviewed and double-confirmed by Gemini Canon Reviewer.")
                    except Exception as rev_err:
                        print(f"[!] Canon Reviewer note ({rev_err}), continuing with sanitized spec.")
            except Exception as e:
                print(f"[!] Gemini direct_manga failed ({e}). Using fallback.")

        if not raw_spec:
            raw_spec = fallback_spec

        acc = (accessory or raw_spec.get("accessory", "none")).lower().strip()
        if acc not in VALID_ACCESSORIES:
            acc = "none"

        dossier_dict = None
        if isinstance(chapter_text_or_summary, str):
            try:
                dossier_dict = json.loads(chapter_text_or_summary)
            except Exception:
                pass
        elif isinstance(chapter_text_or_summary, dict):
            dossier_dict = chapter_text_or_summary

        validated_scenes = self.validate_and_sanitize(raw_spec, fallback_spec, dossier_data=dossier_dict)

        return VideoStorySpec(
            title=str(raw_spec.get("title", f"{manga_title} Chapter Recap")).title(),
            aspect_ratio=aspect_ratio,
            theme="dark",
            accessory=acc,
            scenes=validated_scenes
        )

    def _review_and_verify_manga_spec(self, raw_spec: Dict[str, Any], chapter_dossier_text: str, manga_title: str) -> Dict[str, Any]:
        """
        Gemini Double-Confirmation & Canon Verification Gate:
        Audits the generated story spec against chapter facts and trained manga canon knowledge.
        Strictly catches and fixes:
        - Opponent mix-ups / swapped matchups across different parallel battles.
        - Hallucinated characters not present in this chapter.
        - Mismatched weapon attachments (swords, spears, flames, etc.).
        - Voiceover narrative consistency (making sure the spoken text names the true opponent).
        """
        review_prompt = (
            f"You are the STRICT CANON REVIEWER & FACT-CHECK AUDITOR for '{manga_title}'.\n"
            f"Audit and double-confirm the generated stickman video script against the actual chapter dossier facts and your trained canon knowledge:\n\n"
            f"CHAPTER FACTS & EVIDENCE:\n{chapter_dossier_text[:3500]}\n\n"
            f"DRAFT STORY SPEC TO AUDIT:\n{json.dumps(raw_spec, indent=2)}\n\n"
            f"MANDATORY AUDIT CRITERIA:\n"
            f"1. DYNAMIC OPPONENT & MATCHUP INTEGRITY:\n"
            f"   - Cross-check every 2-character matchup against 'clash_events' in the chapter dossier!\n"
            f"   - If multiple parallel battles occur in the chapter, NEVER mix up opponents from different subplots!\n"
            f"   - If a protagonist is placed against an opponent they never encounter in 'clash_events', IMMEDIATELY correct the opponent to their true adversary from the dossier across character names, visual traits, weapons, and voiceover text!\n"
            f"2. BATTLE ACTIONS & TRAITS:\n"
            f"   - Ensure each character's action matches what they did in the manga panel (e.g. kicks, flame strikes, weapon thrusts, defend, fall).\n"
            f"   - Ensure weapon attachments and visual traits match the dossier profiles.\n"
            f"3. SCRIPT CONSISTENCY:\n"
            f"   - Ensure the spoken narration ('vo_text') names the EXACT correct opponent being fought on screen.\n\n"
            f"Return ONLY valid JSON with the audited and verified story spec matching the exact schema."
        )
        return self._call_gemini_prompt(review_prompt)

