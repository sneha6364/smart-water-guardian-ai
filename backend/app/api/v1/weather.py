from fastapi import APIRouter, HTTPException, Query
from app.services.weather import get_weather_forecast

router = APIRouter()


@router.get("/forecast")
async def weather_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """Fetch 7-day weather forecast for the given coordinates from Open-Meteo."""
    data = await get_weather_forecast(latitude, longitude)
    return data
