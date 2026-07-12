"""
╔══════════════════════════════════════════════════════════════╗
║   calculators.py  —  Instant health calculators (no API!)     ║
╚══════════════════════════════════════════════════════════════╝

Pure-Python health math. These need NO internet and NO API key, so
they always work. Every function returns a small dict so the CLI and
the AI agent can both use them easily.

Includes:
    • BMI + category
    • BMR (Mifflin-St Jeor) + TDEE (daily calorie need)
    • Ideal body weight (Devine formula)
    • Daily water intake
    • Max heart rate + training zones
    • Estimated body-fat % (BMI method)
"""

from __future__ import annotations


# ─────────────────────────────────────────────
# BMI  —  Body Mass Index
# ─────────────────────────────────────────────
def bmi(weight_kg: float, height_cm: float) -> dict:
    """Body Mass Index and its WHO category."""
    height_m = height_cm / 100
    value = weight_kg / (height_m ** 2)
    value = round(value, 1)

    if value < 18.5:
        category, emoji, note = "Underweight", "⬇️", "Consider a nutrient-rich diet; consult a dietitian."
    elif value < 25:
        category, emoji, note = "Normal weight", "✅", "Great! Maintain your healthy lifestyle."
    elif value < 30:
        category, emoji, note = "Overweight", "⚠️", "Regular exercise & mindful eating can help."
    else:
        category, emoji, note = "Obese", "🔴", "Please consult a doctor for a personalized plan."

    return {"bmi": value, "category": category, "emoji": emoji, "note": note}


# ─────────────────────────────────────────────
# BMR  —  Basal Metabolic Rate (Mifflin-St Jeor)
# Calories your body burns at complete rest.
# ─────────────────────────────────────────────
def bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Calories burned at rest per day."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    value = base + 5 if sex.lower().startswith("m") else base - 161
    return round(value)


# Activity multipliers for TDEE
_ACTIVITY = {
    "sedentary":   1.2,    # little/no exercise
    "light":       1.375,  # 1-3 days/week
    "moderate":    1.55,   # 3-5 days/week
    "active":      1.725,  # 6-7 days/week
    "very_active": 1.9,    # hard exercise / physical job
}


def daily_calories(weight_kg: float, height_cm: float, age: int,
                   sex: str, activity: str = "moderate") -> dict:
    """Total daily calorie need (TDEE) + goal targets."""
    base = bmr(weight_kg, height_cm, age, sex)
    multiplier = _ACTIVITY.get(activity.lower(), 1.55)
    tdee = round(base * multiplier)
    return {
        "bmr": base,
        "maintenance": tdee,
        "mild_weight_loss": round(tdee - 300),   # ~0.25 kg/week
        "weight_loss": round(tdee - 500),         # ~0.5 kg/week
        "weight_gain": round(tdee + 400),
        "activity": activity,
    }


# ─────────────────────────────────────────────
# Ideal body weight  (Devine formula)
# ─────────────────────────────────────────────
def ideal_weight(height_cm: float, sex: str) -> dict:
    """Healthy weight range for a given height."""
    inches_over_5ft = max(0, (height_cm / 2.54) - 60)
    if sex.lower().startswith("m"):
        devine = 50 + 2.3 * inches_over_5ft
    else:
        devine = 45.5 + 2.3 * inches_over_5ft
    # Healthy BMI range (18.5–24.9) as a practical band
    h_m = height_cm / 100
    low, high = 18.5 * h_m ** 2, 24.9 * h_m ** 2
    return {
        "ideal_kg": round(devine, 1),
        "healthy_range_kg": (round(low, 1), round(high, 1)),
    }


# ─────────────────────────────────────────────
# Daily water intake
# ─────────────────────────────────────────────
def water_intake(weight_kg: float, activity_minutes: int = 30) -> dict:
    """Recommended daily water in litres (33 ml/kg + exercise bonus)."""
    base = weight_kg * 0.033
    bonus = (activity_minutes / 30) * 0.35  # ~350 ml per 30 min activity
    litres = round(base + bonus, 1)
    return {"litres": litres, "glasses": round(litres / 0.25)}  # 250 ml glasses


# ─────────────────────────────────────────────
# Heart rate zones
# ─────────────────────────────────────────────
def heart_rate_zones(age: int) -> dict:
    """Max heart rate and training zones (Karvonen simplified)."""
    max_hr = 220 - age
    return {
        "max_hr": max_hr,
        "fat_burn": (round(max_hr * 0.60), round(max_hr * 0.70)),
        "cardio":   (round(max_hr * 0.70), round(max_hr * 0.85)),
        "peak":     (round(max_hr * 0.85), max_hr),
    }


# ─────────────────────────────────────────────
# Estimated body fat %  (BMI method — rough guide)
# ─────────────────────────────────────────────
def body_fat(weight_kg: float, height_cm: float, age: int, sex: str) -> dict:
    """Rough body-fat % estimate from BMI (Deurenberg formula)."""
    b = bmi(weight_kg, height_cm)["bmi"]
    sex_factor = 1 if sex.lower().startswith("m") else 0
    bf = 1.20 * b + 0.23 * age - 10.8 * sex_factor - 5.4
    return {"body_fat_percent": round(bf, 1)}


# Quick self-test when run directly
if __name__ == "__main__":
    print("BMI:", bmi(70, 175))
    print("Calories:", daily_calories(70, 175, 25, "male", "moderate"))
    print("Ideal weight:", ideal_weight(175, "male"))
    print("Water:", water_intake(70, 45))
    print("HR zones:", heart_rate_zones(25))
    print("Body fat:", body_fat(70, 175, 25, "male"))
