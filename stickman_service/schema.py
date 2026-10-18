from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class CharacterState:
    name: str = "Stickman"
    action: str = "idle"       # "idle", "walk", "run", "sit", "point", "celebrate", "shrug", "shocked", "kick", "punch", "defend", "kneel", "fall"
    expression: str = "neutral" # "neutral", "smirk", "shocked", "deadpan", "smile", "angry"
    speed: float = 1.0
    direction: str = "right"   # "left", "right"
    x_offset: float = 0.0      # -0.6 to 0.6 relative to center
    accessory: Optional[str] = None # Backwards compatibility
    visual_trait: Optional[str] = "none" # Backwards compatibility
    attachments: Dict[str, str] = field(default_factory=dict) # Sockets: "head", "mouth", "lead_hand", "rear_hand", "lead_foot", "rear_foot", "torso"
    # Modular Caricature Visual Identity
    skin_tone: str = "fair"       # "fair", "pale", "tan", "dark", "bone_white", "green"
    hair_style: str = "bald"      # "blonde_sweep", "green_crop", "massive_afro", "curly_short", "spiky_black", "high_bun", "regal_wavy", "bald"
    hair_color: str = "black"     # "blonde", "green", "purple", "black", "white", "brown", "orange"
    clothing_type: str = "shirt"  # "suit", "dress", "officer_coat", "corset", "shirt", "vest", "robe"
    clothing_color: str = "white" # "black", "purple", "crimson", "blue", "pink", "green", "white", "gold"
    face_traits: List[str] = field(default_factory=list) # "curly_eyebrow", "cigarette", "queen_eyelashes", "lipstick", "eye_scar", "triple_earring", "mustache", "horns", "sharp_teeth", "sinister_smile"
    motion_style: str = "combat_idle" # "combat_idle", "snap_strike", "flurry", "locked_in", "lunge_dash", "recoil"
    motion_path: str = "auto"         # "auto", "cross_screen", "charge_in", "lunge_clash", "aerial_dive", "flying", "knockback_slide", "stalk_forward", "stationary"
    altitude: float = 0.0             # 0.0 (grounded) to 1.0 (high aerial flight)
    start_x: Optional[float] = None   # starting spatial offset
    end_x: Optional[float] = None     # ending spatial offset

    # ── Gemini Generative Kinetic & VFX Grammar ──────────────────────────────
    # Gemini uses this dict to express ANY combat pose or power that doesn't
    # fit the physical action library — magic, aura, void, beam, etc.
    # The engine reads this and renders procedural VFX with zero hardcoded names.
    # Structure:
    # {
    #   "technique_name": "Stigma",         # Canon move name (for HUD or debug)
    #   "pose": {
    #     "posture": "floating",             # grounded|floating|kneeling|crouching|arched
    #     "lead_arm": "outstretched_palm",   # outstretched_palm|skyward|claw|crossed|blade_hold|guard|tucked
    #     "trail_arm": "behind_back",        # behind_back|guard|side|skyward|tucked
    #     "legs": "hover_straight"           # hover_straight|combat_stride|wide_stance|kick_extended|kneel_one
    #   },
    #   "vfx": {
    #     "type": "swirling_vortex",         # swirling_vortex|lightning_burst|slash_cleave|aura_field|
    #                                        # energy_beam|tendril_spears|dark_miasma|shockwave_ring|particle_storm
    #     "origin": "ground",               # ground|palms|eyes|body_core|lead_foot|lead_hand|all_around
    #     "primary_color": "#0d021a",        # Hex color string
    #     "secondary_color": "#8b0000",      # Hex color string
    #     "intensity": 0.9,                  # 0.0 to 1.0
    #     "scale": 1.5                       # 0.5 to 3.0
    #   }
    # }
    kinetic: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.attachments:
            self.attachments = {}
            if self.accessory and self.accessory != "none":
                self.attachments["head"] = self.accessory
            if self.visual_trait and self.visual_trait != "none":
                if self.visual_trait in ("straw_hat", "red_beanie", "headphones", "glasses", "crown", "headband", "horns"):
                    self.attachments["head"] = self.visual_trait
                elif self.visual_trait in ("cape", "tie"):
                    self.attachments["torso"] = self.visual_trait
                elif self.visual_trait == "flame":
                    sock = "lead_hand" if self.action == "punch" else "lead_foot"
                    self.attachments[sock] = "flame"
                elif self.visual_trait == "blade":
                    self.attachments["lead_hand"] = "blade"
                elif self.visual_trait == "smoke":
                    self.attachments["lead_foot"] = "smoke"

@dataclass
class PropSpec:
    type: str                  # Any Lucide icon name (e.g. "coffee", "brain", "skull", "anchor", "tv", etc.)
    params: Dict[str, Any] = field(default_factory=dict)
    animation: str = "anim-float" # "anim-float", "anim-pulse", "anim-spin", "anim-bounce"
    size: int = 85

@dataclass
class SceneSpec:
    scene_id: int
    stage: str                 # "hook", "disrupt", "insider_secret", "mechanism", "truth", "elevation"
    vo_text: str               # Voiceover spoken text (20-25 words)
    badge: str                 # Header pill badge (e.g. "THE TRAP", "REALITY CHECK")
    overlay: str               # Bottom highlight text (e.g. "SUNK COST FALLACY")
    character: CharacterState = field(default_factory=CharacterState)
    characters: List[CharacterState] = field(default_factory=list)
    props: List[PropSpec] = field(default_factory=list)
    accent_color: str = "cyan" # "cyan", "crimson", "gold", "emerald", "violet", "amber"
    background_style: str = "spotlight" # "arena_ground", "speed_lines", "clash_burst", "fire_storm", "dark_vortex", "spotlight", "minimal_gradient"
    camera_shake: float = 0.0  # 0.0 to 1.0 (visceral strike impact / clash intensity)

    def __post_init__(self):
        if not self.characters and self.character:
            self.characters = [self.character]
        elif self.characters and (not self.character or self.character.action == "idle" and self.character.name == "Stickman"):
            self.character = self.characters[0]

@dataclass
class VideoStorySpec:
    title: str
    aspect_ratio: str = "9:16"
    theme: str = "dark"        # "dark", "light"
    fps: int = 25
    voice_name: str = "en-US-ChristopherNeural"
    accessory: str = "none"    # Global fallback accessory ("none" by default)
    scenes: List[SceneSpec] = field(default_factory=list)
