"""
main.py — Master Stickman AI Studio & Telegram Bot Controller
=============================================================
Purpose:
  - Interactive Telegram Bot UI for Stickman Explainer Video Generation
  - Mode Selection:
      1. 💡 Topic Generation (Gemini crafts 6-stage script & directs visual stickman video)
      2. 📝 Script Direction (Direct user voiceover script — Gemini handles acting, props, timing)
      3. 📖 Manga / Comic PDF (Extracts pages via PyMuPDF, analyzes chapter, creates viral anime recap)
  - Interactive UI Controls:
      • 📐 Aspect Ratio Selector (9:16 Vertical, 16:9 Widescreen, 1:1 Square)
      • 👒 Character Accessory Selector (Straw Hat, Headphones, Beanie, Glasses, Crown, Headband, Tie)
  - Telegram 4-Button Approval Suite:
      • [✅ Approve & Set Title]  callback_data="approve_title_<session_id>"
      • [🚀 Post / Save Video]   callback_data="approve_post_<session_id>"
      • [🛠️ Re-Edit / Tweak]      callback_data="reedit_<session_id>"
      • [🗑️ Reject & Discard]     callback_data="reject_<session_id>"
"""

import os
import sys
import time
import json
import uuid
import signal
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Instant Ctrl+C Termination Handler
def _instant_sigint_handler(signum, frame):
    print("\n🛑 [INSTANT EXIT] Ctrl+C detected. Terminating process immediately...", flush=True)
    os._exit(130)

try:
    signal.signal(signal.SIGINT, _instant_sigint_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _instant_sigint_handler)
except Exception:
    pass

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Load .env file
_env_file = _REPO_ROOT / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

# ── Logging & Polling Filter Setup ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("stickman_telegram_bot")

class PollingFilter(logging.Filter):
    def filter(self, record):
        return "getUpdates" not in record.getMessage()

for lib in ["httpx", "telegram", "telegram.ext", "httpcore"]:
    l = logging.getLogger(lib)
    l.setLevel(logging.WARNING)
    l.addFilter(PollingFilter())

# ── Session & State Management ───────────────────────────────────────────────
user_state: Dict[int, Dict[str, Any]] = {}
video_sessions: Dict[str, Dict[str, Any]] = {}

ACCESSORY_ICONS = {
    "auto": "⚡ Auto (Topic-Based)",
    "straw_hat": "👒 Straw Hat (One Piece / Luffy)",
    "headphones": "🎧 Headphones (Podcaster / Tech)",
    "red_beanie": "🧢 Red Beanie (Urban / Indie)",
    "glasses": "👓 Glasses (Coding / Science / Nerd)",
    "crown": "👑 Crown (Success / Wealth / King)",
    "headband": "🥋 Headband (Anime / Ninja)",
    "tie": "👔 Business Tie (Finance / Corporate)",
    "none": "⚪ Minimalist Stickman"
}

def get_user_config(chat_id: int) -> Dict[str, Any]:
    if chat_id not in user_state:
        user_state[chat_id] = {
            "mode": "idle",
            "ratio": "9:16",
            "accessory": "auto",
            "active_session": None
        }
    return user_state[chat_id]


# ── MTProto Client & Large File Downloader (Bypasses 20MB Bot API Limit) ──────
_pyro_client = None
_pyro_lock = asyncio.Lock()

async def get_mtproto_client():
    """
    Initializes and caches a Pyrogram MTProto bot client.
    Handles clock skew with Telegram servers automatically.
    Supports downloading files up to 2GB.
    """
    global _pyro_client
    async with _pyro_lock:
        if _pyro_client is not None and getattr(_pyro_client, "is_connected", False):
            return _pyro_client

        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

        if not api_id or not api_hash or not bot_token:
            return None

        # Synchronize time with Telegram server to avoid BadMsgNotification [17]
        try:
            import urllib.request
            import email.utils
            from pyrogram.session.internals import msg_id

            server_date = urllib.request.urlopen("https://api.telegram.org", timeout=5).headers.get("Date")
            if server_date:
                server_ts = email.utils.parsedate_to_datetime(server_date).timestamp()
                time_offset = server_ts - time.time()
                def calibrated_msg_id(cls):
                    now = int(time.time() + time_offset)
                    cls.offset = (cls.offset + 4) if now == cls.last_time else 0
                    m_id = (now * 2 ** 32) + cls.offset
                    cls.last_time = now
                    return m_id
                msg_id.MsgId.__new__ = calibrated_msg_id
                logger.info(f"Synchronized MTProto clock offset with Telegram: {time_offset:+.2f}s")
        except Exception as e:
            logger.warning(f"Could not calibrate time offset: {e}")

        try:
            from pyrogram import Client
            session_dir = _REPO_ROOT / "temp" / "sessions"
            session_dir.mkdir(parents=True, exist_ok=True)
            _pyro_client = Client(
                name="stickman_mtproto",
                api_id=int(api_id),
                api_hash=api_hash,
                bot_token=bot_token,
                workdir=str(session_dir),
                in_memory=True
            )
            await _pyro_client.start()
            logger.info("✅ Pyrogram MTProto Client connected successfully (supports files up to 2GB).")
            return _pyro_client
        except Exception as e:
            logger.error(f"❌ Failed to start Pyrogram MTProto Client: {e}")
            return None

async def download_telegram_document(doc, msg, destination_path: Path, status_msg=None) -> Path:
    """
    Downloads document using standard Bot API if under 20MB.
    Automatically switches to MTProto (Pyrogram) if file is >=20MB or Bot API fails.
    """
    file_size = getattr(doc, "file_size", 0) or 0
    file_size_mb = file_size / (1024 * 1024)
    use_mtproto = file_size_mb >= 19.5

    if not use_mtproto:
        try:
            tg_file = await doc.get_file()
            await tg_file.download_to_drive(custom_path=str(destination_path))
            return destination_path
        except Exception as e:
            if "File is too big" in str(e):
                logger.info("Bot API reported file is too big; switching to MTProto.")
                use_mtproto = True
            else:
                raise e

    if use_mtproto:
        if status_msg:
            try:
                await status_msg.edit_text(
                    f"📥 **Large File Detected ({file_size_mb:.1f} MB)**\n\n"
                    f"🚀 Downloading via Telegram MTProto engine (bypassing 20MB limit)..."
                )
            except Exception:
                pass

        pyro = await get_mtproto_client()
        if not pyro:
            raise RuntimeError(
                "File exceeds Telegram Bot API 20MB limit, and MTProto credentials "
                "(TELEGRAM_API_ID / TELEGRAM_API_HASH) are not configured."
            )

        pyro_msg = await pyro.get_messages(chat_id=msg.chat.id, message_ids=msg.message_id)
        downloaded = await pyro.download_media(pyro_msg, file_name=str(destination_path))
        if downloaded and Path(downloaded).exists():
            return Path(downloaded)
        raise RuntimeError(f"Pyrogram MTProto download failed for: {destination_path}")


# ── Keyboards Builder ────────────────────────────────────────────────────────

def build_main_menu_keyboard(chat_id: int):
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        cfg = get_user_config(chat_id)
        ratio = cfg.get("ratio", "9:16")
        acc = cfg.get("accessory", "auto")
        acc_label = ACCESSORY_ICONS.get(acc, acc)

        ratio_badge = "📱 9:16 (Shorts)" if ratio == "9:16" else ("🖥️ 16:9 (Wide)" if ratio == "16:9" else "⏹️ 1:1 (Square)")

        keyboard = [
            [
                InlineKeyboardButton(f"📐 Ratio: {ratio_badge}", callback_data="menu_toggle_ratio")
            ],
            [
                InlineKeyboardButton("💡 Generate from Topic", callback_data="menu_topic"),
                InlineKeyboardButton("📝 Generate from Script", callback_data="menu_script")
            ],
            [
                InlineKeyboardButton("📖 Direct Manga / Comic PDF", callback_data="menu_manga")
            ],
            [
                InlineKeyboardButton(f"🎭 Accessory: {acc_label}", callback_data="menu_accessory")
            ],
            [
                InlineKeyboardButton("🌐 Open HTML5 Live Studio", callback_data="menu_open_studio")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    except ImportError:
        return None

def build_accessory_keyboard():
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("⚡ Auto (Topic Detection)", callback_data="acc_auto")],
            [InlineKeyboardButton("👒 Straw Hat (One Piece)", callback_data="acc_straw_hat"),
             InlineKeyboardButton("🎧 Headphones (Tech/Podcasts)", callback_data="acc_headphones")],
            [InlineKeyboardButton("🧢 Red Beanie (Street/Indie)", callback_data="acc_red_beanie"),
             InlineKeyboardButton("👓 Glasses (Code/Science)", callback_data="acc_glasses")],
            [InlineKeyboardButton("👑 Crown (Royalty/Wealth)", callback_data="acc_crown"),
             InlineKeyboardButton("🥋 Headband (Anime/Ninja)", callback_data="acc_headband")],
            [InlineKeyboardButton("👔 Tie (Corporate/Business)", callback_data="acc_tie"),
             InlineKeyboardButton("⚪ Minimalist (None)", callback_data="acc_none")],
            [InlineKeyboardButton("↩️ Back to Main Menu", callback_data="menu_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    except ImportError:
        return None

def build_telegram_session_keyboard(session_id: str):
    """
    Builds the 4-Button Approval Suite:
      - [✅ Approve & Set Title]
      - [🚀 Post / Save Video]
      - [🛠️ Re-Edit / Tweak]
      - [🗑️ Reject & Discard]
    """
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve & Set Title", callback_data=f"approve_title_{session_id}"),
                InlineKeyboardButton("🚀 Post / Save Video", callback_data=f"approve_post_{session_id}"),
            ],
            [
                InlineKeyboardButton("🛠️ Re-Edit / Tweak", callback_data=f"reedit_{session_id}"),
                InlineKeyboardButton("🗑️ Reject & Discard", callback_data=f"reject_{session_id}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    except ImportError:
        return None

def build_reedit_keyboard(session_id: str):
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("👒 Switch to Straw Hat", callback_data=f"re_acc_straw_hat_{session_id}"),
             InlineKeyboardButton("🎧 Switch to Headphones", callback_data=f"re_acc_headphones_{session_id}")],
            [InlineKeyboardButton("👑 Switch to Crown", callback_data=f"re_acc_crown_{session_id}"),
             InlineKeyboardButton("👓 Switch to Glasses", callback_data=f"re_acc_glasses_{session_id}")],
            [InlineKeyboardButton("🔄 Re-generate Narrative Beat", callback_data=f"re_regen_{session_id}")],
            [InlineKeyboardButton("↩️ Cancel", callback_data=f"re_cancel_{session_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    except ImportError:
        return None

# ── Video Generation Dispatcher ──────────────────────────────────────────────

def dispatch_stickman_generation(chat_id: int, bot, topic: str = None, script: str = None, manga_pdf: str = None, accessory: str = "auto", ratio: str = "9:16"):
    """
    Runs the stickman pipeline in a non-blocking background thread
    and delivers the finished MP4 video + 4-button review card directly to Telegram.
    """
    session_id = str(uuid.uuid4())[:8]

    # Capture main application event loop where the Telegram Bot and httpx client live
    try:
        main_loop = asyncio.get_running_loop()
    except RuntimeError:
        main_loop = None

    def _worker():
        from stickman_service.pipeline import run_pipeline
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Output video file
        out_dir = _REPO_ROOT / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = "".join(c if c.isalnum() else "_" for c in (topic or "script" or "manga").lower())[:24].strip("_")
        out_mp4 = out_dir / f"{slug}_{session_id}_{ratio.replace(':', '_')}.mp4"

        acc_arg = accessory if accessory != "auto" else None

        try:
            rendered_path = loop.run_until_complete(run_pipeline(
                topic=topic,
                script=script,
                manga_pdf=manga_pdf,
                accessory=acc_arg,
                output_path=str(out_mp4),
                ratio=ratio,
                preview=False
            ))

            video_sessions[session_id] = {
                "session_id": session_id,
                "video_path": str(rendered_path),
                "chat_id": chat_id,
                "topic": topic or "Script Explainer",
                "title": topic or "Stickman Explainer",
                "ratio": ratio,
                "accessory": accessory
            }

            async def _send_video():
                keyboard = build_telegram_session_keyboard(session_id)
                with open(rendered_path, "rb") as vf:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=vf,
                        caption=(
                            f"🎬 **Stickman Video Ready!**\n\n"
                            f"📌 **Topic/Title**: `{topic or 'Custom Script'}`\n"
                            f"📐 **Ratio**: `{ratio}`\n"
                            f"🆔 `Session: {session_id}`\n\n"
                            f"👇 **Review and select an action:**"
                        ),
                        reply_markup=keyboard,
                        read_timeout=300,
                        write_timeout=300
                    )

            if main_loop and main_loop.is_running():
                fut = asyncio.run_coroutine_threadsafe(_send_video(), main_loop)
                fut.result(timeout=180)
            else:
                loop.run_until_complete(_send_video())

        except Exception as err:
            logger.error(f"Error rendering stickman video: {err}", exc_info=True)
            async def _send_err():
                try:
                    await bot.send_message(chat_id=chat_id, text=f"❌ **Video Generation Failed**: `{err}`")
                except Exception:
                    pass
            if main_loop and main_loop.is_running():
                asyncio.run_coroutine_threadsafe(_send_err(), main_loop)
            else:
                try:
                    loop.run_until_complete(_send_err())
                except Exception:
                    pass
        finally:
            try:
                loop.close()
            except Exception:
                pass

    import threading
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def dispatch_publishing(chat_id: int, bot, session_id: str):
    """
    Asynchronously broadcasts an approved stickman reel across configured platforms
    (YouTube Shorts, Meta Instagram/Facebook, TikTok, and Public Telegram Channel)
    via Publishing_Modules, sending live progress and links back to the user.
    """
    sess = video_sessions.get(session_id)
    if not sess:
        return

    video_path = sess.get("video_path")
    title = sess.get("title") or sess.get("topic") or "Stickman Explainer"
    tags = "#viral #shorts #stickman #animation #trending"

    try:
        main_loop = asyncio.get_running_loop()
    except RuntimeError:
        main_loop = None

    def _pub_worker():
        try:
            from stickman_service.Publishing_Modules.media_publisher_main import run_phase4_publishing
            results = run_phase4_publishing(
                video_path=video_path,
                title=title,
                description=f"{title}\n\n{tags}",
                tags=tags,
                user_id=str(chat_id)
            )

            lines = [
                f"🚀 **Multi-Platform Publishing Report:**",
                f"📌 **Title**: `{title}`\n"
            ]
            for p_name, p_data in results.get("platforms", {}).items():
                st = p_data.get("status", "unknown")
                if st == "success":
                    link = p_data.get("url") or p_data.get("link") or "Published"
                    lines.append(f"✅ **{p_name.upper()}**: [View Live Post]({link})" if str(link).startswith("http") else f"✅ **{p_name.upper()}**: {link}")
                elif st == "skipped":
                    reason = p_data.get("message") or "Credentials not configured in .env"
                    lines.append(f"⏭️ **{p_name.upper()}**: Skipped ({reason})")
                else:
                    err = p_data.get("error") or p_data.get("message") or "Upload error"
                    lines.append(f"❌ **{p_name.upper()}**: Failed ({err})")

            pub_count = results.get("published_count", 0)
            lines.append(f"\n🎉 Successfully published to {pub_count} platform(s)!")
            report_text = "\n".join(lines)

            async def _send_report():
                await bot.send_message(
                    chat_id=chat_id,
                    text=report_text,
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )

            if main_loop and main_loop.is_running():
                asyncio.run_coroutine_threadsafe(_send_report(), main_loop)
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_send_report())
                loop.close()

        except Exception as err:
            logger.error(f"Error publishing video: {err}", exc_info=True)
            async def _send_pub_err():
                await bot.send_message(chat_id=chat_id, text=f"❌ **Publishing Workflow Failed**: `{err}`")

            if main_loop and main_loop.is_running():
                asyncio.run_coroutine_threadsafe(_send_pub_err(), main_loop)
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_send_pub_err())
                loop.close()

    import threading
    t = threading.Thread(target=_pub_worker, daemon=True)
    t.start()


# ── Telegram Handlers ────────────────────────────────────────────────────────

async def handle_start(update, context):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    cfg = get_user_config(chat_id)
    cfg["mode"] = "idle"

    keyboard = build_main_menu_keyboard(chat_id)
    await msg.reply_text(
        "⚡ **Welcome to the AI Stickman Video Studio!**\n\n"
        "Direct viral stickman explainers with deterministic kinematics, "
        "Luffy's Straw Hat & modular accessories, and all 1,500+ Lucide vector props.\n\n"
        "👇 **Choose your generation mode or adjust settings below:**",
        reply_markup=keyboard
    )

async def handle_callback(update, context):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data
    chat_id = update.effective_chat.id
    cfg = get_user_config(chat_id)

    # 1. Main Menu
    if data == "menu_main":
        cfg["mode"] = "idle"
        keyboard = build_main_menu_keyboard(chat_id)
        await query.edit_message_text(
            "⚡ **AI Stickman Video Studio — Main Menu**\n\n👇 **Select an option:**",
            reply_markup=keyboard
        )
        return

    # 2. Toggle Ratio
    if data == "menu_toggle_ratio":
        curr = cfg.get("ratio", "9:16")
        next_ratio = "16:9" if curr == "9:16" else ("1:1" if curr == "16:9" else "9:16")
        cfg["ratio"] = next_ratio
        keyboard = build_main_menu_keyboard(chat_id)
        await query.edit_message_text(
            f"✅ **Aspect ratio updated to `{next_ratio}`!**\n\n👇 **Choose what you want to create:**",
            reply_markup=keyboard
        )
        return

    # 3. Topic Mode
    if data == "menu_topic":
        cfg["mode"] = "waiting_topic"
        await query.edit_message_text(
            "💡 **Mode: Generate from Topic**\n\n"
            "Please send the topic for your stickman video.\n\n"
            "📌 *Examples:*\n"
            "• `Why Coffee Stops Working`\n"
            "• `One Piece Pacing Truth`\n"
            "• `The Psychology of Sunk Cost`\n"
            "• `Why Procrastination is Not Laziness`\n\n"
            "Send your topic now 👇"
        )
        return

    # 4. Script Mode
    if data == "menu_script":
        cfg["mode"] = "waiting_script"
        await query.edit_message_text(
            "📝 **Mode: Generate from Script**\n\n"
            "*(This makes Gemini significantly more comfortable by eliminating hallucinated copy!)*\n\n"
            "Paste your complete voiceover script or article below.\n"
            "Gemini will choreograph the 6 stages, body language, Lucide props, and accent colors to match your exact words.\n\n"
            "Send your script now 👇"
        )
        return

    # 5. Manga / Comic PDF Mode
    if data == "menu_manga":
        cfg["mode"] = "waiting_manga_pdf"
        await query.edit_message_text(
            "📖 **Mode: Direct Manga / Comic PDF**\n\n"
            "Please **upload a manga chapter PDF** (or CBZ file) as an attachment.\n\n"
            "⚡ **How it works:**\n"
            "1. PyMuPDF extracts the pages instantly at high DPI\n"
            "2. Gemini Vision reads the chapter action and dialog\n"
            "3. The Stickman Engine generates an anime recap video with the Straw Hat / Headband!\n\n"
            "Upload your PDF file now 👇"
        )
        return

    # 6. Accessory Menu
    if data == "menu_accessory":
        keyboard = build_accessory_keyboard()
        await query.edit_message_text(
            "🎭 **Choose Character Accessory / Recognition Item:**\n\n"
            "Select an iconic item for your stickman character:",
            reply_markup=keyboard
        )
        return

    if data.startswith("acc_"):
        chosen_acc = data.replace("acc_", "")
        cfg["accessory"] = chosen_acc
        keyboard = build_main_menu_keyboard(chat_id)
        label = ACCESSORY_ICONS.get(chosen_acc, chosen_acc)
        await query.edit_message_text(
            f"✅ **Accessory set to: {label}!**\n\n👇 **Main Menu:**",
            reply_markup=keyboard
        )
        return

    # 7. Open Studio
    if data == "menu_open_studio":
        web_index = _REPO_ROOT / "stickman_service" / "web" / "index.html"
        os.system(f'start "" "{web_index}"')
        await query.answer("Opening Live Studio in browser!", show_alert=True)
        return

    # ── 4-Button Review Callbacks ─────────────────────────────────────────────
    if data.startswith("approve_title_"):
        session_id = data.replace("approve_title_", "")
        sess = video_sessions.get(session_id)
        cfg["mode"] = "waiting_title"
        cfg["active_session"] = session_id
        await query.message.reply_text(
            f"✏️ **Approved! Please send the custom YouTube/TikTok title for Session `{session_id}`:**"
        )
        return

    if data.startswith("approve_post_"):
        session_id = data.replace("approve_post_", "")
        sess = video_sessions.get(session_id)
        if sess:
            v_path = sess["video_path"]
            title = sess.get("title") or sess.get("topic") or "Stickman Explainer"
            await query.message.reply_text(
                f"🚀 **PUBLISHING INITIATED!**\n\n"
                f"📌 **Title**: `{title}`\n"
                f"📁 **Reel**: `{os.path.basename(v_path)}`\n\n"
                f"⏳ Broadcasting to configured platforms (YouTube Shorts, Instagram Reels, TikTok, Telegram Channel)...\n"
                f"Status report with live links will be posted here as uploads finish."
            )
            dispatch_publishing(chat_id=chat_id, bot=context.bot, session_id=session_id)
        return

    if data.startswith("reedit_"):
        session_id = data.replace("reedit_", "")
        keyboard = build_reedit_keyboard(session_id)
        await query.message.reply_text(
            f"🛠️ **Re-Edit & Tweak Options for Session `{session_id}`:**\n\n"
            f"Choose what to tweak:",
            reply_markup=keyboard
        )
        return

    if data.startswith("re_acc_"):
        parts = data.split("_")
        new_acc = parts[2]
        session_id = parts[3]
        sess = video_sessions.get(session_id)
        if sess:
            await query.message.reply_text(f"🔄 Re-rendering with `{new_acc}` accessory...")
            dispatch_stickman_generation(
                chat_id=chat_id,
                bot=context.bot,
                topic=sess.get("topic"),
                accessory=new_acc,
                ratio=sess.get("ratio", "9:16")
            )
        return

    if data.startswith("reject_"):
        session_id = data.replace("reject_", "")
        sess = video_sessions.pop(session_id, None)
        if sess and os.path.exists(sess["video_path"]):
            try:
                os.remove(sess["video_path"])
            except Exception:
                pass
        await query.message.reply_text(
            f"🗑️ **Session `{session_id}` rejected and temporary files discarded.**"
        )
        return

async def handle_message(update, context):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    cfg = get_user_config(chat_id)
    mode = cfg.get("mode", "idle")

    # 1. Custom Title Submission
    if mode == "waiting_title":
        title = msg.text.strip()
        sess_id = cfg.get("active_session")
        cfg["mode"] = "idle"
        sess = video_sessions.get(sess_id)
        if sess:
            sess["title"] = title
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        post_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Post Immediately to All Platforms", callback_data=f"approve_post_{sess_id}")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]
        ])
        await msg.reply_text(
            f"✅ **Title updated to:** `{title}`\n\n"
            f"👇 Tap below to broadcast to all platforms immediately:",
            reply_markup=post_kb
        )
        return

    # 2. Topic Input
    if mode == "waiting_topic" or (msg.text and not msg.text.startswith("/") and mode == "idle" and not msg.document):
        topic = msg.text.strip()
        cfg["mode"] = "idle"
        ratio = cfg.get("ratio", "9:16")
        acc = cfg.get("accessory", "auto")

        await msg.reply_text(
            f"⚡ **Generating Stickman Video from Topic:**\n\n"
            f"📌 **Topic**: `{topic}`\n"
            f"📐 **Ratio**: `{ratio}`\n"
            f"🎭 **Accessory**: `{ACCESSORY_ICONS.get(acc, acc)}`\n\n"
            f"⏳ Gemini is structuring narrative & Python engine is rendering frames... (approx 30-45s)"
        )

        dispatch_stickman_generation(
            chat_id=chat_id,
            bot=context.bot,
            topic=topic,
            accessory=acc,
            ratio=ratio
        )
        return

    # 3. Script Input
    if mode == "waiting_script":
        script_text = msg.text.strip()
        cfg["mode"] = "idle"
        ratio = cfg.get("ratio", "9:16")
        acc = cfg.get("accessory", "auto")

        await msg.reply_text(
            f"📝 **Choreographing User Script:**\n\n"
            f"📜 Length: {len(script_text.split())} words\n"
            f"📐 Ratio: `{ratio}`\n\n"
            f"⏳ Gemini is choreographing acting, 1,500+ Lucide props, and synthesizing voiceover..."
        )

        dispatch_stickman_generation(
            chat_id=chat_id,
            bot=context.bot,
            script=script_text,
            accessory=acc,
            ratio=ratio
        )
        return

    # 4. Manga / Comic PDF Document Upload
    if msg.document:
        doc = msg.document
        fname = doc.file_name or "manga.pdf"
        if fname.lower().endswith(".pdf") or mode == "waiting_manga_pdf":
            cfg["mode"] = "idle"
            ratio = cfg.get("ratio", "9:16")
            acc = cfg.get("accessory", "auto")
            accessory_param = None if acc == "auto" else acc

            file_mb = ((getattr(doc, "file_size", 0) or 0) / (1024 * 1024))
            status_msg = await msg.reply_text(
                f"📥 **Manga PDF Received:** `{fname}` ({file_mb:.1f} MB)\n\n"
                f"⏳ Downloading file and extracting pages via PyMuPDF..."
            )

            # Download PDF
            temp_dir = _REPO_ROOT / "temp" / f"manga_upload_{chat_id}_{int(time.time())}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            local_pdf = temp_dir / fname
            
            try:
                await download_telegram_document(doc, msg, local_pdf, status_msg=status_msg)
            except Exception as dl_err:
                logger.error(f"Failed to download document: {dl_err}", exc_info=True)
                await status_msg.edit_text(f"❌ **Download Failed:** {dl_err}")
                return

            await status_msg.edit_text(
                f"📖 **Pages extracted!** Gemini Vision is analyzing chapter beats & choreographing anime stickman recap..."
            )

            dispatch_stickman_generation(
                chat_id=chat_id,
                bot=context.bot,
                manga_pdf=str(local_pdf),
                accessory=accessory_param,
                ratio=ratio
            )
            return

    # Fallback
    await msg.reply_text(
        "👋 Please select an action from the menu below or send a topic:",
        reply_markup=build_main_menu_keyboard(chat_id)
    )


# ── Bot Service Launcher ─────────────────────────────────────────────────────

def start_telegram_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token.startswith("your_"):
        print("❌ Error: TELEGRAM_BOT_TOKEN is missing or unconfigured in .env!")
        print("Please add TELEGRAM_BOT_TOKEN=... to d:\\Stickman\\.env")
        return

    from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
    from telegram.request import HTTPXRequest

    print("==================================================================")
    print("   AI STICKMAN MASTER ORCHESTRATION & TELEGRAM BOT SERVICE        ")
    print("==================================================================")
    print("[*] Long-polling Telegram listener starting...")

    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=300.0,
        write_timeout=300.0,
        connect_timeout=30.0
    )

    app = ApplicationBuilder().token(token).request(request).build()

    async def global_error_handler(update, context):
        logger.error(f"Uncaught Telegram Error: {context.error}")

    app.add_error_handler(global_error_handler)
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, handle_message))

    print("[OK] Telegram Bot is LIVE! Press Ctrl+C anytime to stop gracefully.\n")
    app.run_polling(poll_interval=2.0, drop_pending_updates=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Stickman Studio & Telegram Bot")
    parser.add_argument("--bot", action="store_true", help="Launch Telegram Bot Service")
    parser.add_argument("--topic", type=str, default=None, help="CLI Topic generation")
    parser.add_argument("--script", type=str, default=None, help="CLI Script generation")
    parser.add_argument("--manga", type=str, default=None, help="CLI Manga PDF generation")
    parser.add_argument("--ratio", type=str, default="9:16", help="Aspect Ratio (9:16, 16:9, 1:1)")
    parser.add_argument("--publish", action="store_true", help="Automatically broadcast to social media via Publishing_Modules")
    args = parser.parse_args()

    if args.bot or (not args.topic and not args.script and not args.manga):
        start_telegram_bot()
    else:
        from stickman_service.pipeline import run_pipeline
        asyncio.run(run_pipeline(
            topic=args.topic,
            script=args.script,
            manga_pdf=args.manga,
            ratio=args.ratio,
            publish=args.publish
        ))
