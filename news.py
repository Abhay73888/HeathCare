"""
╔══════════════════════════════════════════════════════════════╗
║   news.py  —  Latest health news feed                         ║
╚══════════════════════════════════════════════════════════════╝

Fetches recent health headlines so the assistant can stay current.

  WITH a NEWSAPI_KEY -> live top health headlines.
  WITHOUT a key       -> a friendly message + evergreen health tips.

Free key: https://newsapi.org/register
"""

from __future__ import annotations
import httpx
import config


# Shown in offline mode so the feature is never empty
EVERGREEN_TIPS = [
    "Walking 30 minutes a day lowers heart-disease risk significantly.",
    "7-9 hours of sleep boosts immunity and mental health.",
    "Drinking water before meals aids digestion and weight control.",
    "Washing hands well is still one of the best ways to prevent infection.",
    "Reducing added sugar helps prevent type-2 diabetes.",
]


async def get_health_news(topic: str = "health", limit: int = 5) -> dict:
    """Return recent health headlines (or offline tips if no key)."""
    if not config.HAS_NEWS:
        return {
            "available": False,
            "message": ("📰 Live health news needs a NEWSAPI_KEY in .env "
                        "(free at newsapi.org)."),
            "tips": EVERGREEN_TIPS,
        }

    url = "https://newsapi.org/v2/top-headlines"
    params = {"category": "health", "language": "en", "pageSize": limit,
              "apiKey": config.NEWSAPI_KEY}
    if topic and topic != "health":
        url = "https://newsapi.org/v2/everything"
        params = {"q": f"{topic} health", "language": "en", "pageSize": limit,
                  "sortBy": "publishedAt", "apiKey": config.NEWSAPI_KEY}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            data = (await client.get(url, params=params)).json()
        articles = [
            {"title": a.get("title", ""), "source": a.get("source", {}).get("name", ""),
             "url": a.get("url", "")}
            for a in data.get("articles", [])[:limit]
        ]
        return {"available": True, "articles": articles}
    except Exception as e:
        return {"available": False, "message": f"News fetch failed: {e}", "tips": EVERGREEN_TIPS}


def format_news(data: dict) -> str:
    """Human-friendly news summary."""
    if data.get("available"):
        if not data["articles"]:
            return "No health headlines right now."
        lines = ["📰 Latest health headlines:\n"]
        for i, a in enumerate(data["articles"], 1):
            lines.append(f"  {i}. {a['title']}  ({a['source']})")
            if a["url"]:
                lines.append(f"     {a['url']}")
        return "\n".join(lines)

    lines = [data.get("message", ""), "", "💡 Meanwhile, some evergreen health tips:"]
    lines += [f"  • {t}" for t in data.get("tips", EVERGREEN_TIPS)]
    return "\n".join(lines)


if __name__ == "__main__":
    import asyncio
    print(format_news(asyncio.run(get_health_news())))
