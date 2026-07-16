"""
╔══════════════════════════════════════════════════════════════╗
║   🔐  auth.py  —  Login system for MediMate AI (ChatGPT-style)║
╚══════════════════════════════════════════════════════════════╝

Ye module 4 kaam karta hai:

  1. 👤 GUEST MODE  — bina login ke sirf GUEST_MESSAGE_LIMIT messages
       (bilkul ChatGPT ki tarah — free try karo, phir login karo).
  2. 📧 EMAIL LOGIN — local signup/login (users.json me SAFE hashed
       passwords — kabhi plain-text nahi!).
  3. 📱 PHONE OTP LOGIN — phone number dalo → OTP aayega → verify karo
       → account apne aap ban jayega. Email baad me add kar sakte ho!
       (Real SMS ke liye Twilio keys chahiye secrets.toml me — warna
        DEMO mode me OTP screen pe hi dikh jayega. 🧪)
  4. 🔵 GOOGLE LOGIN — Streamlit ka built-in st.login() (OIDC).
       Setup: .streamlit/secrets.toml me [auth] section chahiye
       (dekho .streamlit/secrets.toml.example).

Password security:
  - PBKDF2-HMAC-SHA256 + random salt + 200,000 iterations.
  - Matlab agar users.json leak bhi ho jaye, password nahi milega. 🔒

OTP security:
  - OTP kabhi plain store nahi hota (hash hota hai session me).
  - 5 minute me expire, max 5 galat attempts, 30s resend cooldown.
"""

import hashlib
import hmac
import json
import os
import re
import secrets
import time

import streamlit as st

# ─────────────────────────────────────────────
# ⚙️ SETTINGS
# ─────────────────────────────────────────────
GUEST_MESSAGE_LIMIT = 5           # 👤 bina login itne messages free (ChatGPT-style)
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
_PBKDF2_ITERATIONS = 200_000      # password hashing strength

# 📱 OTP settings
OTP_LENGTH = 6                    # 6-digit OTP (standard)
OTP_EXPIRY_SECONDS = 300          # 5 minute me OTP expire
OTP_MAX_ATTEMPTS = 5              # itne galat attempts ke baad naya OTP lena padega
OTP_RESEND_SECONDS = 30           # resend ke beech itna gap (spam se bachao)
DEFAULT_COUNTRY_CODE = "+91"      # 10-digit number pe ye lag jayega (India 🇮🇳)

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
#  Key = email  (email accounts)  ya  "+91xxxx" phone (phone accounts)
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


def _email_taken(users: dict, email: str, except_key: str | None = None) -> bool:
    """Kya ye email kisi aur account me already use ho rahi hai?
    (direct email-account key YA phone-account ki linked email)"""
    email = email.strip().lower()
    for key, rec in users.items():
        if key == except_key:
            continue
        if key == email or rec.get("email", "").lower() == email:
            return True
    return False


def signup(name: str, email: str, password: str) -> dict:
    """
    ✍️ Naya account banao (email + password).
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
    if _email_taken(users, email):
        return {"ok": False, "error": "Ye email pehle se registered hai — Login tab try karo."}

    salt = secrets.token_hex(16)   # har user ka apna random salt
    users[email] = {
        "name": name,
        "email": email,
        "salt": salt,
        "password_hash": _hash_password(password, salt),
    }
    _save_users(users)
    return {"ok": True}


def login(email: str, password: str) -> dict:
    """
    🔑 Email + password se login.
    Phone-account walo ne agar baad me email+password add kiya hai,
    to wo bhi isi se login kar sakte hain. 📱→📧
    Returns {"ok": True, "user": {...}} ya {"ok": False, "error": "..."}.
    """
    email = email.strip().lower()
    users = _load_users()
    record = users.get(email)

    # Direct email account nahi mila? Phone accounts me linked email dhundo.
    if not record:
        for rec in users.values():
            if rec.get("email", "").lower() == email and "password_hash" in rec:
                record = rec
                break

    # Dono galat cases me SAME message — taaki koi guess na kar sake
    # ki kaunsi email registered hai (security best practice).
    if (not record or "password_hash" not in record
            or not _verify_password(password, record["salt"], record["password_hash"])):
        return {"ok": False, "error": "Email ya password galat hai."}

    user = {"name": record["name"], "email": email, "provider": "email"}
    if record.get("phone"):
        user["phone"] = record["phone"]
    return {"ok": True, "user": user}


# ═════════════════════════════════════════════
#  📱 PHONE OTP LOGIN
#  Flow: send_otp(number) → user OTP daale → verify_otp(code)
#        → account mil gaya to login, nahi to naya ban jayega. ✨
# ═════════════════════════════════════════════

def normalize_phone(raw: str) -> str | None:
    """
    Phone number ko standard "+91xxxxxxxxxx" format me lao.
      "98765 43210"   → "+919876543210"  (10 digit = India default)
      "+1 555 0100.." → "+15550100.."
    Galat number → None.
    """
    raw = (raw or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None

    if raw.startswith("+"):
        num = "+" + digits
    elif len(digits) == 10:
        num = DEFAULT_COUNTRY_CODE + digits       # 🇮🇳 default
    elif 11 <= len(digits) <= 15:
        num = "+" + digits                        # country code included lagta hai
    else:
        return None

    # E.164 standard: + ke baad 10–15 digits
    return num if 11 <= len(num) <= 16 else None


def _hash_otp(otp: str, salt: str) -> str:
    """OTP bhi hash karke hi rakho — plain kabhi nahi. (5-min ke liye SHA256 kaafi hai)"""
    return hashlib.sha256((salt + otp).encode("utf-8")).hexdigest()


def sms_configured() -> bool:
    """Kya secrets.toml me [sms] Twilio keys hain? (nahi → demo mode)"""
    try:
        s = st.secrets.get("sms", {})
        return bool(s.get("twilio_sid") and s.get("twilio_token") and s.get("twilio_from"))
    except Exception:
        return False


def _send_sms_twilio(phone: str, body: str) -> bool:
    """Twilio REST API se real SMS bhejo (httpx already project me hai)."""
    try:
        import httpx
        s = st.secrets["sms"]
        r = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{s['twilio_sid']}/Messages.json",
            data={"To": phone, "From": s["twilio_from"], "Body": body},
            auth=(s["twilio_sid"], s["twilio_token"]),
            timeout=15,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


def send_otp(phone_raw: str) -> dict:
    """
    📲 Phone pe OTP bhejo.
    Returns:
      {"ok": True, "phone": "+91...", "demo": False}            → real SMS gaya
      {"ok": True, "phone": "+91...", "demo": True, "otp": ...} → demo mode
                                        (SMS setup nahi — OTP screen pe dikhao)
      {"ok": False, "error": "..."}
    """
    phone = normalize_phone(phone_raw)
    if not phone:
        return {"ok": False,
                "error": "Phone number sahi nahi lag raha — 10 digit (ya +country code ke saath) daalo."}

    # ⏱️ Resend cooldown — spam se bachao
    now = time.time()
    prev = st.session_state.get("_otp")
    if prev and prev.get("phone") == phone:
        wait = int(OTP_RESEND_SECONDS - (now - prev.get("last_sent", 0)))
        if wait > 0:
            return {"ok": False, "error": f"Thoda ruko — {wait} second baad dobara OTP bhej sakte ho. ⏳"}

    otp = f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"
    salt = secrets.token_hex(8)
    st.session_state["_otp"] = {
        "phone": phone,
        "otp_hash": _hash_otp(otp, salt),
        "salt": salt,
        "expires": now + OTP_EXPIRY_SECONDS,
        "attempts": 0,
        "last_sent": now,
    }

    if sms_configured():
        if not _send_sms_twilio(phone, f"MediMate AI login OTP: {otp} (5 min valid). Kisi ko mat batana!"):
            st.session_state.pop("_otp", None)
            return {"ok": False, "error": "SMS bhejne me dikkat aa gayi — number check karke dobara try karo."}
        return {"ok": True, "phone": phone, "demo": False}

    # 🧪 DEMO MODE — Twilio setup nahi hai, OTP screen pe hi dikhayenge
    return {"ok": True, "phone": phone, "demo": True, "otp": otp}


def verify_otp(code: str) -> dict:
    """
    ✅ User ka dala hua OTP check karo.
    Sahi hua → account dhundo ya naya banao → login!
    Returns {"ok": True, "user": {...}, "new": bool} ya {"ok": False, "error": "..."}.
    """
    state = st.session_state.get("_otp")
    if not state:
        return {"ok": False, "error": "Pehle OTP bhejo — phir verify karna. 😊"}
    if time.time() > state["expires"]:
        st.session_state.pop("_otp", None)
        return {"ok": False, "error": "OTP expire ho gaya (5 min) — naya OTP bhejo."}
    if state["attempts"] >= OTP_MAX_ATTEMPTS:
        st.session_state.pop("_otp", None)
        return {"ok": False, "error": "Bahut saare galat attempts — naya OTP bhejo."}

    state["attempts"] += 1
    code = re.sub(r"\D", "", code or "")
    if not hmac.compare_digest(_hash_otp(code, state["salt"]), state["otp_hash"]):
        left = OTP_MAX_ATTEMPTS - state["attempts"]
        return {"ok": False, "error": f"OTP galat hai — dobara dekh ke daalo. ({left} attempts bache)"}

    # 🎉 OTP sahi! Ab account dhundo ya banao.
    phone = state["phone"]
    st.session_state.pop("_otp", None)

    users = _load_users()
    rec = users.get(phone)
    is_new = rec is None
    if is_new:
        # ✨ Naya account — naam baad me settings se change kar sakte ho,
        #    email bhi baad me add hoga (⚙️ Account settings me).
        rec = {"name": "User " + phone[-4:], "phone": phone, "email": ""}
        users[phone] = rec
        _save_users(users)

    user = {"name": rec["name"], "email": rec.get("email", ""),
            "phone": phone, "provider": "phone"}
    return {"ok": True, "user": user, "new": is_new}


# ═════════════════════════════════════════════
#  ⚙️ PROFILE UPDATE  —  phone users baad me email/password add karein
# ═════════════════════════════════════════════

def update_profile(user: dict, name: str | None = None,
                   email: str | None = None, password: str | None = None) -> dict:
    """
    Logged-in user ka naam / email / password update karo.
      📱 Phone user + email + password add kare → phir wo EMAIL se bhi
         login kar payega. (User ne yahi manga tha! 😄)
    Returns {"ok": True, "user": {...updated...}} ya {"ok": False, "error": "..."}.
    """
    users = _load_users()
    key = user.get("phone") if user.get("provider") == "phone" else user.get("email", "")
    rec = users.get(key)
    if not rec:
        return {"ok": False, "error": "Account nahi mila — dobara login karke try karo."}

    if name is not None and name.strip():
        rec["name"] = name.strip()

    if email:
        email = email.strip().lower()
        if not _EMAIL_RE.match(email):
            return {"ok": False, "error": "Email sahi nahi lag rahi — dobara check karo."}
        if user.get("provider") == "email" and email != key:
            return {"ok": False, "error": "Email-account ki email change abhi supported nahi hai."}
        if _email_taken(users, email, except_key=key):
            return {"ok": False, "error": "Ye email kisi aur account me already use ho rahi hai."}
        rec["email"] = email

    if password:
        if len(password) < 6:
            return {"ok": False, "error": "Password kam se kam 6 characters ka rakho."}
        if user.get("provider") == "phone" and not rec.get("email") and not email:
            return {"ok": False, "error": "Password set karne se pehle email add karo "
                                          "(email+password se hi login hota hai)."}
        salt = secrets.token_hex(16)
        rec["salt"] = salt
        rec["password_hash"] = _hash_password(password, salt)

    _save_users(users)

    updated = {"name": rec["name"], "email": rec.get("email", ""),
               "provider": user["provider"]}
    if rec.get("phone"):
        updated["phone"] = rec["phone"]
    return {"ok": True, "user": updated}


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
    Pehle Google check karo, phir local (email/phone) session.
    Returns {"name","email","provider",...} ya None (guest).
    """
    g = _google_user()
    if g:
        return g
    return st.session_state.get("local_user")


def is_logged_in() -> bool:
    return current_user() is not None


def set_local_user(user: dict) -> None:
    """Email/Phone-login success ke baad session me user save karo."""
    st.session_state["local_user"] = user


def logout() -> None:
    """Sab logout karo — Google session + local session + OTP state dono."""
    st.session_state.pop("local_user", None)
    st.session_state.pop("_otp", None)
    st.session_state.pop("_otp_demo", None)
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
