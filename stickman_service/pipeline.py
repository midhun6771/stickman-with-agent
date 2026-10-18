import os
import sys
import json
import shutil
import asyncio
import argparse
from pathlib import Path
from typing import Optional

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

# Auto-load .env file if present
env_file = ROOT_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from stickman_service.agent import GeminiDirectorAgent
from stickman_service.agent.prompts import ASPECT_PROFILES
from stickman_service.engine import VideoRenderer

async def run_pipeline(
    topic: Optional[str] = None,
    script: Optional[str] = None,
    manga_pdf: Optional[str] = None,
    accessory: Optional[str] = None,
    output_path: str = None,
    api_key: str = None,
    ratio: str = "9:16",
    preview: bool = False,
    publish: bool = False
):
    profile = ASPECT_PROFILES.get(ratio, ASPECT_PROFILES["9:16"])
    width = profile["width"]
    height = profile["height"]

    print("================================================================")
    print("   AI STICKMAN AGENT SERVICE: CREATIVE DIRECTOR & MATH ENGINE   ")
    print("================================================================")
    print(f"[*] Aspect Ratio: {ratio} ({width}x{height})")

    director = GeminiDirectorAgent(api_key=api_key)

    # Step 1: Creative Director Agent (Topic vs Script vs Manga)
    if script:
        print("[*] Mode: Directing from User-Provided Script...")
        title_base = "script_breakdown"
        story_spec = director.direct_script(script, aspect_ratio=ratio, accessory=accessory)
    elif manga_pdf:
        print(f"[*] Mode: Directing from Manga/Comic PDF: '{manga_pdf}'...")
        from stickman_service.engine.manga_extractor import MangaExtractor
        extractor = MangaExtractor()
        manga_name = Path(manga_pdf).stem
        title_base = f"manga_{manga_name}"
        image_paths, embedded_text = extractor.extract_pdf_pages(manga_pdf)
        print(f"[OK] Extracted {len(image_paths)} pages from PDF.")
        summary = extractor.understand_manga_chapter(manga_name, image_paths, director.api_key, embedded_text)
        story_spec = director.direct_manga(manga_name, summary, aspect_ratio=ratio, accessory=accessory)
    else:
        topic_str = topic or "Stickman Explainer"
        print(f"[*] Mode: Directing from Topic: '{topic_str}'...")
        title_base = topic_str
        story_spec = director.direct_topic(topic_str, aspect_ratio=ratio)
        if accessory and accessory != "none":
            story_spec.accessory = accessory

    print(f"[OK] Story structured: '{story_spec.title}' with {len(story_spec.scenes)} narrative stages.")
    print(f"[*] Global Accessory Fallback: '{story_spec.accessory}'")

    # Determine output file
    if not output_path:
        slug = "".join(c if c.isalnum() else "_" for c in title_base.lower())[:30].strip("_")
        output_dir = Path("d:/Stickman/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        final_mp4 = output_dir / f"{slug}_{ratio.replace(':', '_')}.mp4"
    else:
        final_mp4 = Path(output_path)
        final_mp4.parent.mkdir(parents=True, exist_ok=True)

    # Step 2: Deterministic Math & Layout Video Renderer
    temp_work_dir = final_mp4.parent / f"build_{final_mp4.stem}"
    renderer = VideoRenderer(output_dir=temp_work_dir, width=width, height=height)

    # Prepare audio first to get exact measured durations
    print(f"[*] Synthesizing voiceover and measuring exact timings...")
    total_audio_duration = await renderer.prepare_audio(story_spec)

    # Copy scene audio files to web player directory
    web_dir = Path(__file__).resolve().parent / "web"
    web_audio_dir = web_dir / "audio"
    web_audio_dir.mkdir(parents=True, exist_ok=True)

    scenes_data = []
    for s in story_spec.scenes:
        dur = s.params.get("duration", 6.5)
        src_audio = s.params.get("audio_path")
        audio_rel_url = ""
        if src_audio and Path(src_audio).exists():
            dest_audio = web_audio_dir / f"scene_{s.scene_id}.mp3"
            shutil.copy2(src_audio, dest_audio)
            audio_rel_url = f"audio/scene_{s.scene_id}.mp3"

        p_first = s.props[0] if s.props else None
        prop_data = {
            "name": p_first.type if p_first else "zap",
            "size": getattr(p_first, "size", 85) if p_first else 85,
            "animation": getattr(p_first, "animation", "anim-float") if p_first else "anim-float"
        }

        char_primary = s.characters[0] if s.characters else s.character
        characters_list = [
            {
                "name": ch.name,
                "action": ch.action,
                "expression": ch.expression,
                "direction": ch.direction,
                "speed": ch.speed,
                "x_offset": ch.x_offset,
                "visual_trait": getattr(ch, "visual_trait", "none") or "none",
                "attachments": getattr(ch, "attachments", {}),
                "skin_tone": getattr(ch, "skin_tone", "fair"),
                "hair_style": getattr(ch, "hair_style", "bald"),
                "hair_color": getattr(ch, "hair_color", "black"),
                "clothing_type": getattr(ch, "clothing_type", "shirt"),
                "clothing_color": getattr(ch, "clothing_color", "white"),
                "face_traits": getattr(ch, "face_traits", []),
                "motion_style": getattr(ch, "motion_style", "combat_idle")
            }
            for ch in s.characters
        ] if s.characters else []

        scenes_data.append({
            "scene_id": s.scene_id,
            "stage": s.stage,
            "badge": s.badge,
            "overlay": s.overlay,
            "accent_color": s.accent_color,
            "background_style": getattr(s, "background_style", "arena_ground"),
            "camera_shake": getattr(s, "camera_shake", 0.0),
            "action": char_primary.action,
            "expression": char_primary.expression,
            "characters": characters_list,
            "prop": prop_data,
            "duration": round(dur, 2),
            "audio_url": audio_rel_url
        })

    story_payload = {
        "title": story_spec.title,
        "aspect_ratio": ratio,
        "accessory": story_spec.accessory,
        "scenes": scenes_data
    }

    # Write both story.json and story.js (for zero-CORS direct file:// loading)
    web_story_json = web_dir / "story.json"
    with open(web_story_json, "w", encoding="utf-8") as f:
        json.dump(story_payload, f, indent=2)

    web_story_js = web_dir / "story.js"
    with open(web_story_js, "w", encoding="utf-8") as f:
        f.write(f"window.STORY_DATA = {json.dumps(story_payload, indent=2)};\n")

    print(f"[OK] Exported interactive web story spec: {web_story_json}")

    if preview:
        index_file = web_dir / "index.html"
        print(f"[*] Opening Live Web Player (1,500+ Lucide vector icons) in browser: {index_file}")
        os.system(f'start "" "{index_file}"')

    # Step 3: Stream frames to FFmpeg to build offline MP4
    rendered_file = await renderer.render_video(story_spec, final_mp4)
    print(f"\n[OK] SUCCESS: Offline MP4 video generated at: {rendered_file}")

    if publish:
        print("\n[*] Multi-Platform Publishing initiated via Publishing_Modules...")
        try:
            from stickman_service.Publishing_Modules.media_publisher_main import run_phase4_publishing
            pub_res = run_phase4_publishing(
                video_path=str(rendered_file),
                title=story_spec.title,
                description=f"{story_spec.title}\n\n#viral #shorts #trending #stickman",
                tags="#viral #shorts #trending #stickman"
            )
            print(f"[OK] Multi-Platform Publishing completed: {pub_res.get('published_count', 0)} platforms published.")
        except Exception as p_err:
            print(f"[!] Publishing error: {p_err}")

    return rendered_file

def main():
    parser = argparse.ArgumentParser(description="AI Stickman Video Generator Service")
    parser.add_argument("--topic", type=str, default=None, help="Topic for the stickman explainer")
    parser.add_argument("--script", type=str, default=None, help="Direct voiceover script text")
    parser.add_argument("--manga", type=str, default=None, help="Path to manga or comic PDF file")
    parser.add_argument("--accessory", type=str, default=None, help="Accessory (straw_hat, headphones, beanie, glasses, crown, headband, tie)")
    parser.add_argument("--ratio", type=str, choices=["9:16", "16:9", "1:1"], default="9:16", help="Aspect ratio (default: 9:16)")
    parser.add_argument("--preview", action="store_true", help="Launch live HTML5 player in browser")
    parser.add_argument("--output", type=str, default=None, help="Output mp4 path")
    parser.add_argument("--api-key", type=str, default=None, help="Google Gemini API Key (optional)")
    parser.add_argument("--publish", action="store_true", help="Automatically broadcast to social media via Publishing_Modules")
    args = parser.parse_args()

    if not args.topic and not args.script and not args.manga:
        parser.error("You must specify either --topic, --script, or --manga.")

    asyncio.run(run_pipeline(
        topic=args.topic,
        script=args.script,
        manga_pdf=args.manga,
        accessory=args.accessory,
        output_path=args.output,
        api_key=args.api_key,
        ratio=args.ratio,
        preview=args.preview,
        publish=args.publish
    ))

if __name__ == "__main__":
    main()
