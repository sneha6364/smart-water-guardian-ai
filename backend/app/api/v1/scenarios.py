"""What-if scenario simulator endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Farm, CropRecord, WaterStorageRecord, ScenarioSimulation
from app.schemas import ScenarioRequest, ScenarioResponse, ScenarioResult
from app.services.weather import get_weather_forecast, weather_to_irrigation_inputs
from app.services.irrigation_engine import IrrigationInputs, run_what_if_scenarios
from app.services.groq_service import explain_scenario_comparison

router = APIRouter()


@router.post("/", response_model=ScenarioResponse, status_code=201)
async def run_scenarios(req: ScenarioRequest, db: AsyncSession = Depends(get_db)):
    farm = await db.get(Farm, req.farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    crop_result = await db.execute(
        select(CropRecord)
        .where(CropRecord.farm_id == farm.id, CropRecord.is_active == True)
        .order_by(CropRecord.id.desc())
        .limit(1)
    )
    crop = crop_result.scalars().first()

    water_result = await db.execute(
        select(WaterStorageRecord)
        .where(WaterStorageRecord.farm_id == farm.id)
        .order_by(WaterStorageRecord.recorded_at.desc())
        .limit(1)
    )
    water_record = water_result.scalars().first()
    storage = water_record.storage_litres if water_record else farm.water_storage_litres

    weather_data = {}
    if farm.latitude and farm.longitude:
        weather_data = await get_weather_forecast(farm.latitude, farm.longitude)

    weather_inputs = weather_to_irrigation_inputs(weather_data, days=3)

    base_inputs = IrrigationInputs(
        area_hectares=farm.area_hectares,
        irrigation_method=farm.irrigation_method,
        water_storage_litres=storage,
        crop_type=crop.crop_type if crop else None,
        growth_stage=crop.growth_stage if crop else None,
        soil_moisture_pct=crop.soil_moisture_pct if crop else None,
        et0_mm_per_day=weather_inputs.get("et0_mm_per_day"),
        forecast_rain_mm=weather_inputs.get("forecast_rain_mm"),
        rain_probability_pct=weather_inputs.get("rain_probability_pct"),
        forecast_days=weather_inputs.get("forecast_days", 3),
    )

    raw_scenarios = run_what_if_scenarios(base_inputs)

    farm_info = {
        "farm_name": farm.name,
        "area_hectares": farm.area_hectares,
        "crop_type": crop.crop_type if crop else None,
        "growth_stage": crop.growth_stage if crop else None,
        "water_storage_litres": storage,
    }

    ai_comparison = await explain_scenario_comparison(raw_scenarios, farm_info)

    # Persist
    sim = ScenarioSimulation(
        farm_id=farm.id,
        scenario_name="What-If Simulation",
        inputs=farm_info,
        results=raw_scenarios,
    )
    db.add(sim)
    await db.commit()

    scenario_results = [
        ScenarioResult(
            scenario_name=s["scenario_name"],
            description=s["description"],
            estimated_water_use_litres=s.get("estimated_water_use_litres"),
            remaining_storage_litres=s.get("remaining_storage_litres"),
            days_remaining=s.get("days_remaining"),
            recommendation=s.get("recommendation", ""),
            assumptions=s.get("assumptions", []),
            limitations=s.get("limitations", []),
        )
        for s in raw_scenarios
    ]

    from app.core.config import settings
    return ScenarioResponse(
        farm_id=farm.id,
        scenarios=scenario_results,
        ai_comparison=ai_comparison,
        ai_available=settings.groq_configured,
    )
