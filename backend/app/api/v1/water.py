from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import WaterStorageRecord, Farm
from app.schemas import WaterStorageCreate, WaterStorageRead

router = APIRouter()


@router.post("/", response_model=WaterStorageRead, status_code=201)
async def record_water_storage(data: WaterStorageCreate, db: AsyncSession = Depends(get_db)):
    record = WaterStorageRecord(**data.model_dump())
    db.add(record)
    # Also update the farm's current storage
    farm = await db.get(Farm, data.farm_id)
    if farm:
        farm.water_storage_litres = data.storage_litres
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/farm/{farm_id}", response_model=list[WaterStorageRead])
async def list_water_records(farm_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WaterStorageRecord)
        .where(WaterStorageRecord.farm_id == farm_id)
        .order_by(WaterStorageRecord.recorded_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.post("/events", status_code=201)
async def record_irrigation_event(
    farm_id: int,
    water_used_litres: float,
    db: AsyncSession = Depends(get_db),
):
    """Record that an irrigation event happened and deduct from storage."""
    from app.db.models import IrrigationEvent
    event = IrrigationEvent(farm_id=farm_id, water_used_litres=water_used_litres)
    db.add(event)
    farm = await db.get(Farm, farm_id)
    if farm and farm.water_storage_litres is not None:
        farm.water_storage_litres = max(0, farm.water_storage_litres - water_used_litres)
    await db.commit()
    return {"message": "Irrigation event recorded", "water_used_litres": water_used_litres}
