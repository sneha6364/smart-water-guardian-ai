from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Farm
from app.schemas import FarmCreate, FarmRead, FarmUpdate

router = APIRouter()


@router.post("/", response_model=FarmRead, status_code=201)
async def create_farm(data: FarmCreate, db: AsyncSession = Depends(get_db)):
    farm = Farm(**data.model_dump())
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    return farm


@router.get("/", response_model=list[FarmRead])
async def list_farms(farmer_id: int | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Farm).order_by(Farm.id)
    if farmer_id:
        q = q.where(Farm.farmer_id == farmer_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{farm_id}", response_model=FarmRead)
async def get_farm(farm_id: int, db: AsyncSession = Depends(get_db)):
    farm = await db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.patch("/{farm_id}", response_model=FarmRead)
async def update_farm(farm_id: int, data: FarmUpdate, db: AsyncSession = Depends(get_db)):
    farm = await db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(farm, key, value)
    farm.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=204)
async def delete_farm(farm_id: int, db: AsyncSession = Depends(get_db)):
    farm = await db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    await db.delete(farm)
    await db.commit()
