"""
Core_Modules/user_credential_manager.py
========================================
Multi-User Credential Manager with GitHub Secrets API Integration & Libsodium Encryption

Manages user authentication, credential collection, and secure storage via GitHub Secrets.
Each user's credentials can be securely synced to GitHub Secrets using official Libsodium asymmetric encryption.

Security Notes:
- Requires GitHub PAT with `repo` and `secrets` (admin:repo_hook / repo) scopes.
- Uses Libsodium SealedBox encryption required by GitHub Actions Secrets REST API.
- Local fallback uses Fernet symmetric encryption.
"""

import os
import json
import base64
import logging
import hashlib
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("user_credential_manager")

# ── Configuration ─────────────────────────────────────────────────────────────
GITHUB_TOKEN = (
    os.getenv("GH_PAT") or
    os.getenv("GITHUB_PAT") or
    os.getenv("GITHUB_TOKEN") or
    ""
).strip()

GITHUB_REPO = os.getenv("GITHUB_REPO", "stickman-with-agent").strip()
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "midhun6771").strip()

# ── User Session Storage ───────────────────────────────────────────────────────
_SESSIONS_DIR = Path("user_sessions")
_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# ── Credential Collection Guides ────────────────────────────────────────────────
CREDENTIAL_GUIDES = {
    "gemini_api_key": {
        "name": "Google Gemini API Key",
        "link": "https://aistudio.google.com/app/apikey",
        "instructions": [
            "1. Go to Google AI Studio",
            "2. Click 'Create API Key'",
            "3. Select or create a project",
            "4. Copy the API key",
            "5. Paste it here"
        ]
    },
    "telegram_bot_token": {
        "name": "Telegram Bot Token",
        "link": "https://t.me/BotFather",
        "instructions": [
            "1. Open Telegram and search for @BotFather",
            "2. Send /newbot command",
            "3. Follow the instructions to create a bot",
            "4. Copy the token (starts with numbers:bot_token)",
            "5. Paste it here"
        ]
    },
    "telegram_api_id": {
        "name": "Telegram API ID",
        "link": "https://my.telegram.org",
        "instructions": [
            "1. Log into https://my.telegram.org",
            "2. Go to 'API development tools'",
            "3. Copy the numeric 'api_id'",
            "4. Paste it here"
        ]
    },
    "telegram_api_hash": {
        "name": "Telegram API Hash",
        "link": "https://my.telegram.org",
        "instructions": [
            "1. Log into https://my.telegram.org",
            "2. Go to 'API development tools'",
            "3. Copy the 'api_hash' string",
            "4. Paste it here"
        ]
    },
    "youtube_client_secret": {
        "name": "YouTube Client Secret",
        "link": "https://console.cloud.google.com/apis/credentials",
        "instructions": [
            "1. Go to Google Cloud Console Credentials",
            "2. Create OAuth 2.0 Client ID (Web/Desktop application)",
            "3. Download the client_secret.json file",
            "4. Paste the JSON content here"
        ]
    },
    "youtube_token_json": {
        "name": "YouTube Token JSON",
        "link": "https://console.cloud.google.com/apis/credentials",
        "instructions": [
            "1. Complete the YouTube OAuth login flow",
            "2. Copy the token.json content",
            "3. Paste it here"
        ]
    },
    "meta_page_token": {
        "name": "Meta (Facebook/Instagram) Page Token",
        "link": "https://developers.facebook.com/tools/explorer",
        "instructions": [
            "1. Go to Facebook Graph API Explorer",
            "2. Generate Page Access Token",
            "3. Copy the token (starts with EAAB...)",
            "4. Paste it here"
        ]
    },
    "telegram_public_group_id": {
        "name": "Telegram Public Broadcast Channel ID",
        "link": "https://t.me/username_to_id_bot",
        "instructions": [
            "1. Forward a message from your channel to @username_to_id_bot",
            "2. Copy the numeric group ID (e.g., -1001234567890)",
            "3. Paste it here"
        ]
    }
}

REQUIRED_CREDENTIALS = [
    "gemini_api_key",
    "telegram_bot_token",
    "telegram_api_id",
    "telegram_api_hash"
]

# ── GitHub Secrets API with Libsodium Encryption (FIXED) ──────────────────────
def _get_github_headers() -> Dict[str, str]:
    if not GITHUB_TOKEN:
        raise ValueError("GH_PAT environment variable is not configured")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

def _secret_name(user_id: str, credential_type: str) -> str:
    """Generate normalized uppercase GitHub secret name."""
    clean = f"{user_id}_{credential_type}".upper().replace("-", "_").replace(" ", "_")
    return "".join(c for c in clean if c.isalnum() or c == "_")

def store_user_credential(user_id: str, credential_type: str, value: str) -> bool:
    """
    Store a credential into GitHub Secrets using official Libsodium asymmetric encryption.
    Falls back to local encrypted store if GH_PAT is missing or API fails.
    """
    # 1. Always persist to local encrypted storage first
    _store_local_credential(user_id, credential_type, value)

    # 2. Check if GitHub PAT is available
    token = GITHUB_TOKEN or os.getenv("GH_PAT") or os.getenv("GITHUB_PAT")
    if not token:
        logger.warning(f"⚠️ GH_PAT not set — saved {credential_type} to local encrypted vault only.")
        return True

    secret_name = _secret_name(user_id, credential_type)
    owner = GITHUB_OWNER
    repo = GITHUB_REPO

    try:
        from nacl import encoding, public
    except ImportError:
        logger.warning("⚠️ 'pynacl' library not installed. Secret saved locally only. (Run: pip install pynacl)")
        return True

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # Step A: Fetch Repository Public Key
        pk_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
        pk_resp = requests.get(pk_url, headers=headers, timeout=15)
        if pk_resp.status_code != 200:
            logger.error(f"❌ Failed to fetch GitHub repo public key: {pk_resp.status_code} - {pk_resp.text}")
            return False

        pk_data = pk_resp.json()
        key_id = pk_data["key_id"]
        raw_key = pk_data["key"]

        # Step B: Encrypt using Libsodium SealedBox
        public_key = public.PublicKey(raw_key.encode("utf-8"), encoding.Base64Encoder)
        sealed_box = public.SealedBox(public_key)
        encrypted_bytes = sealed_box.encrypt(value.strip().encode("utf-8"))
        encrypted_b64 = base64.b64encode(encrypted_bytes).decode("utf-8")

        # Step C: Upload Encrypted Secret to GitHub Actions
        put_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
        payload = {
            "encrypted_value": encrypted_b64,
            "key_id": key_id
        }
        put_resp = requests.put(put_url, headers=headers, json=payload, timeout=15)

        if put_resp.status_code in (201, 204):
            logger.info(f"✅ Successfully synced secret '{secret_name}' to GitHub Actions for {owner}/{repo}")
            return True
        else:
            logger.error(f"❌ Failed to upload secret to GitHub: {put_resp.status_code} - {put_resp.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Error during GitHub Secret Libsodium upload: {e}")
        return False

# ── Local Encrypted Storage (Fernet) ───────────────────────────────────────────
def _get_or_create_fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None

    key_file = _SESSIONS_DIR / "encryption.key"
    if key_file.exists():
        with open(key_file, "rb") as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
    return Fernet(key)

def _store_local_credential(user_id: str, credential_type: str, value: str) -> bool:
    """Store credential in local encrypted storage."""
    fernet = _get_or_create_fernet()
    user_file = _SESSIONS_DIR / f"{user_id}_credentials.json"
    encrypted_data = {}

    if user_file.exists():
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                encrypted_data = json.load(f)
        except Exception:
            pass

    if fernet:
        encrypted_value = fernet.encrypt(value.encode("utf-8")).decode("utf-8")
    else:
        # Simple obfuscation if cryptography is not available
        encrypted_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")

    encrypted_data[credential_type] = encrypted_value

    try:
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(encrypted_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"❌ Error storing local credential: {e}")
        return False

def _retrieve_local_credential(user_id: str, credential_type: str) -> Optional[str]:
    """Retrieve credential from local encrypted storage."""
    user_file = _SESSIONS_DIR / f"{user_id}_credentials.json"
    if not user_file.exists():
        return None

    try:
        with open(user_file, "r", encoding="utf-8") as f:
            encrypted_data = json.load(f)

        if credential_type not in encrypted_data:
            return None

        encrypted_val = encrypted_data[credential_type]
        fernet = _get_or_create_fernet()
        if fernet:
            return fernet.decrypt(encrypted_val.encode("utf-8")).decode("utf-8")
        else:
            return base64.b64decode(encrypted_val.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"❌ Error retrieving local credential: {e}")
        return None

def retrieve_user_credential(user_id: str, credential_type: str) -> Optional[str]:
    return _retrieve_local_credential(user_id, credential_type)

# ── User Account Management ───────────────────────────────────────────────────
def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = os.urandom(32).hex()
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return key, salt

def create_user(username: str, password: str, telegram_chat_id: str) -> Dict[str, Any]:
    user_id = username.lower().replace(" ", "_")
    user_file = _SESSIONS_DIR / f"{user_id}_user.json"
    if user_file.exists():
        return {"success": False, "error": "Username already exists"}

    password_hash, salt = hash_password(password)
    user_data = {
        "user_id": user_id,
        "username": username,
        "password_hash": password_hash,
        "salt": salt,
        "telegram_chat_id": str(telegram_chat_id),
        "created_at": datetime.utcnow().isoformat(),
        "credentials_collected": [],
        "is_active": True
    }
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=2)
    return {"success": True, "user_id": user_id}

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user_id = username.lower().replace(" ", "_")
    user_file = _SESSIONS_DIR / f"{user_id}_user.json"
    if not user_file.exists():
        return None

    try:
        with open(user_file, "r", encoding="utf-8") as f:
            user_data = json.load(f)
        p_hash, _ = hash_password(password, user_data["salt"])
        if p_hash == user_data["password_hash"]:
            return user_data
    except Exception:
        pass
    return None

def get_user_by_telegram_chat(telegram_chat_id: str) -> Optional[Dict[str, Any]]:
    for user_file in _SESSIONS_DIR.glob("*_user.json"):
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)
            if str(user_data.get("telegram_chat_id")) == str(telegram_chat_id):
                return user_data
        except Exception:
            continue
    return None

def save_user_credential(user_id: str, credential_type: str, value: str) -> Dict[str, Any]:
    """Save credential locally and attempt sync to GitHub Secrets."""
    success = store_user_credential(user_id, credential_type, value)
    user_file = _SESSIONS_DIR / f"{user_id}_user.json"
    if user_file.exists():
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)
            collected = user_data.setdefault("credentials_collected", [])
            if credential_type not in collected:
                collected.append(credential_type)
            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, indent=2)
        except Exception:
            pass

    return {"success": success, "credential_type": credential_type}
