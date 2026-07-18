"""
╔══════════════════════════════════════════════════════════════╗
║   knowledge.py  —  Offline medical knowledge base (fallback)  ║
╚══════════════════════════════════════════════════════════════╝

If there's no internet or no API key, the agent isn't useless — it can
still answer common health questions from this trusted, curated mini
knowledge base. Think of it as a tiny offline first-aid encyclopedia.

V2 UPGRADES 🚀
  • Topics 8 → 20 (asthma, migraine, UTI, thyroid, anemia, PCOS, aur bhi…)
  • Smart retrieval: TF-IDF cosine similarity (sklearn) — ab fuzzy/multi-word
    queries bhi match hoti hain ("saans lene me dikkat aur wheezing" → asthma).
    Substring match fallback ke roop me abhi bhi hai (sklearn na ho tab bhi
    kaam kare — same graceful-fallback style).

Each topic has: what it is, common symptoms, self-care, and when to see
a doctor. Information is general and educational — NOT a diagnosis.
"""

from __future__ import annotations

import config  # noqa: F401  (UTF-8 console fix on Windows)


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
    "asthma": {
        "title": "Asthma",
        "about": "A condition where airways narrow and swell, making breathing difficult, often triggered by dust, pollen, cold air or exercise.",
        "symptoms": ["Wheezing (whistling sound while breathing)", "Shortness of breath",
                     "Chest tightness", "Coughing, worse at night or early morning"],
        "self_care": ["Avoid known triggers (dust, smoke, pollen)", "Keep inhaler accessible and use as prescribed",
                      "Warm up before exercise", "Keep home dust-free"],
        "see_doctor": "Seek urgent help if the inhaler doesn't relieve symptoms, lips turn bluish, or speaking is difficult.",
    },
    "migraine": {
        "title": "Migraine",
        "about": "A neurological condition causing intense, often one-sided throbbing headaches, sometimes with nausea and light sensitivity.",
        "symptoms": ["Throbbing pain, often one side", "Nausea/vomiting", "Sensitivity to light and sound",
                     "Aura (flashing lights/zigzag lines) before the headache"],
        "self_care": ["Rest in a dark, quiet room", "Cold compress on forehead", "Stay hydrated",
                      "Track and avoid triggers (skipped meals, poor sleep, certain foods)"],
        "see_doctor": "See a doctor if migraines are frequent, disabling, or suddenly change in pattern.",
    },
    "uti": {
        "title": "Urinary Tract Infection (UTI)",
        "about": "A bacterial infection of the bladder or urinary tract, more common in women.",
        "symptoms": ["Burning while urinating", "Frequent urge to urinate", "Cloudy or strong-smelling urine",
                     "Lower belly pain"],
        "self_care": ["Drink plenty of water", "Don't hold urine for long", "Urinate after intercourse",
                      "Maintain hygiene"],
        "see_doctor": "See a doctor promptly — UTIs usually need antibiotics. Urgent if fever, back pain, or blood in urine.",
    },
    "thyroid": {
        "title": "Thyroid Problems (Hypo/Hyperthyroidism)",
        "about": "The thyroid gland making too little (hypo) or too much (hyper) hormone, affecting metabolism.",
        "symptoms": ["Hypo: weight gain, fatigue, cold intolerance, hair loss, constipation",
                     "Hyper: weight loss, racing heart, sweating, anxiety, tremors",
                     "Neck swelling (goitre) in some cases"],
        "self_care": ["Take prescribed thyroid medicine at the same time daily (empty stomach for hypo)",
                      "Regular TSH testing as advised", "Balanced diet with adequate iodine"],
        "see_doctor": "A simple TSH blood test diagnoses it — see a doctor if you notice these symptom patterns.",
    },
    "anemia": {
        "title": "Anemia (Low Hemoglobin)",
        "about": "Too few healthy red blood cells to carry oxygen — iron deficiency is the most common cause.",
        "symptoms": ["Fatigue and weakness", "Pale skin/nails", "Shortness of breath on exertion",
                     "Dizziness", "Cold hands and feet"],
        "self_care": ["Iron-rich foods: leafy greens, beans, jaggery, dates, meat",
                      "Vitamin C with meals (improves iron absorption)", "Avoid tea/coffee right after meals"],
        "see_doctor": "Get a CBC blood test; see a doctor for iron supplements and to find the underlying cause.",
    },
    "pcos": {
        "title": "PCOS (Polycystic Ovary Syndrome)",
        "about": "A hormonal condition in women causing irregular periods, and often weight gain and acne.",
        "symptoms": ["Irregular or missed periods", "Weight gain (especially belly)", "Acne/oily skin",
                     "Excess facial/body hair", "Hair thinning on scalp"],
        "self_care": ["Regular exercise + balanced low-refined-carb diet (5-10% weight loss helps a lot)",
                      "Good sleep routine", "Stress management"],
        "see_doctor": "See a gynecologist for hormone tests and a management plan, especially if periods are very irregular.",
    },
    "back pain": {
        "title": "Back Pain",
        "about": "Pain in the lower or upper back — usually from muscle strain, posture, or prolonged sitting.",
        "symptoms": ["Dull ache or sharp pain in the back", "Stiffness", "Pain worse after sitting long",
                     "Muscle spasm"],
        "self_care": ["Gentle stretching and short walks", "Hot/cold compress", "Good sitting posture with lumbar support",
                      "Avoid heavy lifting; bend with knees"],
        "see_doctor": "Urgent if pain shoots down the leg, or with numbness, weakness, fever, or loss of bladder control.",
    },
    "allergy": {
        "title": "Allergies",
        "about": "The immune system overreacting to harmless things like dust, pollen, or certain foods.",
        "symptoms": ["Sneezing, runny nose", "Itchy/watery eyes", "Skin rash or hives", "Itching"],
        "self_care": ["Identify and avoid triggers", "Keep windows closed during high-pollen days",
                      "Wash hands/face after being outdoors", "Antihistamines as directed by a pharmacist/doctor"],
        "see_doctor": "EMERGENCY if face/tongue swelling or trouble breathing (anaphylaxis) — call an ambulance.",
    },
    "insomnia": {
        "title": "Insomnia (Sleep Problems)",
        "about": "Difficulty falling or staying asleep, often linked to stress, screens, or irregular routines.",
        "symptoms": ["Trouble falling asleep", "Waking up at night repeatedly", "Daytime tiredness",
                     "Irritability and poor concentration"],
        "self_care": ["Fixed sleep/wake time (even weekends)", "No screens 1 hour before bed",
                      "No caffeine after evening", "Cool, dark, quiet bedroom", "Relaxation/deep breathing"],
        "see_doctor": "See a doctor if it persists beyond a few weeks or affects daily functioning.",
    },
    "constipation": {
        "title": "Constipation",
        "about": "Infrequent or hard-to-pass stools, usually from low fibre, low water, or inactivity.",
        "symptoms": ["Fewer than 3 stools a week", "Hard/dry stools", "Straining", "Bloating"],
        "self_care": ["More fibre: fruits, vegetables, whole grains", "Drink more water",
                      "Daily walk/exercise", "Don't ignore the urge to go"],
        "see_doctor": "See a doctor if lasting >2 weeks, with blood in stool, or unexplained weight loss.",
    },
    "diarrhea": {
        "title": "Diarrhea (Loose Motions)",
        "about": "Frequent loose, watery stools — usually from infection or food. Biggest risk is dehydration.",
        "symptoms": ["Loose/watery stools", "Stomach cramps", "Urgency", "Sometimes fever or nausea"],
        "self_care": ["ORS after every loose stool (most important!)", "Light food: khichdi, banana, curd-rice",
                      "Avoid oily/spicy food and milk for a day or two", "Wash hands well"],
        "see_doctor": "See a doctor if blood in stool, high fever, signs of dehydration, or lasting >2 days (sooner for children/elderly).",
    },
    "skin infection": {
        "title": "Common Skin Problems (Fungal/Rash)",
        "about": "Itchy rashes and fungal infections thrive in sweat and moisture — very common in humid weather.",
        "symptoms": ["Itchy red/ring-shaped patches (fungal)", "Rash", "Scaling or peeling skin",
                     "Itching worse with sweat"],
        "self_care": ["Keep the area clean and DRY", "Loose cotton clothes", "Don't share towels",
                      "Antifungal cream/powder as directed"],
        "see_doctor": "See a doctor if spreading, painful, oozing pus, or not improving in 1-2 weeks.",
    },
    "obesity": {
        "title": "Obesity / Weight Management",
        "about": "Excess body weight (BMI ≥ 30) that raises the risk of diabetes, heart disease, and joint problems.",
        "symptoms": ["BMI 30 or above", "Breathlessness on mild activity", "Joint pain", "Fatigue",
                     "Snoring/sleep issues"],
        "self_care": ["Small sustainable changes: smaller portions, fewer sugary drinks",
                      "150+ min brisk walking per week", "More protein and fibre, less refined carbs",
                      "7-8 hours sleep (poor sleep drives weight gain)"],
        "see_doctor": "A doctor can check for thyroid/hormonal causes and design a safe plan; even 5-10% weight loss brings big health gains.",
    },
}


# ─────────────────────────────────────────────
# SMART RETRIEVAL  —  TF-IDF cosine similarity (RAG-lite 🔎)
# Har topic ka ek "document" banta hai (title + about + symptoms + key),
# query usse compare hoti hai. Built lazily, ek hi baar.
# ─────────────────────────────────────────────
_TFIDF = None   # (vectorizer, matrix, [entries]) — cached singleton

# Itni similarity se kam = "match nahi mila" (random overlap avoid karne ke liye)
_MIN_SIMILARITY = 0.12


def _entry_document(key: str, entry: dict) -> str:
    """Ek topic ko searchable text-document me badlo.

    Title/key ko 3x repeat karte hain — TF-IDF me unka weight badh jata hai,
    taaki ek incidental shared word (jaise 'burning') galat topic na jeet le.
    """
    boosted = f"{key} {entry['title']} " * 3
    return " ".join([boosted, entry["about"], " ".join(entry["symptoms"]),
                     " ".join(entry["self_care"]), entry["see_doctor"]])


def _get_tfidf():
    """Build (once) and cache the TF-IDF index. None if sklearn missing."""
    global _TFIDF
    if _TFIDF is None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ImportError:
            _TFIDF = False   # sklearn nahi hai — substring fallback chalega
            return None
        entries = list(KNOWLEDGE_BASE.items())
        docs = [_entry_document(k, e) for k, e in entries]
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vec.fit_transform(docs)
        _TFIDF = (vec, matrix, [e for _, e in entries])
    return _TFIDF if _TFIDF else None


def lookup(query: str) -> dict | None:
    """
    Find the knowledge-base topic that best matches the query.

    1) Substring topic match (fast, exact — "diabetes kya hai" → diabetes)
    2) TF-IDF cosine similarity (fuzzy — "whistling sound while breathing
       at night" → asthma). Agar sklearn na ho to sirf step 1 chalta hai.
    """
    q = query.lower()
    # exact / substring topic match
    for key, entry in KNOWLEDGE_BASE.items():
        if key in q:
            return entry
    for entry in KNOWLEDGE_BASE.values():
        if entry["title"].lower() in q:
            return entry

    # fuzzy TF-IDF match
    index = _get_tfidf()
    if index:
        from sklearn.metrics.pairwise import cosine_similarity
        vec, matrix, entries = index
        sims = cosine_similarity(vec.transform([q]), matrix)[0]
        best = int(sims.argmax())
        if sims[best] >= _MIN_SIMILARITY:
            return entries[best]
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
    tests = [
        "what are diabetes symptoms",                       # substring hit
        "whistling sound while breathing at night",         # fuzzy → asthma
        "burning sensation while passing urine",            # fuzzy → UTI
        "can't sleep at night and tired all day",           # fuzzy → insomnia
    ]
    for t in tests:
        hit = lookup(t)
        print(f"❓ {t!r}  →  {'📖 ' + hit['title'] if hit else '❌ No match'}")
