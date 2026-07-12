"""
╔══════════════════════════════════════════════════════════════╗
║   nutrition.py  —  Food & diet tracker                        ║
╚══════════════════════════════════════════════════════════════╝

Tell it what you ate (e.g. "2 roti + 1 cup dal + 1 egg") and it returns
calories + protein + carbs + fat for the whole meal.

  • WITH a USDA_API_KEY  -> looks up almost any food online.
  • WITHOUT a key         -> uses a built-in table of common Indian &
                             everyday foods, so it STILL works offline.

Values are approximate, per typical serving. For education only.
"""

from __future__ import annotations
import re
import httpx
import config


# ─────────────────────────────────────────────
# OFFLINE FOOD TABLE  (per 1 typical serving)
# kcal, protein(g), carbs(g), fat(g)
# ─────────────────────────────────────────────
FOOD_TABLE = {
    # Indian staples
    "roti":        {"unit": "piece",  "kcal": 120, "protein": 3,  "carbs": 18, "fat": 3},
    "chapati":     {"unit": "piece",  "kcal": 120, "protein": 3,  "carbs": 18, "fat": 3},
    "naan":        {"unit": "piece",  "kcal": 260, "protein": 9,  "carbs": 48, "fat": 5},
    "paratha":     {"unit": "piece",  "kcal": 210, "protein": 5,  "carbs": 28, "fat": 9},
    "rice":        {"unit": "cup",    "kcal": 205, "protein": 4,  "carbs": 45, "fat": 0.5},
    "dal":         {"unit": "cup",    "kcal": 230, "protein": 18, "carbs": 40, "fat": 1},
    "rajma":       {"unit": "cup",    "kcal": 245, "protein": 15, "carbs": 43, "fat": 1},
    "chole":       {"unit": "cup",    "kcal": 270, "protein": 15, "carbs": 45, "fat": 4},
    "idli":        {"unit": "piece",  "kcal": 58,  "protein": 2,  "carbs": 12, "fat": 0.3},
    "dosa":        {"unit": "piece",  "kcal": 168, "protein": 4,  "carbs": 28, "fat": 4},
    "poha":        {"unit": "cup",    "kcal": 180, "protein": 4,  "carbs": 34, "fat": 3},
    "upma":        {"unit": "cup",    "kcal": 200, "protein": 5,  "carbs": 32, "fat": 6},
    "samosa":      {"unit": "piece",  "kcal": 260, "protein": 4,  "carbs": 30, "fat": 13},
    "paneer":      {"unit": "100g",   "kcal": 265, "protein": 18, "carbs": 6,  "fat": 20},
    "curd":        {"unit": "cup",    "kcal": 100, "protein": 9,  "carbs": 12, "fat": 3},
    "dahi":        {"unit": "cup",    "kcal": 100, "protein": 9,  "carbs": 12, "fat": 3},
    # Proteins
    "egg":         {"unit": "piece",  "kcal": 78,  "protein": 6,  "carbs": 1,  "fat": 5},
    "chicken":     {"unit": "100g",   "kcal": 165, "protein": 31, "carbs": 0,  "fat": 4},
    "fish":        {"unit": "100g",   "kcal": 206, "protein": 22, "carbs": 0,  "fat": 12},
    "milk":        {"unit": "cup",    "kcal": 150, "protein": 8,  "carbs": 12, "fat": 8},
    # Fruits
    "banana":      {"unit": "piece",  "kcal": 105, "protein": 1,  "carbs": 27, "fat": 0.3},
    "apple":       {"unit": "piece",  "kcal": 95,  "protein": 0,  "carbs": 25, "fat": 0.3},
    "orange":      {"unit": "piece",  "kcal": 62,  "protein": 1,  "carbs": 15, "fat": 0.2},
    "mango":       {"unit": "piece",  "kcal": 200, "protein": 3,  "carbs": 50, "fat": 1},
    # Everyday
    "bread":       {"unit": "slice",  "kcal": 70,  "protein": 3,  "carbs": 13, "fat": 1},
    "butter":      {"unit": "tbsp",   "kcal": 100, "protein": 0,  "carbs": 0,  "fat": 11},
    "tea":         {"unit": "cup",    "kcal": 40,  "protein": 1,  "carbs": 7,  "fat": 1},
    "coffee":      {"unit": "cup",    "kcal": 40,  "protein": 1,  "carbs": 6,  "fat": 1},
}


def _parse_meal(text: str) -> list[tuple[float, str]]:
    """Split 'chatty' meal text into (quantity, food) pairs.

    '2 roti + 1 cup dal and an egg' -> [(2,'roti'), (1,'dal'), (1,'egg')]
    """
    # break on +, comma, 'and', '&'
    parts = re.split(r"\+|,|\band\b|&", text.lower())
    items = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # find a leading number (default 1)
        m = re.match(r"(\d+(?:\.\d+)?)", part)
        qty = float(m.group(1)) if m else 1.0
        # strip number + common unit words to isolate the food name
        name = re.sub(r"^\d+(?:\.\d+)?", "", part)
        name = re.sub(r"\b(cup|cups|piece|pieces|slice|slices|bowl|glass|tbsp|tsp|g|grams?|of|a|an)\b",
                      "", name).strip()
        if name:
            items.append((qty, name))
    return items


def _match_offline(food: str) -> tuple[str, dict] | None:
    """Fuzzy-match a food name to the offline table."""
    food = food.strip().lower()
    if food in FOOD_TABLE:
        return food, FOOD_TABLE[food]
    for key, data in FOOD_TABLE.items():
        if key in food or food in key:
            return key, data
    return None


async def _usda_lookup(food: str) -> dict | None:
    """Look up one food via the USDA FoodData Central API (needs key)."""
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"query": food, "pageSize": 1, "api_key": config.USDA_API_KEY}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
        foods = data.get("foods", [])
        if not foods:
            return None
        nutrients = {n.get("nutrientName", ""): n.get("value", 0)
                     for n in foods[0].get("foodNutrients", [])}
        return {
            "kcal":    round(nutrients.get("Energy", 0)),
            "protein": round(nutrients.get("Protein", 0), 1),
            "carbs":   round(nutrients.get("Carbohydrate, by difference", 0), 1),
            "fat":     round(nutrients.get("Total lipid (fat)", 0), 1),
            "unit":    "100g",
        }
    except Exception:
        return None


async def analyze_meal(text: str) -> dict:
    """
    Main entry: analyze a whole meal string and return totals + breakdown.
    """
    items = _parse_meal(text)
    breakdown = []
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    unknown = []

    for qty, food in items:
        data, source = None, "offline"
        hit = _match_offline(food)
        if hit:
            _, data = hit
        elif config.HAS_NUTRITION:
            data = await _usda_lookup(food)
            source = "usda"

        if not data:
            unknown.append(food)
            continue

        entry = {
            "food": food,
            "qty": qty,
            "unit": data.get("unit", "serving"),
            "kcal": round(data["kcal"] * qty),
            "protein": round(data["protein"] * qty, 1),
            "carbs": round(data["carbs"] * qty, 1),
            "fat": round(data["fat"] * qty, 1),
            "source": source,
        }
        breakdown.append(entry)
        for k in totals:
            totals[k] += entry[k]

    totals = {k: round(v, 1) for k, v in totals.items()}
    return {"breakdown": breakdown, "totals": totals, "unknown": unknown}


def format_meal(result: dict) -> str:
    """Human-friendly meal summary."""
    if not result["breakdown"]:
        return ("Couldn't recognise any food. Try: '2 roti + 1 cup dal + 1 egg'.\n"
                "Add a USDA_API_KEY in .env to look up any food online.")
    lines = ["🍽️  Meal breakdown:"]
    for e in result["breakdown"]:
        lines.append(f"  • {e['qty']:g} {e['food']} — {e['kcal']} kcal "
                     f"(P {e['protein']}g / C {e['carbs']}g / F {e['fat']}g)")
    t = result["totals"]
    lines.append(f"\n📊 TOTAL: {t['kcal']:g} kcal  |  Protein {t['protein']:g}g  "
                 f"|  Carbs {t['carbs']:g}g  |  Fat {t['fat']:g}g")
    if result["unknown"]:
        lines.append(f"\n❔ Not recognised: {', '.join(result['unknown'])}")
    return "\n".join(lines)


def known_foods() -> list[str]:
    """List foods available offline."""
    return sorted(FOOD_TABLE.keys())


if __name__ == "__main__":
    import asyncio
    r = asyncio.run(analyze_meal("2 roti + 1 cup dal + 1 egg + 1 banana"))
    print(format_meal(r))
