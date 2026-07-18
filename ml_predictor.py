"""
╔══════════════════════════════════════════════════════════════╗
║   🧠  ml_predictor.py  —  Real ML models for MediMate AI      ║
║   Diabetes + Heart + Stroke + Breast-cancer risk (sklearn)    ║
╚══════════════════════════════════════════════════════════════╝

Ye file MediMate ko REAL machine learning deti hai — sirf API calls nahi! 💪

Ab CHAAR models train hote hain:

  1. 🍬 DIABETES RISK      — Pima Indians Diabetes dataset (768 patients)
  2. ❤️  HEART DISEASE      — UCI Cleveland Heart dataset (303 patients)
  3. 🧠 STROKE RISK        — Kaggle healthcare-stroke dataset (~5000 patients)
  4. 🎗️  BREAST CANCER      — Wisconsin dataset (sklearn built-in, 569 patients)

V2 UPGRADES (accuracy boost) 🚀
-------------------------------
  • Missing-value fix: Pima dataset me Glucose/BP/BMI ke "0" values
    actually MISSING hain — ab unhe median se impute karte hain.
  • Model selection: har disease ke liye 3 candidates compete karte hain
    (RandomForest vs GradientBoosting vs LogisticRegression) — 5-fold
    cross-validation ROC-AUC se best wala jeet-ta hai. 🏆
  • metrics.json me ab CV score + winning model ka naam bhi save hota hai.

HOW IT WORKS
------------
  • Pehli baar:  `python ml_predictor.py`  chalao
        → datasets download honge (internet chahiye, sirf ek baar;
          breast-cancer to sklearn me built-in hai — zero download!)
        → best models train + tune honge (~1-2 min)
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
STROKE_MODEL_FILE   = os.path.join(MODELS_DIR, "stroke_model.joblib")
BREAST_MODEL_FILE   = os.path.join(MODELS_DIR, "breast_model.joblib")
METRICS_FILE        = os.path.join(MODELS_DIR, "metrics.json")

# Public, well-known teaching datasets (CSV over HTTPS)
DIABETES_CSV_URL = "https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv"
HEART_CSV_URL    = "https://raw.githubusercontent.com/sharmaroshan/Heart-UCI-Dataset/master/heart.csv"
# Stroke dataset ke kai GitHub mirrors hain — pehla jo chale wahi use hota hai
STROKE_CSV_URLS = [
    "https://raw.githubusercontent.com/YuvrazError/Healthcare-Dataset-Analysis/main/healthcare-dataset-stroke-data.csv",
    "https://raw.githubusercontent.com/karavokyrismichail/Stroke-Prediction---Random-Forest/main/healthcare-dataset-stroke-data/healthcare-dataset-stroke-data.csv",
]

# Features each model expects (ORDER MATTERS — same as training!)
DIABETES_FEATURES = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
                     "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"]
HEART_FEATURES = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
                  "thalach", "exang", "oldpeak", "slope", "ca", "thal"]
STROKE_FEATURES = ["gender", "age", "hypertension", "heart_disease",
                   "avg_glucose_level", "bmi", "smoking_status"]
# Breast cancer: sklearn ke 30 me se 6 easy-to-read features
BREAST_FEATURES = ["mean radius", "mean texture", "mean perimeter",
                   "mean area", "mean concavity", "mean symmetry"]

# Pima dataset me in columns ka 0 == "value recorded nahi hui" (missing)
_DIABETES_ZERO_AS_MISSING = ["Glucose", "BloodPressure", "SkinThickness",
                             "Insulin", "BMI"]

_SMOKING_MAP = {"never smoked": 0.0, "unknown": 0.5, "formerly smoked": 1.0,
                "smokes": 2.0}


# ─────────────────────────────────────────────
# DATASET LOADERS  —  har disease ka apna loader (X, y return karta hai)
# ─────────────────────────────────────────────

def _load_diabetes():
    import numpy as np
    import pandas as pd
    df = pd.read_csv(DIABETES_CSV_URL)
    df.columns = [c.strip().lstrip("﻿") for c in df.columns]  # BOM fix
    # 0 → NaN in medically-impossible columns; pipeline ka imputer bharega
    df[_DIABETES_ZERO_AS_MISSING] = df[_DIABETES_ZERO_AS_MISSING].replace(0, np.nan)
    return df[DIABETES_FEATURES], df["Outcome"]


def _load_heart():
    import pandas as pd
    df = pd.read_csv(HEART_CSV_URL)
    df.columns = [c.strip().lstrip("﻿") for c in df.columns]
    return df[HEART_FEATURES], df["target"]


def _load_stroke():
    import numpy as np
    import pandas as pd
    df, last_err = None, None
    for url in STROKE_CSV_URLS:   # mirrors — jo pehla chale wahi sahi
        try:
            df = pd.read_csv(url)
            break
        except Exception as e:    # noqa: BLE001 — try next mirror
            last_err = e
    if df is None:
        raise RuntimeError(f"Stroke dataset download fail (sab mirrors): {last_err}")
    df.columns = [c.strip() for c in df.columns]
    df["gender"] = (df["gender"].str.lower() == "male").astype(int)
    df["smoking_status"] = (df["smoking_status"].str.lower()
                            .map(_SMOKING_MAP).fillna(0.5))
    df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce")  # "N/A" → NaN
    return df[STROKE_FEATURES], df["stroke"]


def _load_breast():
    # sklearn built-in — NO download needed! 🎉
    import pandas as pd
    from sklearn.datasets import load_breast_cancer
    data = load_breast_cancer(as_frame=True)
    X = data.frame[BREAST_FEATURES]
    y = 1 - data.target        # sklearn me 1=benign hai; hum 1=malignant chahte
    return X, y


# ─────────────────────────────────────────────
# TRAINING  —  run `python ml_predictor.py` once
# ─────────────────────────────────────────────

def _candidate_models():
    """3 candidate classifiers + chhote param grids — CV winner select hota hai."""
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    return [
        ("RandomForest",
         RandomForestClassifier(n_estimators=200, random_state=42),
         {"clf__max_depth": [4, 6, 8, None],
          "clf__class_weight": ["balanced", None]}),
        ("GradientBoosting",
         GradientBoostingClassifier(n_estimators=150, random_state=42),
         {"clf__learning_rate": [0.05, 0.1], "clf__max_depth": [2, 3]}),
        ("LogisticRegression",
         LogisticRegression(max_iter=2000),
         {"clf__C": [0.1, 1.0, 10.0],
          "clf__class_weight": ["balanced", None]}),
    ]


def train_models(verbose: bool = True) -> dict:
    """
    🏋️ Download datasets + best-model selection + save to disk.

    Har disease ke liye:
      impute → scale → 3 candidate models GridSearch (5-fold CV, ROC-AUC)
      → winner ke out-of-fold CV metrics report hote hain (chhote test-split
        se zyada stable) → winner FULL dataset pe refit hoke save hota hai
        (deployed model ko 100% data milta hai — standard practice 🏆).

    Returns a metrics dict, e.g.:
        {"diabetes": {"accuracy": 0.77, "roc_auc": 0.84,
                      "best_model": "LogisticRegression", ...}}
    """
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.model_selection import GridSearchCV, cross_val_predict
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    os.makedirs(MODELS_DIR, exist_ok=True)
    metrics = get_metrics()  # purane results rakho agar koi job fail ho jaye

    jobs = [
        # (name, loader, model_file)
        ("diabetes", _load_diabetes, DIABETES_MODEL_FILE),
        ("heart",    _load_heart,    HEART_MODEL_FILE),
        ("stroke",   _load_stroke,   STROKE_MODEL_FILE),
        ("breast",   _load_breast,   BREAST_MODEL_FILE),
    ]

    for name, loader, model_file in jobs:
        try:
            if verbose:
                print(f"\n📥 Loading {name} dataset…")
            X, y = loader()

            # 🏆 3 candidates compete — 5-fold CV ROC-AUC decide karta hai
            best = None   # (cv_auc, model_name, fitted_search)
            for clf_name, clf, grid in _candidate_models():
                pipe = Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("clf", clf),
                ])
                search = GridSearchCV(pipe, grid, cv=5, scoring="roc_auc",
                                      n_jobs=-1)
                search.fit(X, y)
                if verbose:
                    print(f"   🥊 {clf_name:<20} CV ROC-AUC: {search.best_score_:.3f}")
                if best is None or search.best_score_ > best[0]:
                    best = (search.best_score_, clf_name, search)

            cv_auc, best_name, search = best
            model = search.best_estimator_   # already refit on FULL data
            if verbose:
                print(f"   🏆 Winner: {best_name}")

            # Out-of-fold predictions = har patient tab predict hua jab wo
            # training me NAHI tha — pura dataset hi "unseen test" ban jata hai.
            oof_probs = cross_val_predict(model, X, y, cv=5, n_jobs=-1,
                                          method="predict_proba")[:, 1]
            oof_preds = (oof_probs >= 0.5).astype(int)
            acc = round(float(accuracy_score(y, oof_preds)), 3)
            auc = round(float(roc_auc_score(y, oof_probs)), 3)
            metrics[name] = {"accuracy": acc, "roc_auc": auc,
                             "cv_auc": round(float(cv_auc), 3),
                             "best_model": best_name,
                             "n_patients": len(X),
                             "positive_rate": round(float(y.mean()), 3)}

            joblib.dump(model, model_file)
            if verbose:
                print(f"✅ {name} model saved → {model_file}")
                print(f"   📊 accuracy: {acc*100:.1f}%   ROC-AUC: {auc}   (5-fold out-of-fold)")
        except Exception as e:   # noqa: BLE001 — ek fail ho to baaki chalte rahen
            if verbose:
                print(f"❌ {name} training fail: {e} — skip karke aage badh rahe hain.")

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
    """True if the two core trained models exist on disk."""
    return (HAS_ML_LIBS and os.path.exists(DIABETES_MODEL_FILE)
            and os.path.exists(HEART_MODEL_FILE))


def all_models_ready() -> bool:
    """True if ALL four models (incl. stroke + breast) exist."""
    return (models_ready() and os.path.exists(STROKE_MODEL_FILE)
            and os.path.exists(BREAST_MODEL_FILE))


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


def _risk_bucket(prob: float, high: float = 0.65,
                 moderate: float = 0.35) -> tuple[str, str]:
    """Probability → (label, emoji) — simple 3-level bucket.

    Thresholds per-condition adjust ho sakte hain: stroke dataset me sirf
    ~5% positive cases hain, isliye wahan 20% probability bhi base-rate se
    4x zyada hai — same cutoffs use karna misleading hota.
    """
    if prob >= high:
        return "HIGH", "🔴"
    if prob >= moderate:
        return "MODERATE", "🟡"
    return "LOW", "🟢"


def _model_line(name: str, dataset_desc: str) -> str:
    """metrics.json se winning model ka naam uthakar credit line banao."""
    m = get_metrics().get(name, {})
    algo = m.get("best_model", "ML model")
    return f"{algo} · {dataset_desc}"


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
        "model": _model_line("diabetes", "Pima Indians Diabetes dataset (768 patients)"),
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
        "model": _model_line("heart", "UCI Cleveland Heart dataset (303 patients)"),
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
# 🧠 STROKE RISK PREDICTION
# ─────────────────────────────────────────────

def predict_stroke(age: int, sex: str, avg_glucose: float, bmi: float,
                   hypertension: bool = False, heart_disease: bool = False,
                   smoking: str = "never") -> dict:
    """
    🧠 Stroke risk from lifestyle + basic health numbers.

    Args:
        age:            years
        sex:            "male" / "female"
        avg_glucose:    average glucose level (mg/dL)
        bmi:            body mass index
        hypertension:   diagnosed high BP?
        heart_disease:  existing heart disease?
        smoking:        "never" / "formerly" / "smokes"

    Returns: {"ok": True, "risk_percent": ..., "risk_level": ..., ...}
    """
    model = _load(STROKE_MODEL_FILE)
    if model is None:
        return {"ok": False, "error": NOT_READY_MSG}

    sex_num = 1 if str(sex).lower().startswith(("m", "1")) else 0
    s = str(smoking).lower()
    smoke_num = 2.0 if s.startswith("smok") or s == "yes" \
        else 1.0 if s.startswith(("former", "past", "quit")) else 0.0

    import pandas as pd
    row = pd.DataFrame([[sex_num, age, int(hypertension), int(heart_disease),
                         avg_glucose, bmi, smoke_num]], columns=STROKE_FEATURES)
    prob = float(model.predict_proba(row)[0][1])
    # Stroke base rate ~5% hai — 20%+ already bahut high hai
    level, emoji = _risk_bucket(prob, high=0.20, moderate=0.08)

    return {
        "ok": True,
        "condition": "Stroke",
        "risk_percent": round(prob * 100, 1),
        "risk_level": level,
        "emoji": emoji,
        "inputs": {"age": age, "sex": sex, "avg_glucose": avg_glucose,
                   "bmi": bmi, "hypertension": hypertension,
                   "heart_disease": heart_disease, "smoking": smoking},
        "advice": _stroke_advice(level, hypertension, smoke_num),
        "model": _model_line("stroke", "Kaggle healthcare-stroke dataset (~5000 patients)"),
        "disclaimer": "⚠️ Screening estimate only — NOT a diagnosis. Neurologist/physician consult zaroori hai.",
    }


def _stroke_advice(level: str, hypertension: bool, smoke_num: float) -> list[str]:
    advice = []
    if level == "HIGH":
        advice.append("Doctor se milkar BP, sugar aur lipid profile checkup karwao — stroke prevention planning zaroori hai.")
    elif level == "MODERATE":
        advice.append("BP aur sugar regular monitor karo, doctor ko risk factors batao.")
    else:
        advice.append("Risk low hai — healthy lifestyle continue rakho. 🧠")
    if hypertension:
        advice.append("Hypertension stroke ka #1 risk factor hai — BP medicines regular lo, kabhi skip mat karo.")
    if smoke_num >= 2:
        advice.append("Smoking chhodna stroke risk ~50% tak ghata deta hai — quit plan ke liye doctor se baat karo. 🚭")
    advice.append("FAST rule yaad rakho: Face drooping, Arm weakness, Speech difficulty → Time to call emergency!")
    return advice


# ─────────────────────────────────────────────
# 🎗️ BREAST CANCER SCREENING (tumor measurements)
# ─────────────────────────────────────────────

def predict_breast_cancer(mean_radius: float, mean_texture: float,
                          mean_perimeter: float, mean_area: float,
                          mean_concavity: float = 0.09,
                          mean_symmetry: float = 0.18) -> dict:
    """
    🎗️ Breast tumor malignancy screening from biopsy/imaging measurements.

    NOTE: Ye general public ke liye nahi — ye FNA/imaging report ke
    measurements pe kaam karta hai (mean radius/texture/perimeter/area).
    Risk = probability tumor MALIGNANT hai (benign nahi).

    Returns: {"ok": True, "risk_percent": ..., "risk_level": ..., ...}
    """
    model = _load(BREAST_MODEL_FILE)
    if model is None:
        return {"ok": False, "error": NOT_READY_MSG}

    import pandas as pd
    row = pd.DataFrame([[mean_radius, mean_texture, mean_perimeter, mean_area,
                         mean_concavity, mean_symmetry]], columns=BREAST_FEATURES)
    prob = float(model.predict_proba(row)[0][1])
    level, emoji = _risk_bucket(prob)

    return {
        "ok": True,
        "condition": "Breast Cancer (malignancy)",
        "risk_percent": round(prob * 100, 1),
        "risk_level": level,
        "emoji": emoji,
        "inputs": {"mean_radius": mean_radius, "mean_texture": mean_texture,
                   "mean_perimeter": mean_perimeter, "mean_area": mean_area},
        "advice": _breast_advice(level),
        "model": _model_line("breast", "Wisconsin Breast Cancer dataset (569 patients)"),
        "disclaimer": "⚠️ Screening estimate only — NOT a diagnosis. Biopsy report oncologist ko hi dikhao.",
    }


def _breast_advice(level: str) -> list[str]:
    advice = []
    if level == "HIGH":
        advice.append("Ye measurements malignant pattern se milte hain — oncologist se JALDI milo, biopsy/further imaging zaroori hai.")
    elif level == "MODERATE":
        advice.append("Results borderline hain — specialist se follow-up imaging discuss karo.")
    else:
        advice.append("Measurements benign pattern ke kareeb hain — phir bhi doctor se report confirm karwao.")
    advice.append("Regular self-examination + doctor-recommended screening schedule follow karo. 🎗️")
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
    print("🧠 MediMate ML trainer v2 shuru…")
    train_models()

    print("── Quick self-test ──")
    d = predict_diabetes(glucose=150, bmi=32, age=45)
    print(f"🍬 Diabetes  (glucose=150, bmi=32, age=45)  → {d['emoji']} {d['risk_level']} ({d['risk_percent']}%)")
    h = predict_heart(age=58, sex="male", resting_bp=145, cholesterol=250,
                      max_heart_rate=140, exercise_angina=True)
    print(f"❤️ Heart     (58M, bp=145, chol=250)        → {h['emoji']} {h['risk_level']} ({h['risk_percent']}%)")
    s = predict_stroke(age=68, sex="male", avg_glucose=210, bmi=33,
                       hypertension=True, smoking="smokes")
    if s["ok"]:
        print(f"🧠 Stroke    (68M, glucose=210, htn=yes)    → {s['emoji']} {s['risk_level']} ({s['risk_percent']}%)")
    b = predict_breast_cancer(mean_radius=20.5, mean_texture=25.0,
                              mean_perimeter=135.0, mean_area=1300.0,
                              mean_concavity=0.2, mean_symmetry=0.24)
    if b["ok"]:
        print(f"🎗️ Breast    (radius=20.5, area=1300)       → {b['emoji']} {b['risk_level']} ({b['risk_percent']}%)")
