"""
Recommendations endpoint.
Orchestrates: weather → calculation engine → RAG → Groq explanation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Farm, CropRecord, WaterStorageRecord, IrrigationRecommendation
from app.schemas import RecommendationRequest, RecommendationResponse
from app.services.weather import get_weather_forecast, weather_to_irrigation_inputs
from app.services.irrigation_engine import IrrigationInputs, calculate_irrigation
from app.services.knowledge_rag import get_context_passages
from app.services.groq_service import explain_recommendation

router = APIRouter()


@router.post("/", response_model=RecommendationResponse, status_code=201)
async def generate_recommendation(
    req: RecommendationRequest, db: AsyncSession = Depends(get_db)
):
    # 1. Load farm
    farm = await db.get(Farm, req.farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # 2. Load active crop
    crop_result = await db.execute(
        select(CropRecord)
        .where(CropRecord.farm_id == farm.id, CropRecord.is_active == True)
        .order_by(CropRecord.id.desc())
        .limit(1)
    )
    crop = crop_result.scalars().first()

    # 3. Load latest water storage
    water_result = await db.execute(
        select(WaterStorageRecord)
        .where(WaterStorageRecord.farm_id == farm.id)
        .order_by(WaterStorageRecord.recorded_at.desc())
        .limit(1)
    )
    water_record = water_result.scalars().first()
    storage = water_record.storage_litres if water_record else farm.water_storage_litres

    # 4. Fetch weather
    weather_data = {}
    if farm.latitude and farm.longitude:
        weather_data = await get_weather_forecast(farm.latitude, farm.longitude)

    weather_inputs = weather_to_irrigation_inputs(weather_data, days=3)

    # 5. Build irrigation inputs
    inputs = IrrigationInputs(
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

    # 6. Deterministic calculation
    calc = calculate_irrigation(inputs)

    calc_dict = {
        "recommended_action": calc.recommended_action,
        "reason": calc.reason,
        "kc_used": calc.kc_used,
        "etc_mm_per_day": calc.etc_mm_per_day,
        "net_irrigation_mm": calc.net_irrigation_mm,
        "gross_irrigation_mm": calc.gross_irrigation_mm,
        "gross_irrigation_litres": calc.gross_irrigation_litres,
        "daily_demand_litres": calc.daily_demand_litres,
        "days_water_remaining": calc.days_water_remaining,
        "storage_alert": calc.storage_alert,
        "effective_rainfall_mm": calc.effective_rainfall_mm,
        "efficiency_used": calc.efficiency_used,
        "assumptions": calc.assumptions,
        "missing_inputs": calc.missing_inputs,
        "uncertainty": calc.uncertainty,
    }

    # 7. RAG knowledge retrieval
    passages = get_context_passages(
        crop_type=crop.crop_type if crop else None,
        growth_stage=crop.growth_stage if crop else None,
        soil_type=farm.soil_type,
        irrigation_method=farm.irrigation_method,
    )

    # 8. Groq explanation
    farm_info = {
        "farm_name": farm.name,
        "area_hectares": farm.area_hectares,
        "soil_type": farm.soil_type,
        "irrigation_method": farm.irrigation_method,
        "water_storage_litres": storage,
        "crop_type": crop.crop_type if crop else None,
        "growth_stage": crop.growth_stage if crop else None,
    }

    ai_result = await explain_recommendation(farm_info, calc_dict, weather_data, passages)

    # 9. Persist recommendation
    rec = IrrigationRecommendation(
        farm_id=farm.id,
        recommended_action=ai_result.get("recommended_action", calc.recommended_action),
        reason=ai_result.get("reason", calc.reason),
        weather_summary=ai_result.get("weather_summary", ""),
        water_budget_summary=ai_result.get("water_budget_summary", ""),
        estimated_water_requirement_litres=calc.gross_irrigation_litres,
        uncertainty=ai_result.get("uncertainty", calc.uncertainty),
        missing_information=ai_result.get("missing_information", ""),
        evidence_sources=[
            {"title": p["title"], "publisher": p.get("publisher"), "url": p.get("url")}
            for p in passages
        ],
        next_steps=ai_result.get("next_steps", ""),
        ai_explanation=ai_result.get("reason"),
        ai_available=ai_result.get("ai_available", False),
        calculation_inputs={**farm_info, **weather_inputs, "calc": calc_dict},
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)

    return RecommendationResponse(
        farm_id=farm.id,
        recommended_action=rec.recommended_action,
        reason=rec.reason,
        weather_summary=rec.weather_summary,
        water_budget_summary=rec.water_budget_summary,
        estimated_water_requirement_litres=rec.estimated_water_requirement_litres,
        uncertainty=rec.uncertainty,
        missing_information=rec.missing_information or "",
        evidence_sources=rec.evidence_sources or [],
        next_steps=rec.next_steps or "",
        ai_explanation=rec.ai_explanation,
        ai_available=rec.ai_available,
        calculation_inputs=rec.calculation_inputs,
        created_at=rec.created_at,
    )


@router.get("/farm/{farm_id}", response_model=list[RecommendationResponse])
async def list_recommendations(farm_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(IrrigationRecommendation)
        .where(IrrigationRecommendation.farm_id == farm_id)
        .order_by(IrrigationRecommendation.created_at.desc())
        .limit(20)
    )
    recs = result.scalars().all()
    return [
        RecommendationResponse(
            farm_id=r.farm_id,
            recommended_action=r.recommended_action,
            reason=r.reason or "",
            weather_summary=r.weather_summary or "",
            water_budget_summary=r.water_budget_summary or "",
            estimated_water_requirement_litres=r.estimated_water_requirement_litres,
            uncertainty=r.uncertainty or "",
            missing_information=r.missing_information or "",
            evidence_sources=r.evidence_sources or [],
            next_steps=r.next_steps or "",
            ai_explanation=r.ai_explanation,
            ai_available=r.ai_available,
            calculation_inputs=r.calculation_inputs,
            created_at=r.created_at,
        )
        for r in recs
    ]
