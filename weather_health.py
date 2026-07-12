"""
╔══════════════════════════════════════════════════════════════╗
║   weather_health.py  —  Weather & Air-Quality health alerts   ║
╚══════════════════════════════════════════════════════════════╝

Gives health advice based on the LIVE weather and air quality (AQI) of
your city:

  • "AQI is 180 (Unhealthy) — wear a mask, avoid outdoor exercise."
  • "38°C heat — drink extra water, avoid the afternoon sun."

  WITH an OPENWEATHER_API_KEY -> real live data for any city.
  WITHOUT a key                -> a clear message + general seasonal tips.

Free key: https://openweathermap.org/api
"""

from __future__ import annotations
import httpx
import config


# AQI scale (OpenWeather returns 1-5) -> label + health advice
_AQI_LEVELS = {
    1: ("Good", "🟢", "Air quality is great. Enjoy outdoor activities!"),
    2: ("Fair", "🟡", "Air is acceptable. Very sensitive people should watch symptoms."),
    3: ("Moderate", "🟠", "Sensitive groups (asthma, heart, elderly, kids) should limit long outdoor exertion."),
    4: ("Poor", "🔴", "Wear a mask outdoors. Avoid outdoor exercise. Keep windows closed."),
    5: ("Very Poor", "🟣", "Stay indoors if possible. Use a mask/air purifier. Asthma patients: keep inhaler handy."),
}


async def _geocode(city: str) -> tuple[float, float] | None:
    """City name -> (lat, lon) via OpenWeather geocoding."""
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": config.OPENWEATHER_API_KEY}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            data = (await client.get(url, params=params)).json()
        if data:
            return data[0]["lat"], data[0]["lon"]
    except Exception:
        pass
    return None


async def get_weather_health(city: str | None = None) -> dict:
    """
    Return weather + AQI + health advice for a city.
    Falls back to a friendly offline message if no key is set.
    """
    city = city or config.DEFAULT_CITY

    if not config.HAS_WEATHER:
        return {
            "available": False,
            "city": city,
            "message": ("🌤️ Live weather needs an OPENWEATHER_API_KEY in .env "
                        "(free at openweathermap.org).\n"
                        "General tips: stay hydrated, dress for the season, and on "
                        "hazy/polluted days wear a mask and limit outdoor exercise."),
        }

    coords = await _geocode(city)
    if not coords:
        return {"available": False, "city": city, "message": f"Couldn't find city '{city}'."}
    lat, lon = coords

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            w = (await client.get("https://api.openweathermap.org/data/2.5/weather",
                 params={"lat": lat, "lon": lon, "units": "metric",
                         "appid": config.OPENWEATHER_API_KEY})).json()
            a = (await client.get("http://api.openweathermap.org/data/2.5/air_pollution",
                 params={"lat": lat, "lon": lon, "appid": config.OPENWEATHER_API_KEY})).json()
    except Exception as e:
        return {"available": False, "city": city, "message": f"Weather fetch failed: {e}"}

    temp = w.get("main", {}).get("temp")
    feels = w.get("main", {}).get("feels_like")
    humidity = w.get("main", {}).get("humidity")
    desc = (w.get("weather", [{}])[0].get("description", "")).title()

    aqi_index = a.get("list", [{}])[0].get("main", {}).get("aqi", 0)
    aqi_label, aqi_emoji, aqi_advice = _AQI_LEVELS.get(aqi_index, ("Unknown", "⚪", ""))
    pm25 = a.get("list", [{}])[0].get("components", {}).get("pm2_5")

    # Build weather-based health tips
    tips = [aqi_advice] if aqi_advice else []
    if temp is not None:
        if temp >= 35:
            tips.append("🥵 It's hot — drink extra water, avoid the midday sun, watch for dizziness (heat stroke).")
        elif temp <= 5:
            tips.append("🥶 It's cold — dress warm; cold can trigger asthma & raise blood pressure.")
    if humidity and humidity >= 80:
        tips.append("💧 High humidity — pace yourself; heat feels worse and dehydration is easy.")

    return {
        "available": True,
        "city": city,
        "temp": temp, "feels_like": feels, "humidity": humidity, "description": desc,
        "aqi_index": aqi_index, "aqi_label": aqi_label, "aqi_emoji": aqi_emoji, "pm25": pm25,
        "tips": tips,
    }


def format_weather(data: dict) -> str:
    """Human-friendly weather + health summary."""
    if not data.get("available"):
        return data.get("message", "Weather unavailable.")
    lines = [
        f"📍 {data['city']} — {data['description']}",
        f"🌡️  Temp: {data['temp']}°C (feels {data['feels_like']}°C)   💧 Humidity: {data['humidity']}%",
        f"{data['aqi_emoji']} Air Quality: {data['aqi_label']} (AQI {data['aqi_index']}/5"
        + (f", PM2.5 {data['pm25']})" if data.get("pm25") is not None else ")"),
        "",
        "🩺 Health tips for today:",
    ]
    lines += [f"  • {t}" for t in data["tips"]] or ["  • Have a healthy day!"]
    return "\n".join(lines)


if __name__ == "__main__":
    import asyncio
    print(format_weather(asyncio.run(get_weather_health("Delhi"))))
