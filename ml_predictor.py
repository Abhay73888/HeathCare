"""
╔══════════════════════════════════════════════════════════════╗
║   🧠  ml_predictor.py  —  Real ML models for MediMate AI      ║
║   Diabetes risk + Heart disease risk (scikit-learn)           ║
╚══════════════════════════════════════════════════════════════╝

Ye file MediMate ko REAL machine learning deti hai — sirf API calls nahi! 💪

Do models train hote hain:

  1. 🍬 DIABETES RISK   — Pima Indians Diabetes dataset (768 patients)
  2. ❤️  HEART DISEASE   — UCI Cleveland Heart dataset (303 patients)

HOW IT WORKS
------------
  • Pehli baar:  `python ml_predictor.py`  chalao
        → datasets download honge (internet chahiye, sirf ek baar)
        → RandomForest models train honge (~5 seconds)
        → models `ml_models/` folder me save ho jayenge (joblib)
  • Uske baad:  app offline bhi predict kar sakta hai — model file
    se load hota hai, internet ki zaroorat NahI. 📴✅

  • Agar models trained nahi hain to functions ek friendly message
    dete hain (crash NAHI karte) — same graceful-fallback style
    jaise baaki MediMate features.

⚠️ DISCLAIMER: Ye educational risk-screening hai, medical diagnosis
NAHI. Har result ke saath "doctor se milo" wala disclaimer hai.
"""

import os
import json

import config  # noqa: F401  (UTF-8 console fix on Windows + shared settings)

# ── Lazy/optional imports — bina scikit-learn ke bhi app crash na ho ──
try:
    import joblib
    HAS_ML_LIBS = True
except ImportError:      # scikit-learn/joblib installed nahi hai
    HAS_ML_LIBS = False

# ─────────────────────────────────────────────
# PATHS & DATASET URLS
# ─────────────────────────────────────────────
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_models")

DIABETES_MODEL_FILE = os.path.join(MODELS_DIR, "diabetes_model.joblib")
HEART_MODEL_FILE    = os.path.join(MODELS_DIR, "heart_model.joblib")
METRICS_FILE        = os.path.join(MODELS_DIR, "metrics.json")

# Public, well-known teaching datasets (CSV over HTTPS)
DIABETES_CSV_URL = "https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv"
HEART_CSV_URL    = "https://raw.githubusercontent.com/sharmaroshan/Heart-UCI-Dataset/master/heart.csv"

# Features each model expects (ORDER MATTERS — same as training!)
DIABETES_FEATURES = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
                     "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"]
HEART_FEATURES = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
                  "thalach", "exang", "oldpeak", "slope", "ca", "thal"]


# ─────────────────────────────────────────────
# TRAINING  —  run `python ml_predictor.py` once
# ─────────────────────────────────────────────

def train_models(verbose: bool = True) -> dict:
    """
    🏋️ Download datasets + train both models + save to disk.

    Returns a metrics dict, e.g.:
        {"diabetes": {"accuracy": 0.75, ...}, "heart": {"accuracy": 0.85, ...}}
    """
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    os.makedirs(MODELS_DIR, exist_ok=True)
    metrics = {}

    jobs = [
        # (name, url, target_column, feature_list, model_file)
        ("diabetes", DIABETES_CSV_URL, "Outcome", DIABETES_FEATURES, DIABETES_MODEL_FILE),
        ("heart",    HEART_CSV_URL,    "target",  HEART_FEATURES,    HEART_MODEL_FILE),
    ]

    for name, url, target, features, model_file in jobs:
        if verbose:
            print(f"\n📥 Downloading {name} dataset…")
        df = pd.read_csv(url)
        df.columns = [c.strip().lstrip("﻿") for c in df.columns]  # BOM fix

        X, y = df[features], df[target]

        # 80/20 split — stratify rakha taaki dono classes balanced rahen
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y)

        # Pipeline = scaler + RandomForest (scaling RF ko zaroori nahi,
        # par pipeline rakhne se future me model swap karna easy hai)
        model = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=200, max_depth=6,
                                           random_state=42, class_weight="balanced")),
        ])

        if verbose:
            print(f"🏋️  Training {name} model on {len(X_train)} patients…")
        model.fit(X_train, y_train)

        # Evaluate on the 20% the model has NEVER seen
        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1]
        acc = round(float(accuracy_score(y_test, preds)), 3)
        auc = round(float(roc_auc_score(y_test, probs)), 3)
        metrics[name] = {"accuracy": acc, "roc_auc": auc,
                         "train_size": len(X_train), "test_size": len(X_test)}

        joblib.dump(model, model_file)
        if verbose:
            print(f"✅ {name} model saved → {model_file}")
            print(f"   📊 accuracy: {acc*100:.1f}%   ROC-AUC: {auc}")

    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    if verbose:
        print("\n🎉 Done! Models ready — ab app offline bhi predict karega.\n")
    return metrics


# ─────────────────────────────────────────────
# LOADING  —  cached singletons (train once, load once)
# ─────────────────────────────────────────────
_CACHE: dict = {}


def _load(model_file: str):
    """Load a saved model from disk (cached). None if missing/unavailable."""
    if not HAS_ML_LIBS or not os.path.exists(model_file):
        return None
    if model_file not in _CACHE:
        _CACHE[model_file] = joblib.load(model_file)
    return _CACHE[model_file]


def models_ready() -> bool:
    """True if both trained models exist on disk."""
    return (HAS_ML_LIBS and os.path.exists(DIABETES_MODEL_FILE)
            and os.path.exists(HEART_MODEL_FILE))


def get_metrics() -> dict:
    """Saved training metrics (accuracy etc.) — {} if not trained yet."""
    try:
        with open(METRICS_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


NOT_READY_MSG = ("🤖 ML models abhi trained nahi hain. Ek baar terminal me "
                 "`python ml_predictor.py` chalao (internet chahiye), phir ye "
                 "feature offline bhi kaam karega.")


def _risk_bucket(prob: float) -> tuple[str, str]:
    """Probability → (label, emoji) — simple 3-level bucket."""
    if prob >= 0.65:
        return "HIGH", "🔴"
    if prob >= 0.35:
        return "MODERATE", "🟡"
    return "LOW", "🟢"


# ─────────────────────────────────────────────
# 🍬 DIABETES RISK PREDICTION
# ─────────────────────────────────────────────

def predict_diabetes(glucose: float, bmi: float, age: int,
                     blood_pressure: float = 72, pregnancies: int = 0,
                     skin_thickness: float = 20, insulin: float = 80,
                     pedigree: float = 0.4) -> dict:
    """
    🍬 Diabetes risk from basic health numbers.

    Required: glucose (mg/dL, fasting), bmi, age.
    Baaki params optional — dataset ke median jaise sensible defaults hain.

    Returns: {"ok": True, "risk_percent": 71.2, "risk_level": "HIGH", ...}
    """
    model = _load(DIABETES_MODEL_FILE)
    if model is None:
        return {"ok": False, "error": NOT_READY_MSG}

    import pandas as pd
    row = pd.DataFrame([[pregnancies, glucose, blood_pressure, skin_thickness,
                         insulin, bmi, pedigree, age]], columns=DIABETES_FEATURES)
    prob = float(model.predict_proba(row)[0][1])
    level, emoji = _risk_bucket(prob)

    return {
        "ok": True,
        "condition": "Type-2 Diabetes",
        "risk_percent": round(prob * 100, 1),
        "risk_level": level,
        "emoji": emoji,
        "inputs": {"glucose": glucose, "bmi": bmi, "age": age,
                   "blood_pressure": blood_pressure},
        "advice": _diabetes_advice(level, glucose, bmi),
        "model": "RandomForest · Pima Indians Diabetes dataset (768 patients)",
        "disclaimer": "⚠️ Screening estimate only — NOT a diagnosis. Blood test + doctor consult zaroori hai.",
    }


def _diabetes_advice(level: str, glucose: float, bmi: float) -> list[str]:
    """Simple, safe lifestyle advice based on the risk level."""
    advice = []
    if level == "HIGH":
        advice.append("Jaldi hi doctor se milkar HbA1c / fasting sugar test karwao.")
    elif level == "MODERATE":
        advice.append("Agle health checkup me blood sugar test zaroor karwao.")
    else:
        advice.append("Risk low hai — healthy routine maintain karo. 💪")
    if glucose >= 126:
        advice.append(f"Fasting glucose {glucose} mg/dL diabetic range me hai (≥126) — doctor se confirm karo.")
    elif glucose >= 100:
        advice.append(f"Fasting glucose {glucose} mg/dL pre-diabetic range me hai (100–125).")
    if bmi >= 25:
        advice.append(f"BMI {bmi} overweight range me hai — 5-7% weight loss se diabetes risk kaafi ghat jata hai.")
    advice.append("Daily 30 min walk + kam sugar/refined carbs = best prevention.")
    return advice


# ─────────────────────────────────────────────
# ❤️ HEART DISEASE RISK PREDICTION
# ─────────────────────────────────────────────

def predict_heart(age: int, sex: str, resting_bp: float, cholesterol: float,
                  max_heart_rate: float, chest_pain_type: int = 0,
                  fasting_bs_high: bool = False, exercise_angina: bool = False) -> dict:
    """
    ❤️ Heart disease risk from common checkup numbers.

    Args:
        age:              years
        sex:              "male" / "female"
        resting_bp:       resting blood pressure (mm Hg)
        cholesterol:      serum cholesterol (mg/dL)
        max_heart_rate:   max heart rate achieved (thalach)
        chest_pain_type:  0 = typical angina, 1 = atypical, 2 = non-anginal, 3 = none/asymptomatic
        fasting_bs_high:  fasting blood sugar > 120 mg/dL?
        exercise_angina:  chest pain during exercise?

    Returns: {"ok": True, "risk_percent": ..., "risk_level": ..., ...}
    """
    model = _load(HEART_MODEL_FILE)
    if model is None:
        return {"ok": False, "error": NOT_READY_MSG}

    sex_num = 1 if str(sex).lower().startswith(("m", "1")) else 0
    # Dataset ke less-common clinical fields ke liye median-ish defaults:
    restecg, oldpeak, slope, ca, thal = 1, 1.0, 1, 0, 2

    import pandas as pd
    row = pd.DataFrame([[age, sex_num, chest_pain_type, resting_bp, cholesterol,
                         int(fasting_bs_high), restecg, max_heart_rate,
                         int(exercise_angina), oldpeak, slope, ca, thal]],
                       columns=HEART_FEATURES)
    prob = float(model.predict_proba(row)[0][1])
    level, emoji = _risk_bucket(prob)

    return {
        "ok": True,
        "condition": "Heart Disease",
        "risk_percent": round(prob * 100, 1),
        "risk_level": level,
        "emoji": emoji,
        "inputs": {"age": age, "sex": sex, "resting_bp": resting_bp,
                   "cholesterol": cholesterol, "max_heart_rate": max_heart_rate},
        "advice": _heart_advice(level, resting_bp, cholesterol),
        "model": "RandomForest · UCI Cleveland Heart dataset (303 patients)",
        "disclaimer": "⚠️ Screening estimate only — NOT a diagnosis. ECG/lipid profile + cardiologist consult zaroori hai.",
    }


def _heart_advice(level: str, bp: float, chol: float) -> list[str]:
    advice = []
    if level == "HIGH":
        advice.append("Cardiologist se milkar ECG + lipid profile karwana best rahega.")
    elif level == "MODERATE":
        advice.append("Regular BP + cholesterol monitoring shuru karo, doctor ko batao.")
    else:
        advice.append("Risk low hai — heart-healthy habits continue rakho. ❤️")
    if bp >= 140:
        advice.append(f"Resting BP {bp} high hai (≥140) — hypertension check karwao.")
    if chol >= 240:
        advice.append(f"Cholesterol {chol} mg/dL high hai (≥240) — diet me oil/fried kam karo.")
    advice.append("Daily exercise, no smoking, kam namak — heart ke best friends. 🏃")
    return advice


# ─────────────────────────────────────────────
# FORMATTER  —  dict → chat-friendly text (for the LLM tool / CLI)
# ─────────────────────────────────────────────

def format_prediction(result: dict) -> str:
    """Turn a prediction dict into a readable chat message."""
    if not result.get("ok"):
        return result.get("error", "Prediction failed.")
    lines = [
        f"{result['emoji']} **{result['condition']} risk: {result['risk_level']}** "
        f"(~{result['risk_percent']}% probability)",
        "",
        "**Advice:**",
    ]
    lines += [f"- {a}" for a in result["advice"]]
    lines += ["", f"_Model: {result['model']}_", result["disclaimer"]]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# RUN DIRECTLY  →  train + quick self-test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("🧠 MediMate ML trainer shuru…")
    train_models()

    print("── Quick self-test ──")
    d = predict_diabetes(glucose=150, bmi=32, age=45)
    print(f"🍬 Diabetes  (glucose=150, bmi=32, age=45)  → {d['emoji']} {d['risk_level']} ({d['risk_percent']}%)")
    h = predict_heart(age=58, sex="male", resting_bp=145, cholesterol=250,
                      max_heart_rate=140, exercise_angina=True)
    print(f"❤️ Heart     (58M, bp=145, chol=250)        → {h['emoji']} {h['risk_level']} ({h['risk_percent']}%)")
