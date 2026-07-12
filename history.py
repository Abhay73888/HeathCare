"""
╔══════════════════════════════════════════════════════════════╗
║   history.py  —  Remember every consultation                  ║
╚══════════════════════════════════════════════════════════════╝

Saves each Q&A to a JSON file so you can look back at past chats and
even export a clean Markdown health report to share with a real doctor.

Nothing leaves your computer — it's a plain local file.
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from config import HISTORY_FILE, APP_NAME


def _load() -> list[dict]:
    """Read the history file (returns [] if it doesn't exist yet)."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_consultation(patient: str, question: str, answer: str,
                      urgency: str = "informational", extra: dict | None = None) -> None:
    """Append one consultation to the history file."""
    records = _load()
    records.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient": patient,
        "question": question,
        "answer": answer,
        "urgency": urgency,
        "extra": extra or {},
    })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def get_history(patient: str | None = None, limit: int = 10) -> list[dict]:
    """Return the most recent consultations (optionally for one patient)."""
    records = _load()
    if patient:
        records = [r for r in records if r["patient"].lower() == patient.lower()]
    return records[-limit:]


def clear_history() -> None:
    """Delete all saved consultations."""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)


def export_report(patient: str | None = None, path: str = "health_report.md") -> str:
    """Export consultations as a shareable Markdown report. Returns the path."""
    records = get_history(patient, limit=1000)
    lines = [
        f"# 🏥 {APP_NAME} — Health Report",
        f"\n**Generated:** {datetime.now().strftime('%d %b %Y, %H:%M')}",
        f"\n**Patient:** {patient or 'All users'}",
        f"\n**Total consultations:** {len(records)}",
        "\n> ⚠️ This report is AI-generated and for information only. "
        "Always confirm with a licensed doctor.\n",
        "\n---\n",
    ]
    for i, r in enumerate(records, 1):
        lines.append(f"### {i}. {r['question']}")
        lines.append(f"*{r['timestamp']}  •  Urgency: {r.get('urgency', 'n/a')}*\n")
        lines.append(r["answer"])
        lines.append("\n---\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


if __name__ == "__main__":
    save_consultation("Test", "Do I have a fever?", "Rest and hydrate.", "self-care")
    print(get_history())
