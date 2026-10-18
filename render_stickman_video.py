import os
import sys
import math
import asyncio
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Set up paths
WORKSPACE = Path("d:/Stickman")
OUTPUT_DIR = WORKSPACE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
FINAL_VIDEO = OUTPUT_DIR / "One_Piece_Pacing_Stickman.mp4"

# Audio script scenes
SCENES = [
    {
        "id": 1,
        "text": "If you started One Piece when it first aired, your newborn child is now old enough to finish college, pay taxes, and still wait for the arc to end.",
        "overlay": "25 YEARS OF EPISODES",
        "badge": "EPISODE 1,120+"
    },
    {
        "id": 2,
        "text": "Every anime fan tells you 'Bro, it gets really good at episode four hundred.' That is not a recommendation; that is a prison sentence.",
        "overlay": "133 HOURS TO GET GOOD?",
        "badge": "PRISON SENTENCE"
    },
    {
        "id": 3,
        "text": "The studio adapts just 0.7 manga chapters per episode. To avoid running out of source material, they mastered the art of stretching a single gasp across four weeks.",
        "overlay": "0.7 CHAPTERS PER EPISODE",
        "badge": "STRETCHED REALITY"
    },
    {
        "id": 4,
        "text": "Psychologists call this the Sunk Cost Fallacy. After investing four hundred hours, quitting feels like admitting defeat. You are not watching anymore, you are protecting your investment.",
        "overlay": "SUNK COST FALLACY",
        "badge": "PSYCHOLOGICAL TRAP"
    },
    {
        "id": 5,
        "text": "And yet, when that one legendary episode finally drops every two years, the internet breaks. Because slow burn pain makes the peak payoff unforgettable.",
        "overlay": "THE PEAK PAYOFF",
        "badge": "INTERNET BROKEN"
    },
    {
        "id": 6,
        "text": "So tell me honestly: is One Piece a generational masterpiece, or the world's most elaborate hostage situation? Put your episode count in the comments.",
        "overlay": "MASTERPIECE OR HOSTAGE?",
        "badge": "DROP YOUR EPISODE 👇"
    }
]

async def generate_audio():
    import edge_tts
    scene_audios = []
    for sc in SCENES:
        audio_file = OUTPUT_DIR / f"scene_{sc['id']}.mp3"
        communicate = edge_tts.Communicate(sc["text"], "en-US-ChristopherNeural", rate="+6%", pitch="+0Hz")
        await communicate.save(str(audio_file))
        
        # Get duration using ffprobe
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
        dur = float(res.stdout.strip())
        sc["audio_path"] = str(audio_file)
        sc["duration"] = dur + 0.6  # Add subtle breathing room
        scene_audios.append(audio_file)
    return scene_audios

def get_font(size):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except:
        try:
            return ImageFont.truetype("calibrib.ttf", size)
        except:
            return ImageFont.load_default()

def get_regular_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return get_font(size)

WIDTH, HEIGHT = 720, 1280
FPS = 25

def draw_header_badges(draw, sc, progress):
    # Top progress bar
    bar_y = 40
    total_bar_w = WIDTH - 80
    draw.rectangle([40, bar_y, 40 + total_bar_w, bar_y + 8], fill=(40, 45, 55))
    draw.rectangle([40, bar_y, 40 + int(total_bar_w * progress), bar_y + 8], fill=(0, 220, 255))
    
    # Title badge
    badge_font = get_font(24)
    badge_text = sc["badge"]
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bx = (WIDTH - bw) // 2
    by = 70
    draw.rounded_rectangle([bx - 16, by - 6, bx + bw + 16, by + bh + 8], radius=10, fill=(255, 45, 85))
    draw.text((bx, by), badge_text, font=badge_font, fill=(255, 255, 255))

    # Bottom main overlay topic
    topic_font = get_font(34)
    topic_text = sc["overlay"]
    tbox = draw.textbbox((0, 0), topic_text, font=topic_font)
    tw, th = tbox[2] - tbox[0], tbox[3] - tbox[1]
    tx = (WIDTH - tw) // 2
    ty = HEIGHT - 150
    draw.rounded_rectangle([tx - 20, ty - 10, tx + tw + 20, ty + th + 12], radius=14, fill=(20, 25, 35), outline=(0, 220, 255), width=2)
    draw.text((tx, ty), topic_text, font=topic_font, fill=(255, 255, 255))

def render_scene_1(t, dur, sc, global_prog):
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 12, 16))
    draw = ImageDraw.Draw(img)
    
    cx, cy = WIDTH // 2, HEIGHT // 2 + 50
    p = t / dur
    
    # TV on the right/center
    tv_x, tv_y = cx + 80, cy - 140
    draw.rectangle([tv_x - 100, tv_y - 70, tv_x + 100, tv_y + 70], outline=(0, 220, 255), width=4, fill=(18, 24, 38))
    draw.line([tv_x - 30, tv_y + 70, tv_x - 50, tv_y + 110], fill=(0, 220, 255), width=4)
    draw.line([tv_x + 30, tv_y + 70, tv_x + 50, tv_y + 110], fill=(0, 220, 255), width=4)
    
    # Episode counter in TV
    ep_num = min(1120, int(1 + (p * 1.5) * 1120))
    ep_font = get_font(36)
    ep_str = f"EP {ep_num}"
    draw.text((tv_x - 65, tv_y - 18), ep_str, font=ep_font, fill=(255, 215, 0))
    
    # Stickman watching TV (sitting on a stool)
    sm_x = cx - 140
    head_y = cy - 80
    # Head
    draw.ellipse([sm_x - 30, head_y - 30, sm_x + 30, head_y + 30], outline=(255, 255, 255), width=4)
    # Face
    draw.ellipse([sm_x + 6, head_y - 8, sm_x + 12, head_y - 2], fill=(255, 255, 255)) # eye
    # Torso
    draw.line([sm_x, head_y + 30, sm_x, head_y + 140], fill=(255, 255, 255), width=4)
    # Legs (seated)
    draw.line([sm_x, head_y + 140, sm_x + 60, head_y + 140], fill=(255, 255, 255), width=4)
    draw.line([sm_x + 60, head_y + 140, sm_x + 60, head_y + 220], fill=(255, 255, 255), width=4)
    # Stool
    draw.line([sm_x - 30, head_y + 150, sm_x + 20, head_y + 150], fill=(120, 120, 140), width=4)
    draw.line([sm_x - 20, head_y + 150, sm_x - 30, head_y + 230], fill=(120, 120, 140), width=3)
    draw.line([sm_x + 10, head_y + 150, sm_x + 20, head_y + 230], fill=(120, 120, 140), width=3)
    
    # Arm holding popcorn
    draw.line([sm_x, head_y + 60, sm_x + 40, head_y + 90], fill=(255, 255, 255), width=4)
    draw.line([sm_x + 40, head_y + 90, sm_x + 30, head_y + 60], fill=(255, 255, 255), width=4)
    # Popcorn bucket
    draw.polygon([(sm_x + 20, head_y + 70), (sm_x + 50, head_y + 70), (sm_x + 45, head_y + 105), (sm_x + 25, head_y + 105)], outline=(255, 45, 85), fill=(255, 255, 255), width=2)

    # After p > 0.4: beard grows, walking cane appears!
    if p > 0.35:
        beard_len = min(130, int((p - 0.35) * 220))
        # Beard
        draw.line([sm_x + 10, head_y + 20, sm_x + 25, head_y + 20 + beard_len], fill=(230, 230, 230), width=6)
        draw.line([sm_x + 5, head_y + 25, sm_x + 15, head_y + 25 + beard_len], fill=(200, 200, 200), width=4)
        # Walking cane
        cane_x = sm_x - 50
        draw.arc([cane_x - 10, head_y + 60, cane_x + 15, head_y + 85], start=180, end=0, fill=(210, 160, 90), width=5)
        draw.line([cane_x + 12, head_y + 72, cane_x + 12, head_y + 230], fill=(210, 160, 90), width=5)

    # Floating year calendar
    cal_y = int(220 + math.sin(t * 3) * 10)
    draw.rectangle([WIDTH // 2 - 120, cal_y, WIDTH // 2 + 120, cal_y + 70], fill=(255, 255, 255), outline=(255, 45, 85), width=3)
    draw.rectangle([WIDTH // 2 - 120, cal_y, WIDTH // 2 + 120, cal_y + 20], fill=(255, 45, 85))
    yr = min(2026, int(1999 + p * 27))
    draw.text((WIDTH // 2 - 55, cal_y + 25), f"YEAR {yr}", font=get_font(26), fill=(10, 12, 16))

    draw_header_badges(draw, sc, global_prog)
    return img

def render_scene_2(t, dur, sc, global_prog):
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 12, 16))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 20
    p = t / dur
    
    # Running treadmill track
    tread_y = cy + 180
    draw.line([80, tread_y, WIDTH - 80, tread_y], fill=(0, 220, 255), width=6)
    offset = int((t * 300) % 60)
    for x in range(80, WIDTH - 80, 60):
        draw.line([x - offset, tread_y, x - offset - 20, tread_y + 25], fill=(0, 220, 255), width=3)
        
    # Moving pillars
    pillar_offset = int((t * 180) % 240)
    for px in range(-100, WIDTH + 200, 240):
        actual_x = px - pillar_offset
        draw.rectangle([actual_x, cy - 250, actual_x + 30, cy + 180], fill=(25, 30, 42))

    # Animated stick figure running
    leg_angle = math.sin(t * 14) * 45
    sm_x = cx - 20
    head_y = cy - 20 + int(math.sin(t * 28) * 8)
    
    # Head
    draw.ellipse([sm_x - 30, head_y - 30, sm_x + 30, head_y + 30], outline=(255, 255, 255), width=4)
    # Stressed eye/sweat
    draw.ellipse([sm_x + 6, head_y - 8, sm_x + 12, head_y - 2], fill=(255, 255, 255))
    draw.line([sm_x + 36, head_y - 20, sm_x + 46, head_y - 12], fill=(0, 220, 255), width=3) # sweat
    # Torso
    draw.line([sm_x, head_y + 30, sm_x - 15, head_y + 120], fill=(255, 255, 255), width=4)
    # Legs running
    hip_x, hip_y = sm_x - 15, head_y + 120
    # Left leg
    l_rad = math.radians(leg_angle)
    knee_lx = hip_x + math.sin(l_rad) * 40
    knee_ly = hip_y + math.cos(l_rad) * 40
    draw.line([hip_x, hip_y, knee_lx, knee_ly], fill=(255, 255, 255), width=4)
    draw.line([knee_lx, knee_ly, knee_lx + 20, knee_ly + 35], fill=(255, 255, 255), width=4)
    # Right leg
    r_rad = math.radians(-leg_angle)
    knee_rx = hip_x + math.sin(r_rad) * 40
    knee_ry = hip_y + math.cos(r_rad) * 40
    draw.line([hip_x, hip_y, knee_rx, knee_ry], fill=(255, 255, 255), width=4)
    draw.line([knee_rx, knee_ry, knee_rx - 20, knee_ry + 35], fill=(255, 255, 255), width=4)
    # Arms pumping
    draw.line([sm_x - 5, head_y + 50, sm_x + math.cos(l_rad) * 40, head_y + 70 + math.sin(l_rad) * 30], fill=(255, 255, 255), width=4)
    draw.line([sm_x - 5, head_y + 50, sm_x - math.cos(l_rad) * 40, head_y + 70 - math.sin(l_rad) * 30], fill=(255, 255, 255), width=4)

    # Episode Breakdown Stack above
    bx, by = 100, cy - 230
    bw = WIDTH - 200
    draw.rectangle([bx, by, bx + bw, by + 40], fill=(255, 45, 85)) # 6m recap
    draw.text((bx + 20, by + 8), "6 MIN RECAP & INTRO", font=get_font(20), fill=(255, 255, 255))
    
    draw.rectangle([bx, by + 45, bx + bw, by + 85], fill=(255, 120, 40)) # 5m running
    draw.text((bx + 20, by + 53), "5 MIN HALLWAY RUNNING", font=get_font(20), fill=(255, 255, 255))

    draw.rectangle([bx, by + 90, bx + bw, by + 130], fill=(200, 30, 80)) # 4m reactions
    draw.text((bx + 20, by + 98), "4 MIN GASPING REACTIONS", font=get_font(20), fill=(255, 255, 255))

    draw.rectangle([bx, by + 135, bx + bw, by + 175], fill=(0, 220, 255)) # 2m actual plot
    draw.text((bx + 20, by + 143), "2 MIN ACTUAL PLOT!", font=get_font(20), fill=(10, 12, 16))

    draw_header_badges(draw, sc, global_prog)
    return img

def render_scene_3(t, dur, sc, global_prog):
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 12, 16))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2
    p = t / dur

    # Giant hydraulic stamping press
    press_cycle = (math.sin(t * 5) + 1) / 2
    press_y = int(220 + press_cycle * 140)
    
    # Hydraulic cylinder
    draw.rectangle([cx - 40, 120, cx + 40, press_y], fill=(90, 105, 130))
    # Stamp head
    draw.rectangle([cx - 160, press_y, cx + 160, press_y + 45], fill=(200, 215, 235), outline=(0, 220, 255), width=3)
    draw.text((cx - 85, press_y + 10), "STUDIO PRESS", font=get_font(22), fill=(10, 12, 16))

    # Anvil base
    draw.rectangle([cx - 180, 450, cx + 180, 500], fill=(45, 55, 75))

    # Manga page being squashed
    squash_h = max(6, int(60 * (1 - press_cycle * 0.85)))
    draw.rectangle([cx - 90, 450 - squash_h, cx + 90, 450], fill=(255, 255, 255), outline=(255, 215, 0), width=2)
    draw.text((cx - 80, 450 - squash_h + 2), "MANGA CHAPTER (0.7)", font=get_font(14), fill=(10, 12, 16))

    # Conveyor belt stretching down
    draw.line([100, 680, WIDTH - 100, 680], fill=(0, 220, 255), width=5)
    
    # 3 Anime film reels popping out
    for i, rx in enumerate([180, 360, 540]):
        angle = (t * 200 + i * 45) % 360
        draw.ellipse([rx - 45, 680 - 95, rx + 45, 680 - 5], outline=(255, 215, 0), width=4, fill=(30, 35, 50))
        draw.ellipse([rx - 15, 680 - 65, rx + 15, 680 - 35], fill=(255, 215, 0))
        draw.line([rx - 40, 680 - 50, rx + 40, 680 - 50], fill=(255, 215, 0), width=2)
        draw.line([rx, 680 - 90, rx, 680 - 10], fill=(255, 215, 0), width=2)

    # Stick figure observing with arms crossed
    sm_x = 120
    head_y = 850
    draw.ellipse([sm_x - 30, head_y - 30, sm_x + 30, head_y + 30], outline=(255, 255, 255), width=4)
    draw.line([sm_x, head_y + 30, sm_x, head_y + 140], fill=(255, 255, 255), width=4)
    # Legs
    draw.line([sm_x, head_y + 140, sm_x - 25, head_y + 240], fill=(255, 255, 255), width=4)
    draw.line([sm_x, head_y + 140, sm_x + 25, head_y + 240], fill=(255, 255, 255), width=4)
    # Arms crossed
    draw.line([sm_x, head_y + 60, sm_x + 35, head_y + 80], fill=(255, 255, 255), width=4)
    draw.line([sm_x + 35, head_y + 80, sm_x - 10, head_y + 85], fill=(255, 255, 255), width=4)
    draw.line([sm_x, head_y + 60, sm_x - 30, head_y + 80], fill=(255, 255, 255), width=4)

    # Cash flying around
    for i in range(5):
        cx_coin = 350 + int(math.sin(t * 3 + i) * 150)
        cy_coin = int(780 + ((t * 80 + i * 40) % 200))
        draw.ellipse([cx_coin - 14, cy_coin - 14, cx_coin + 14, cy_coin + 14], fill=(255, 215, 0), outline=(255, 255, 255), width=2)
        draw.text((cx_coin - 5, cy_coin - 9), "$", font=get_font(16), fill=(10, 12, 16))

    draw_header_badges(draw, sc, global_prog)
    return img

def render_scene_4(t, dur, sc, global_prog):
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 12, 16))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2
    p = t / dur

    # Deep pit walls
    draw.polygon([(0, 200), (140, 880), (0, 880)], fill=(25, 30, 42))
    draw.polygon([(WIDTH, 200), (WIDTH - 140, 880), (WIDTH, 880)], fill=(25, 30, 42))
    draw.line([140, 880, WIDTH - 140, 880], fill=(0, 220, 255), width=4)

    # Piles of episode boxes at bottom
    for i in range(7):
        bx = 160 + i * 55
        by = 840 - (i % 3) * 35
        draw.rectangle([bx, by, bx + 45, by + 35], fill=(35, 45, 65), outline=(0, 220, 255), width=2)
        draw.text((bx + 5, by + 8), f"EP{i*150}", font=get_font(12), fill=(255, 255, 255))

    # Golden Trophy dangling above
    trophy_y = int(320 + math.sin(t * 3) * 12)
    draw.line([cx, 150, cx, trophy_y], fill=(255, 215, 0), width=3) # rope
    # Trophy cup
    draw.polygon([(cx - 35, trophy_y), (cx + 35, trophy_y), (cx + 20, trophy_y + 40), (cx - 20, trophy_y + 40)], fill=(255, 215, 0))
    draw.rectangle([cx - 8, trophy_y + 40, cx + 8, trophy_y + 60], fill=(255, 215, 0))
    draw.rectangle([cx - 25, trophy_y + 60, cx + 25, trophy_y + 72], fill=(255, 215, 0))
    draw.text((cx - 60, trophy_y - 35), "THE ONE PIECE", font=get_font(18), fill=(255, 215, 0))

    # Stick figure trapped at bottom
    sm_x = cx + int(math.sin(t * 4) * 30)
    head_y = 660
    draw.ellipse([sm_x - 30, head_y - 30, sm_x + 30, head_y + 30], outline=(255, 255, 255), width=4)
    # Looking up
    draw.ellipse([sm_x - 4, head_y - 20, sm_x + 4, head_y - 12], fill=(255, 255, 255))
    draw.line([sm_x, head_y + 30, sm_x, head_y + 130], fill=(255, 255, 255), width=4)
    draw.line([sm_x, head_y + 130, sm_x - 25, head_y + 210], fill=(255, 255, 255), width=4)
    draw.line([sm_x, head_y + 130, sm_x + 25, head_y + 210], fill=(255, 255, 255), width=4)
    # Reaching up
    draw.line([sm_x, head_y + 50, sm_x - 30, head_y - 10], fill=(255, 255, 255), width=4)
    draw.line([sm_x, head_y + 50, sm_x + 30, head_y - 10], fill=(255, 255, 255), width=4)

    # Cyan glowing chain around waist
    draw.line([sm_x, head_y + 130, 140, 840], fill=(0, 220, 255), width=4)
    draw.text((sm_x - 70, head_y + 145), "500 HOURS TRAP", font=get_font(16), fill=(0, 220, 255))

    draw_header_badges(draw, sc, global_prog)
    return img

def render_scene_5(t, dur, sc, global_prog):
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 12, 16))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2
    p = t / dur

    # Epic radial speed lines
    for deg in range(0, 360, 15):
        rad = math.radians(deg + t * 40)
        x1 = cx + math.cos(rad) * 120
        y1 = cy + math.sin(rad) * 120
        x2 = cx + math.cos(rad) * 600
        y2 = cy + math.sin(rad) * 600
        col = (255, 215, 0) if deg % 30 == 0 else (255, 255, 255)
        draw.line([x1, y1, x2, y2], fill=col, width=3)

    # Pirate Straw Hat Skull banner on top
    draw.ellipse([cx - 45, 260, cx + 45, 330], outline=(255, 255, 255), width=4, fill=(10, 12, 16))
    # Straw hat brim
    draw.line([cx - 75, 275, cx + 75, 275], fill=(255, 215, 0), width=6)
    draw.arc([cx - 40, 235, cx + 40, 280], start=180, end=0, fill=(255, 215, 0), width=6)
    # Red ribbon
    draw.line([cx - 36, 273, cx + 36, 273], fill=(255, 45, 85), width=4)
    # Crossbones
    draw.line([cx - 65, 240, cx + 65, 350], fill=(255, 255, 255), width=4)
    draw.line([cx + 65, 240, cx - 65, 350], fill=(255, 255, 255), width=4)

    # Stick figure in epic Gear 5 / Victory Pose
    head_y = cy + 20
    draw.ellipse([cx - 35, head_y - 35, cx + 35, head_y + 35], outline=(255, 255, 255), width=5, fill=(10, 12, 16))
    # Big grin
    draw.arc([cx - 20, head_y - 15, cx + 20, head_y + 20], start=0, end=180, fill=(255, 255, 255), width=4)
    # Torso
    draw.line([cx, head_y + 35, cx, head_y + 150], fill=(255, 255, 255), width=5)
    # Arms in celebratory V
    draw.line([cx, head_y + 60, cx - 70, head_y - 20], fill=(255, 255, 255), width=5)
    draw.line([cx, head_y + 60, cx + 70, head_y - 20], fill=(255, 255, 255), width=5)
    # Legs planted wide
    draw.line([cx, head_y + 150, cx - 60, head_y + 260], fill=(255, 255, 255), width=5)
    draw.line([cx, head_y + 150, cx + 60, head_y + 260], fill=(255, 255, 255), width=5)

    # Shockwave circles
    wave_r = int((t * 220) % 250) + 40
    draw.ellipse([cx - wave_r, cy - wave_r + 40, cx + wave_r, cy + wave_r + 40], outline=(255, 215, 0), width=3)

    draw_header_badges(draw, sc, global_prog)
    return img

def render_scene_6(t, dur, sc, global_prog):
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 12, 16))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 50
    p = t / dur

    # Two branching paths
    draw.polygon([(cx - 10, 220), (cx + 10, 220), (WIDTH - 60, 750), (WIDTH - 160, 750)], fill=(35, 20, 30), outline=(255, 45, 85), width=3)
    draw.polygon([(cx - 10, 220), (cx + 10, 220), (160, 750), (60, 750)], fill=(20, 35, 40), outline=(0, 220, 255), width=3)

    # Path Labels
    draw.text((90, 480), "PEAK\nFICTION", font=get_font(26), fill=(0, 220, 255))
    draw.text((WIDTH - 210, 480), "HOSTAGE\nSITUATION", font=get_font(24), fill=(255, 45, 85))

    # Stick figure in foreground pointing directly at camera
    head_y = 660
    draw.ellipse([cx - 40, head_y - 40, cx + 40, head_y + 40], outline=(255, 255, 255), width=5, fill=(10, 12, 16))
    # Smug expression
    draw.line([cx - 18, head_y - 10, cx - 6, head_y - 12], fill=(255, 255, 255), width=3)
    draw.line([cx + 6, head_y - 12, cx + 18, head_y - 10], fill=(255, 255, 255), width=3)
    draw.arc([cx - 15, head_y, cx + 15, head_y + 22], start=0, end=180, fill=(255, 255, 255), width=3)
    # Body
    draw.line([cx, head_y + 40, cx, head_y + 170], fill=(255, 255, 255), width=5)
    # Left hand on hip
    draw.line([cx, head_y + 70, cx - 55, head_y + 110], fill=(255, 255, 255), width=5)
    draw.line([cx - 55, head_y + 110, cx - 10, head_y + 140], fill=(255, 255, 255), width=5)
    # Right arm pointing straight at viewer
    draw.line([cx, head_y + 70, cx + 30, head_y + 90], fill=(255, 255, 255), width=6)
    draw.ellipse([cx + 25, head_y + 85, cx + 55, head_y + 115], fill=(255, 255, 255)) # hand circle
    draw.line([cx + 40, head_y + 85, cx + 40, head_y + 60], fill=(255, 255, 255), width=6) # pointing finger
    # Legs
    draw.line([cx, head_y + 170, cx - 40, head_y + 290], fill=(255, 255, 255), width=5)
    draw.line([cx, head_y + 170, cx + 40, head_y + 290], fill=(255, 255, 255), width=5)

    # Comment prompt box floating in top center
    pulse = int(math.sin(t * 6) * 6)
    draw.rounded_rectangle([cx - 170, 180 + pulse, cx + 170, 260 + pulse], radius=15, fill=(255, 215, 0), outline=(255, 255, 255), width=3)
    draw.text((cx - 145, 202 + pulse), "WHAT EPISODE ARE YOU ON?", font=get_font(18), fill=(10, 12, 16))

    draw_header_badges(draw, sc, global_prog)
    return img

SCENE_RENDERERS = {
    1: render_scene_1,
    2: render_scene_2,
    3: render_scene_3,
    4: render_scene_4,
    5: render_scene_5,
    6: render_scene_6
}

async def main():
    print("Step 1: Generating studio quality voiceover with Edge-TTS...")
    await generate_audio()

    total_duration = sum(sc["duration"] for sc in SCENES)
    total_frames = int(total_duration * FPS)
    print(f"Total video duration: {total_duration:.2f}s ({total_frames} frames @ {FPS} FPS)")

    # Combine audio scenes into master audio
    concat_list_file = OUTPUT_DIR / "concat_audio.txt"
    with open(concat_list_file, "w") as f:
        for sc in SCENES:
            f.write(f"file '{Path(sc['audio_path']).name}'\n")
            
    master_voice_mp3 = OUTPUT_DIR / "master_voice.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list_file), "-c", "copy", str(master_voice_mp3)
    ], check=True)

    # Generate background music rhythm (using ffmpeg audio synthesis for punchy lo-fi beat)
    # A subtle bass-line + ticking hi-hat synth
    bgm_file = OUTPUT_DIR / "bgm.mp3"
    synth_cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"sine=frequency=110:duration={total_duration}[b];sine=frequency=440:duration={total_duration}[h];[b]volume=0.15[vb];[h]volume=0.03[vh];[vb][vh]amix=inputs=2",
        "-c:a", "libmp3lame", str(bgm_file)
    ]
    subprocess.run(synth_cmd, check=True)

    # Mix master voice + subtle bgm
    final_audio = OUTPUT_DIR / "final_soundtrack.mp3"
    mix_cmd = [
        "ffmpeg", "-y", "-i", str(master_voice_mp3), "-i", str(bgm_file),
        "-filter_complex", "[0:a]volume=1.0[v0];[1:a]volume=0.25[v1];[v0][v1]amix=inputs=2:duration=first",
        "-c:a", "libmp3lame", str(final_audio)
    ]
    subprocess.run(mix_cmd, check=True)

    print("Step 2: Rendering animation frames and encoding video with FFmpeg...")
    ffmpeg_proc = subprocess.Popen([
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",  # stdin pipe
        "-i", str(final_audio),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(FINAL_VIDEO)
    ], stdin=subprocess.PIPE)

    cur_time = 0.0
    for sc in SCENES:
        dur = sc["duration"]
        frames_in_scene = int(dur * FPS)
        renderer = SCENE_RENDERERS[sc["id"]]
        print(f"  Rendering Scene {sc['id']}: {sc['overlay']} ({dur:.1f}s)...")
        
        for f in range(frames_in_scene):
            t = f / FPS
            global_p = min(1.0, (cur_time + t) / total_duration)
            frame_img = renderer(t, dur, sc, global_p)
            ffmpeg_proc.stdin.write(frame_img.tobytes())
            
        cur_time += dur

    ffmpeg_proc.stdin.close()
    ffmpeg_proc.wait()

    if ffmpeg_proc.returncode == 0:
        print(f"\nSUCCESS! Animated video rendered at:\n{FINAL_VIDEO}")
    else:
        print("Rendering encountered an error.")

if __name__ == "__main__":
    asyncio.run(main())
