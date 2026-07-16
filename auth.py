"""
╔══════════════════════════════════════════════════════════════╗
║   🔐  auth.py  —  Login system for MediMate AI (ChatGPT-style)║
╚══════════════════════════════════════════════════════════════╝

Ye module 3 kaam karta hai:

  1. 👤 GUEST MODE  — bina login ke sirf GUEST_MESSAGE_LIMIT messages
       (bilkul ChatGPT ki tarah — free try karo, phir login karo).
  2. 📧 EMAIL LOGIN — local signup/login (users.json me SAFE hashed
       passwords — kabhi plain-text nahi!).
  3. 🔵 GOOGLE LOGIN — Streamlit ka built-in st.login() (OIDC).
       Setup: .streamlit/secrets.toml me [auth] section chahiye
       (dekho .streamlit/secrets.toml.example).

Password security:
  - PBKDF2-HMAC-SHA256 + random salt + 200,000 iterations.
  - Matlab agar users.json leak bhi ho jaye, password nahi milega. 🔒
"""

import hashlib
import hmac
import json
import os
import re
import secrets

import streamlit as st

# ─────────────────────────────────────────────
# ⚙️ SETTINGS
# ─────────────────────────────────────────────
GUEST_MESSAGE_LIMIT = 5           # 👤 bina login itne messages free (ChatGPT-style)
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
_PBKDF2_ITERATIONS = 200_000      # password hashing strength

# Email dikhne me sahi hai ya nahi — simple check
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ═════════════════════════════════════════════
#  🔒 PASSWORD HASHING  (kabhi plain-text store nahi!)
# ═════════════════════════════════════════════

def _hash_password(password: str, salt: str) -> str:
    """Password + salt → irreversible hash (PBKDF2-HMAC-SHA256)."""
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITERATIONS
    )
    return dk.hex()


def _verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """Compare in constant time (timing attacks se bachne ke liye)."""
    return hmac.compare_digest(_hash_password(password, salt), stored_hash)


# ═════════════════════════════════════════════
#  💾 LOCAL USER STORE  (users.json)
# ═════════════════════════════════════════════

def _load_users() -> dict:
    """users.json padho. File nahi hai / kharab hai → empty dict."""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_users(users: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def signup(name: str, email: str, password: str) -> dict:
    """
    ✍️ Naya account banao.
    Returns {"ok": True} ya {"ok": False, "error": "..."}.
    """
    name = name.strip()
    email = email.strip().lower()

    if not name:
        return {"ok": False, "error": "Naam to batao! 😅"}
    if not _EMAIL_RE.match(email):
        return {"ok": False, "error": "Email sahi nahi lag rahi — dobara check karo."}
    if len(password) < 6:
        return {"ok": False, "error": "Password kam se kam 6 characters ka rakho."}

    users = _load_users()
    if email in users:
        return {"ok": False, "error": "Ye email pehle se registered hai — Login tab try karo."}

    salt = secrets.token_hex(16)   # har user ka apna random salt
    users[email] = {
        "name": name,
        "salt": salt,
        "password_hash": _hash_password(password, salt),
    }
    _save_users(users)
    return {"ok": True}


def login(email: str, password: str) -> dict:
    """
    🔑 Email + password se login.
    Returns {"ok": True, "user": {...}} ya {"ok": False, "error": "..."}.
    """
    email = email.strip().lower()
    users = _load_users()
    record = users.get(email)

    # Dono galat cases me SAME message — taaki koi guess na kar sake
    # ki kaunsi email registered hai (security best practice).
    if not record or not _verify_password(password, record["salt"], record["password_hash"]):
        return {"ok": False, "error": "Email ya password galat hai."}

    return {"ok": True, "user": {"name": record["name"], "email": email, "provider": "email"}}


# ═════════════════════════════════════════════
#  🔵 GOOGLE LOGIN  (Streamlit native OIDC)
# ═════════════════════════════════════════════

def google_configured() -> bool:
    """Kya secrets.toml me Google [auth] setup hai? (bina setup button hide karenge)"""
    try:
        auth_cfg = st.secrets.get("auth", {})
        # Do styles supported: [auth] direct, ya [auth.google] nested
        if "google" in auth_cfg:
            return bool(auth_cfg["google"].get("client_id"))
        return bool(auth_cfg.get("client_id"))
    except Exception:
        return False


def _google_user() -> dict | None:
    """Agar Google se logged in hai to user dict, warna None."""
    try:
        if getattr(st.user, "is_logged_in", False):
            return {
                "name": st.user.get("name") or st.user.get("email", "User"),
                "email": st.user.get("email", ""),
                "provider": "google",
                "picture": st.user.get("picture", ""),
            }
    except Exception:
        pass
    return None


# ═════════════════════════════════════════════
#  👤 SESSION HELPERS  —  web_app.py yahi use karta hai
# ═════════════════════════════════════════════

def current_user() -> dict | None:
    """
    Abhi kaun logged in hai?
    Pehle Google check karo, phir local (email) session.
    Returns {"name","email","provider"} ya None (guest).
    """
    g = _google_user()
    if g:
        return g
    return st.session_state.get("local_user")


def is_logged_in() -> bool:
    return current_user() is not None


def set_local_user(user: dict) -> None:
    """Email-login success ke baad session me user save karo."""
    st.session_state["local_user"] = user


def logout() -> None:
    """Sab logout karo — Google session + local session dono."""
    st.session_state.pop("local_user", None)
    try:
        if getattr(st.user, "is_logged_in", False):
            st.logout()   # Google/OIDC cookie clear + rerun
    except Exception:
        pass


# ═════════════════════════════════════════════
#  📊 GUEST MESSAGE COUNTING  (ChatGPT-style limit)
# ═════════════════════════════════════════════

def guest_messages_used() -> int:
    return st.session_state.get("guest_msg_count", 0)


def guest_messages_left() -> int:
    return max(0, GUEST_MESSAGE_LIMIT - guest_messages_used())


def record_guest_message() -> None:
    """Har guest message pe counter +1 (logged-in users ke liye call mat karo)."""
    st.session_state["guest_msg_count"] = guest_messages_used() + 1


def can_send_message() -> bool:
    """Kya user abhi message bhej sakta hai? Login = unlimited, guest = limit tak."""
    return is_logged_in() or guest_messages_left() > 0
