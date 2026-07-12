"""
╔══════════════════════════════════════════════════════════════╗
║   reminders.py  —  Medicine reminders (+ optional SMS)        ║
╚══════════════════════════════════════════════════════════════╝

Set reminders like "BP tablet at 14:00". The app checks them and alerts
you when they're due.

  WITH Twilio keys -> sends a real SMS to your phone. 📱
  WITHOUT keys      -> shows the reminder on screen (local mode).

Reminders are stored in a local JSON file — nothing leaves your PC
unless you enable SMS.

Twilio free trial: https://www.twilio.com/try-twilio
"""

from __future__ import annotations
import os
import json
import base64
from datetime import datetime

import httpx
import config


def _load() -> list[dict]:
    if not os.path.exists(config.REMINDERS_FILE):
        return []
    try:
        with open(config.REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(items: list[dict]) -> None:
    with open(config.REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def add_reminder(medicine: str, time_hhmm: str, patient: str = "You", note: str = "") -> dict:
    """Add a medicine reminder for a daily time like '14:00'."""
    # normalise/validate the time
    try:
        t = datetime.strptime(time_hhmm.strip(), "%H:%M").strftime("%H:%M")
    except ValueError:
        return {"ok": False, "error": "Time must look like HH:MM (e.g. 09:30 or 21:00)."}

    items = _load()
    reminder = {
        "id": len(items) + 1,
        "patient": patient,
        "medicine": medicine,
        "time": t,
        "note": note,
        "done_today": False,
    }
    items.append(reminder)
    _save(items)
    return {"ok": True, "reminder": reminder}


def list_reminders(patient: str | None = None) -> list[dict]:
    items = _load()
    if patient:
        items = [r for r in items if r["patient"].lower() == patient.lower()]
    return sorted(items, key=lambda r: r["time"])


def remove_reminder(reminder_id: int) -> bool:
    items = _load()
    new = [r for r in items if r["id"] != reminder_id]
    if len(new) == len(items):
        return False
    _save(new)
    return True


def clear_reminders() -> None:
    if os.path.exists(config.REMINDERS_FILE):
        os.remove(config.REMINDERS_FILE)


def due_now(now_hhmm: str | None = None, window_min: int = 30) -> list[dict]:
    """Return reminders due within `window_min` minutes of now (same day)."""
    now = now_hhmm or datetime.now().strftime("%H:%M")
    now_min = _to_minutes(now)
    due = []
    for r in _load():
        diff = _to_minutes(r["time"]) - now_min
        if 0 <= diff <= window_min:
            due.append({**r, "in_minutes": diff})
    return due


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def send_sms(body: str, to_number: str | None = None) -> dict:
    """
    Send an SMS via Twilio if configured; otherwise 'send' it locally
    (print to screen). Never crashes — always returns a status dict.
    """
    to = to_number or config.TWILIO_TO_NUMBER
    if not config.HAS_SMS or not to:
        # Local fallback — show it on screen
        return {"ok": True, "channel": "local", "body": body,
                "note": "SMS not configured — showing reminder here instead."}

    url = f"https://api.twilio.com/2010-04-01/Accounts/{config.TWILIO_ACCOUNT_SID}/Messages.json"
    auth = base64.b64encode(
        f"{config.TWILIO_ACCOUNT_SID}:{config.TWILIO_AUTH_TOKEN}".encode()).decode()
    try:
        resp = httpx.post(
            url,
            data={"From": config.TWILIO_FROM_NUMBER, "To": to, "Body": body},
            headers={"Authorization": f"Basic {auth}"},
            timeout=15,
        )
        if resp.status_code in (200, 201):
            return {"ok": True, "channel": "sms", "to": to}
        return {"ok": False, "channel": "sms", "error": resp.text}
    except Exception as e:
        return {"ok": False, "channel": "sms", "error": str(e)}


def format_reminders(items: list[dict]) -> str:
    if not items:
        return "No reminders set. Add one with:  /remind <medicine> <HH:MM>"
    lines = ["💊 Your medicine reminders:"]
    for r in items:
        note = f" — {r['note']}" if r.get("note") else ""
        lines.append(f"  [{r['id']}] ⏰ {r['time']}  {r['medicine']}{note}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(add_reminder("BP tablet", "14:00", "Rahul", "after lunch"))
    print(format_reminders(list_reminders()))
    print("Due now:", due_now())
    print(send_sms("Test reminder: take your BP tablet 💊"))
    clear_reminders()
