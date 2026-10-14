"""
Open-Meteo weather integration service.
Fetches forecasts for given farm coordinates.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Open-Meteo variables requested
DAILY_VARIABLES = [
    "precipitation_sum",
    "precipitation_probability_max",
    "et0_fao_evapotranspiration",
    "temperature_2m_max",
    "temperature_2m_min",
    "windspeed_10m_max",
    "weathercode",
]

FORECAST_DAYS = 7

DEMO_WEATHER = {
    "source": "demo",
    "latitude": 13.08,
    "longitude": 77.59,
    "timezone": "Asia/Kolkata",
    "forecast_days": 7,
    "fetched_at": None,
    "daily": {
        "time": ["2024-06-01", "2024-06-02", "2024-06-03", "2024-06-04",
                 "2024-06-05", "2024-06-06", "2024-06-07"],
        "precipitation_sum": [0.0, 0.0, 12.5, 8.0, 0.5, 0.0, 0.0],
        "precipitation_probability_max": [10, 15, 75, 65, 30, 10, 5],
        "et0_fao_evapotranspiration": [4.8, 5.1, 3.2, 3.8, 4.5, 5.0, 5.2],
        "temperature_2m_max": [34, 35, 30, 29, 32, 35, 36],
        "temperature_2m_min": [22, 23, 20, 20, 21, 22, 23],
    },
    "summary": {
        "total_rain_mm": 21.0,
        "max_rain_probability_pct": 75,
        "avg_et0_mm_day": 4.5,
        "next_rain_day": "2024-06-03",
    },
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(httpx.TransportError),
    reraise=True,
)
async def _fetch_raw(url: str, params: Dict) -> Dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def get_weather_forecast(
    latitude: float,
    longitude: float,
) -> Dict[str, Any]:
    """
    Fetch 7-day weather forecast from Open-Meteo for given coordinates.
    Returns a normalised dict. Falls back to demo data on any error.
    """
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        logger.warning("Invalid coordinates: lat=%s lon=%s", latitude, longitude)
        return {**DEMO_WEATHER, "error": "Invalid coordinates — demo data shown"}

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "auto",
        "forecast_days": FORECAST_DAYS,
    }

    try:
        data = await _fetch_raw(settings.WEATHER_API_BASE_URL, params)
        return _normalise_weather(data)
    except httpx.HTTPStatusError as exc:
        logger.error("Open-Meteo HTTP error: %s", exc)
        return {**DEMO_WEATHER, "error": f"Weather service unavailable ({exc.response.status_code}) — demo data shown"}
    except Exception as exc:
        logger.error("Open-Meteo fetch failed: %s", exc)
        return {**DEMO_WEATHER, "error": "Weather service unreachable — demo data shown"}


def _normalise_weather(raw: Dict) -> Dict[str, Any]:
    """Convert raw Open-Meteo JSON into a clean dict used throughout the app."""
    daily = raw.get("daily", {})
    times = daily.get("time", [])
    rain = daily.get("precipitation_sum", [])
    prob = daily.get("precipitation_probability_max", [])
    et0 = daily.get("et0_fao_evapotranspiration", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])

    total_rain = sum(r for r in rain if r is not None)
    max_prob = max((p for p in prob if p is not None), default=0)
    avg_et0 = (
        sum(e for e in et0 if e is not None) / len([e for e in et0 if e is not None])
        if any(e is not None for e in et0) else None
    )

    next_rain_day = None
    for i, (p, r) in enumerate(zip(prob, rain)):
        if (p or 0) >= 60 and (r or 0) > 0:
            next_rain_day = times[i] if i < len(times) else None
            break

    return {
        "source": "open-meteo",
        "latitude": raw.get("latitude"),
        "longitude": raw.get("longitude"),
        "timezone": raw.get("timezone"),
        "forecast_days": len(times),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "daily": {
            "time": times,
            "precipitation_sum": rain,
            "precipitation_probability_max": prob,
            "et0_fao_evapotranspiration": et0,
            "temperature_2m_max": tmax,
            "temperature_2m_min": tmin,
        },
        "summary": {
            "total_rain_mm": round(total_rain, 1),
            "max_rain_probability_pct": max_prob,
            "avg_et0_mm_day": round(avg_et0, 2) if avg_et0 is not None else None,
            "next_rain_day": next_rain_day,
        },
    }


def weather_to_irrigation_inputs(weather: Dict, days: int = 3) -> Dict[str, Any]:
    """
    Extract irrigation-relevant values from weather dict for the given forecast window.
    Returns a dict suitable for populating IrrigationInputs.
    """
    daily = weather.get("daily", {})
    et0_list = daily.get("et0_fao_evapotranspiration", [])
    rain_list = daily.get("precipitation_sum", [])
    prob_list = daily.get("precipitation_probability_max", [])

    window_et0 = [e for e in et0_list[:days] if e is not None]
    window_rain = [r for r in rain_list[:days] if r is not None]
    window_prob = [p for p in prob_list[:days] if p is not None]

    avg_et0 = sum(window_et0) / len(window_et0) if window_et0 else None
    total_rain = sum(window_rain)
    max_prob = max(window_prob) if window_prob else None

    return {
        "et0_mm_per_day": avg_et0,
        "forecast_rain_mm": total_rain,
        "rain_probability_pct": max_prob,
        "forecast_days": days,
    }
