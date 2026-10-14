"""Dashboard endpoint — aggregates all data for the main farmer view."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import (
    Farmer, Farm, CropRecord, WaterStorageRecord,
    IrrigationRecommendation, IrrigationEvent,
)
from app.schemas import (
    DashboardResponse, FarmerRead, FarmRead, CropRead,
    WaterStorageRead, IrrigationEventRead, RecommendationResponse,
)

router = APIRouter()


@router.get("/{farmer_id}", response_model=DashboardResponse)
async def get_dashboard(farmer_id: int, db: AsyncSession = Depends(get_db)):
    farmer = await db.get(Farmer, farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    # Farms
    farms_result = await db.execute(
        select(Farm).where(Farm.farmer_id == farmer_id).order_by(Farm.id)
    )
    farms = farms_result.scalars().all()
    farm_ids = [f.id for f in farms]

    # Active crops (all farms)
    active_crops = []
    latest_water = None
    latest_rec = None
    recent_events = []
    days_remaining = None
    shortage_alert = False

    if farm_ids:
        crop_result = await db.execute(
            select(CropRecord)
            .where(CropRecord.farm_id.in_(farm_ids), CropRecord.is_active == True)
            .order_by(CropRecord.id.desc())
        )
        active_crops = crop_result.scalars().all()

        water_result = await db.execute(
            select(WaterStorageRecord)
            .where(WaterStorageRecord.farm_id.in_(farm_ids))
            .order_by(WaterStorageRecord.recorded_at.desc())
            .limit(1)
        )
        latest_water = water_result.scalars().first()

        rec_result = await db.execute(
            select(IrrigationRecommendation)
            .where(IrrigationRecommendation.farm_id.in_(farm_ids))
            .order_by(IrrigationRecommendation.created_at.desc())
            .limit(1)
        )
        latest_rec_row = rec_result.scalars().first()

        if latest_rec_row:
            latest_rec = RecommendationResponse(
                farm_id=latest_rec_row.farm_id,
                recommended_action=latest_rec_row.recommended_action,
                reason=latest_rec_row.reason or "",
                weather_summary=latest_rec_row.weather_summary or "",
                water_budget_summary=latest_rec_row.water_budget_summary or "",
                estimated_water_requirement_litres=latest_rec_row.estimated_water_requirement_litres,
                uncertainty=latest_rec_row.uncertainty or "",
                missing_information=latest_rec_row.missing_information or "",
                evidence_sources=latest_rec_row.evidence_sources or [],
                next_steps=latest_rec_row.next_steps or "",
                ai_explanation=latest_rec_row.ai_explanation,
                ai_available=latest_rec_row.ai_available,
                calculation_inputs=latest_rec_row.calculation_inputs,
                created_at=latest_rec_row.created_at,
            )

        events_result = await db.execute(
            select(IrrigationEvent)
            .where(IrrigationEvent.farm_id.in_(farm_ids))
            .order_by(IrrigationEvent.irrigated_at.desc())
            .limit(10)
        )
        recent_events = events_result.scalars().all()

        # Calculate days remaining
        if latest_water and latest_rec and latest_rec.estimated_water_requirement_litres:
            daily = latest_rec.estimated_water_requirement_litres / 3
            if daily > 0:
                days_remaining = round(latest_water.storage_litres / daily, 1)
                shortage_alert = days_remaining < 3

    return DashboardResponse(
        farmer=FarmerRead.model_validate(farmer),
        farms=[FarmRead.model_validate(f) for f in farms],
        active_crops=[CropRead.model_validate(c) for c in active_crops],
        latest_water_storage=WaterStorageRead.model_validate(latest_water) if latest_water else None,
        latest_recommendation=latest_rec,
        recent_events=[IrrigationEventRead.model_validate(e) for e in recent_events],
        water_shortage_alert=shortage_alert,
        days_water_remaining=days_remaining,
    )
