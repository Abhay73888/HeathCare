"""
╔══════════════════════════════════════════════════════════════╗
║   emergency.py  —  Life-saving triage & first-aid engine      ║
╚══════════════════════════════════════════════════════════════╝

This is the SAFETY HEART of the app. Before any chit-chat, we scan the
user's words for RED FLAGS — signs of a medical emergency (heart attack,
stroke, severe bleeding, suicidal thoughts, etc.). If found, we shout the
right emergency number IMMEDIATELY instead of giving casual advice.

It also carries an offline FIRST-AID library so it helps even with zero
internet.

⚠️  This is decision-support, NOT a diagnosis. When in doubt: call for help.
"""

from __future__ import annotations
import re
from config import emergency_numbers_for


# ─────────────────────────────────────────────
# RED FLAGS  —  patterns that mean "act NOW"
# Each entry: name, keyword patterns, and the advice to show.
# ─────────────────────────────────────────────
RED_FLAGS = [
    {
        "name": "Possible Heart Attack",
        "emoji": "❤️‍🩹",
        "patterns": [
            r"chest pain", r"chest (tight|pressure|heavy)", r"pain.*(left arm|jaw)",
            r"crushing pain", r"can'?t breathe.*chest",
        ],
        "advice": "Chew an aspirin if not allergic, sit down, stay calm, and call an ambulance NOW.",
    },
    {
        "name": "Possible Stroke (F.A.S.T.)",
        "emoji": "🧠",
        "patterns": [
            r"face (droop|drooping|numb)", r"slurred speech", r"can'?t speak",
            r"sudden (weakness|numbness)", r"one side.*(weak|numb)", r"arm.*drift",
        ],
        "advice": "Remember F.A.S.T. — Face, Arms, Speech, Time. Note the time symptoms started and call an ambulance IMMEDIATELY.",
    },
    {
        "name": "Difficulty Breathing",
        "emoji": "🫁",
        "patterns": [
            r"can'?t breathe", r"cannot breathe", r"struggling to breathe",
            r"short(ness)? of breath", r"choking", r"gasping", r"turning blue",
        ],
        "advice": "Sit upright, loosen tight clothing, use a rescue inhaler if prescribed, and call emergency services.",
    },
    {
        "name": "Severe Bleeding",
        "emoji": "🩸",
        "patterns": [
            r"severe bleeding", r"won'?t stop bleeding", r"heavy bleeding",
            r"lost a lot of blood", r"deep (cut|wound)", r"gushing blood",
        ],
        "advice": "Press firmly on the wound with a clean cloth, raise the injured area above the heart, and call for help.",
    },
    {
        "name": "Anaphylaxis / Severe Allergic Reaction",
        "emoji": "🐝",
        "patterns": [
            r"throat (closing|swelling)", r"swollen (tongue|throat|lips)",
            r"severe allergic", r"anaphyla", r"whole body (rash|hives).*breath",
        ],
        "advice": "Use an EpiPen (adrenaline auto-injector) if available and call an ambulance right away.",
    },
    {
        "name": "Poisoning / Overdose",
        "emoji": "☠️",
        "patterns": [
            r"overdose", r"swallowed (poison|chemical|pills)", r"drank (poison|bleach|acid)",
            r"too many (pills|tablets)",
        ],
        "advice": "Do NOT induce vomiting unless told to. Keep the container/label and call the poison helpline or ambulance.",
    },
    {
        "name": "Suicidal / Self-harm Crisis",
        "emoji": "💚",
        "patterns": [
            r"suicid", r"kill myself", r"end my life", r"want to die",
            r"self harm", r"hurt myself", r"no reason to live",
        ],
        "advice": ("You are not alone and your life matters. Please talk to someone right now — "
                   "reach a trained counsellor on a crisis line, and stay with a person you trust."),
        "is_mental_health": True,
    },
    {
        "name": "Unconscious / Seizure",
        "emoji": "⚡",
        "patterns": [
            r"unconscious", r"passed out", r"not waking up", r"seizure",
            r"convuls", r"fitting", r"collapsed",
        ],
        "advice": "Place them on their side (recovery position), clear the area, don't restrain, and call an ambulance.",
    },
]


def detect_emergency(text: str, country: str = "India") -> dict | None:
    """
    Scan text for emergency red flags.

    Returns a dict with details if an emergency is detected, else None.
    """
    lowered = text.lower()
    for flag in RED_FLAGS:
        for pattern in flag["patterns"]:
            if re.search(pattern, lowered):
                numbers = emergency_numbers_for(country)
                return {
                    "detected": True,
                    "name": flag["name"],
                    "emoji": flag["emoji"],
                    "advice": flag["advice"],
                    "is_mental_health": flag.get("is_mental_health", False),
                    "numbers": numbers,
                    "matched": pattern,
                }
    return None


# ─────────────────────────────────────────────
# FIRST-AID LIBRARY  (offline, step-by-step)
# ─────────────────────────────────────────────
FIRST_AID = {
    "choking": [
        "Ask 'Are you choking?' If they can't speak/cough, act fast.",
        "Give 5 firm back blows between the shoulder blades.",
        "Give 5 abdominal thrusts (Heimlich): hands above the navel, pull in and up.",
        "Repeat back blows + thrusts until the object clears or help arrives.",
        "If they go unconscious, start CPR and call an ambulance.",
    ],
    "burns": [
        "Cool the burn under cool (not ice-cold) running water for 20 minutes.",
        "Remove rings/tight items before swelling starts.",
        "Cover loosely with cling film or a clean non-stick dressing.",
        "Do NOT apply butter, toothpaste, or ice.",
        "Seek medical help for large, deep, or facial burns.",
    ],
    "bleeding": [
        "Apply firm, direct pressure with a clean cloth or dressing.",
        "Keep the injured part raised above heart level if possible.",
        "Add more layers on top if blood soaks through — don't remove the first.",
        "Once controlled, bandage snugly (not so tight it cuts circulation).",
        "Seek care for deep, gaping, or non-stopping wounds.",
    ],
    "cpr": [
        "Check response and breathing. If none, call an ambulance / ask someone to.",
        "Place hands in the centre of the chest, arms straight.",
        "Push HARD and FAST: ~5-6 cm deep, 100-120 pushes per minute.",
        "Tip: push to the beat of 'Stayin' Alive'.",
        "Continue until help arrives or the person starts breathing.",
    ],
    "fainting": [
        "Lay the person down and raise their legs about 30 cm.",
        "Loosen tight clothing and ensure fresh air.",
        "When they wake, let them rest before sitting up slowly.",
        "If they don't wake within a minute, call for help.",
    ],
    "burn_fever": [
        "Rest and sip fluids often to stay hydrated.",
        "Use paracetamol as directed for comfort (follow the label).",
        "A lukewarm sponge can help cool a high fever.",
        "See a doctor if fever >39°C, lasts >3 days, or with a stiff neck/rash.",
    ],
    "snake_bite": [
        "Keep the person calm and still — movement spreads venom.",
        "Keep the bitten limb below heart level and immobilised.",
        "Remove rings/watches near the bite before swelling.",
        "Do NOT cut, suck, or apply a tight tourniquet.",
        "Get to a hospital for antivenom as fast as possible.",
    ],
    "nosebleed": [
        "Sit up and lean slightly FORWARD (not back).",
        "Pinch the soft part of the nose for 10-15 minutes without releasing.",
        "Breathe through the mouth.",
        "Seek help if bleeding won't stop after 20 minutes.",
    ],
    "sprain": [
        "Remember R.I.C.E: Rest, Ice, Compression, Elevation.",
        "Ice for 15-20 min every 2-3 hours for the first day.",
        "Wrap with an elastic bandage for support (not too tight).",
        "See a doctor if you can't bear weight or it's severely swollen.",
    ],
}


def first_aid(condition: str) -> dict | None:
    """Look up step-by-step first aid for a condition (fuzzy keyword match)."""
    key = condition.lower().strip()
    # direct hit
    if key in FIRST_AID:
        return {"condition": key, "steps": FIRST_AID[key]}
    # fuzzy: find the first topic whose name appears in the query
    for topic, steps in FIRST_AID.items():
        if topic.replace("_", " ") in key or key in topic:
            return {"condition": topic, "steps": steps}
    return None


def available_first_aid_topics() -> list[str]:
    """List all first-aid topics we can help with offline."""
    return sorted(FIRST_AID.keys())


if __name__ == "__main__":
    print(detect_emergency("I have crushing chest pain and pain in my left arm"))
    print(detect_emergency("just a mild headache"))
    print(first_aid("choking"))
