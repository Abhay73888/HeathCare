"""
╔══════════════════════════════════════════════════════════════╗
║   knowledge.py  —  Offline medical knowledge base (fallback)  ║
╚══════════════════════════════════════════════════════════════╝

If there's no internet or no API key, the agent isn't useless — it can
still answer common health questions from this trusted, curated mini
knowledge base. Think of it as a tiny offline first-aid encyclopedia.

Each topic has: what it is, common symptoms, self-care, and when to see
a doctor. Information is general and educational — NOT a diagnosis.
"""

from __future__ import annotations


KNOWLEDGE_BASE = {
    "diabetes": {
        "title": "Type 2 Diabetes",
        "about": "A long-term condition where the body can't use insulin well, so blood sugar stays high.",
        "symptoms": ["Frequent urination", "Excessive thirst", "Unexplained weight loss",
                     "Fatigue", "Blurred vision", "Slow-healing wounds"],
        "self_care": ["Eat balanced, low-sugar meals", "Exercise regularly (30 min/day)",
                      "Monitor blood sugar", "Maintain a healthy weight"],
        "see_doctor": "See a doctor for blood tests (HbA1c) and a proper management plan.",
    },
    "hypertension": {
        "title": "High Blood Pressure (Hypertension)",
        "about": "When the force of blood against artery walls stays too high over time.",
        "symptoms": ["Often no symptoms ('silent killer')", "Headaches", "Dizziness",
                     "Nosebleeds (in severe cases)"],
        "self_care": ["Reduce salt intake", "Exercise", "Limit alcohol", "Manage stress",
                      "Don't smoke"],
        "see_doctor": "Get your BP checked regularly; a doctor may prescribe medication.",
    },
    "fever": {
        "title": "Fever",
        "about": "A temporary rise in body temperature, usually a sign the body is fighting infection.",
        "symptoms": ["Temperature above 38°C", "Chills", "Sweating", "Headache", "Body aches"],
        "self_care": ["Rest", "Drink plenty of fluids", "Paracetamol as directed",
                      "Lukewarm sponge to cool down"],
        "see_doctor": "See a doctor if fever is >39°C, lasts more than 3 days, or comes with a stiff neck, rash, or confusion.",
    },
    "common cold": {
        "title": "Common Cold",
        "about": "A mild viral infection of the nose and throat.",
        "symptoms": ["Runny/blocked nose", "Sore throat", "Sneezing", "Cough", "Mild fever"],
        "self_care": ["Rest and stay warm", "Drink fluids", "Warm salt-water gargle",
                      "Steam inhalation", "Honey & ginger for the throat"],
        "see_doctor": "See a doctor if symptoms last >10 days, high fever, or breathing difficulty.",
    },
    "headache": {
        "title": "Headache",
        "about": "Pain in the head or upper neck — most are harmless (tension or dehydration).",
        "symptoms": ["Dull/throbbing pain", "Pressure around forehead/temples", "Sensitivity to light"],
        "self_care": ["Drink water (dehydration is common)", "Rest in a quiet, dark room",
                      "Gentle neck/shoulder stretches", "Limit screen time"],
        "see_doctor": "Seek urgent help for a sudden 'worst-ever' headache, or one with fever, stiff neck, vision loss, or weakness.",
    },
    "anxiety": {
        "title": "Anxiety",
        "about": "A feeling of worry or fear that can affect daily life when persistent.",
        "symptoms": ["Restlessness", "Racing heart", "Trouble sleeping", "Difficulty concentrating",
                     "Rapid breathing"],
        "self_care": ["Slow breathing (4-7-8 technique)", "Regular exercise", "Limit caffeine",
                      "Talk to someone you trust", "Good sleep routine"],
        "see_doctor": "If anxiety interferes with daily life, a doctor or counsellor can really help — reaching out is a strength.",
    },
    "dehydration": {
        "title": "Dehydration",
        "about": "When the body loses more fluid than it takes in.",
        "symptoms": ["Thirst", "Dark yellow urine", "Dry mouth", "Tiredness", "Dizziness"],
        "self_care": ["Sip water regularly", "Use ORS (oral rehydration salts) if losing fluids",
                      "Avoid excess caffeine/alcohol"],
        "see_doctor": "Seek help for severe dizziness, no urination, or confusion.",
    },
    "acidity": {
        "title": "Acidity / Heartburn",
        "about": "A burning feeling when stomach acid rises into the food pipe.",
        "symptoms": ["Burning in chest/throat", "Sour taste", "Bloating", "Burping"],
        "self_care": ["Eat smaller meals", "Avoid spicy/oily/late-night food", "Don't lie down right after eating",
                      "Stay upright; raise the head of the bed"],
        "see_doctor": "See a doctor if frequent, with weight loss, or trouble swallowing.",
    },
}


def lookup(query: str) -> dict | None:
    """Find a knowledge-base topic that matches the query (keyword match)."""
    q = query.lower()
    # exact / substring topic match
    for key, entry in KNOWLEDGE_BASE.items():
        if key in q:
            return entry
    # match on symptoms / title words
    for entry in KNOWLEDGE_BASE.values():
        if entry["title"].lower() in q:
            return entry
    return None


def format_entry(entry: dict) -> str:
    """Turn a knowledge entry into a friendly, readable answer."""
    lines = [f"📖 {entry['title']}", "", entry["about"], "", "Common signs:"]
    lines += [f"  • {s}" for s in entry["symptoms"]]
    lines += ["", "Self-care tips:"]
    lines += [f"  ✓ {s}" for s in entry["self_care"]]
    lines += ["", f"👩‍⚕️ {entry['see_doctor']}"]
    return "\n".join(lines)


def all_topics() -> list[str]:
    """List every topic in the offline knowledge base."""
    return sorted(KNOWLEDGE_BASE.keys())


if __name__ == "__main__":
    hit = lookup("what are diabetes symptoms")
    print(format_entry(hit) if hit else "No match")
