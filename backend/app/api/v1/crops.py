from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import CropRecord
from app.schemas import CropCreate, CropRead

router = APIRouter()


@router.post("/", response_model=CropRead, status_code=201)
async def create_crop(data: CropCreate, db: AsyncSession = Depends(get_db)):
    crop = CropRecord(**data.model_dump())
    db.add(crop)
    await db.commit()
    await db.refresh(crop)
    return crop


@router.get("/farm/{farm_id}", response_model=list[CropRead])
async def list_crops(farm_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CropRecord).where(CropRecord.farm_id == farm_id).order_by(CropRecord.id.desc())
    )
    return result.scalars().all()


@router.get("/{crop_id}", response_model=CropRead)
async def get_crop(crop_id: int, db: AsyncSession = Depends(get_db)):
    crop = await db.get(CropRecord, crop_id)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop record not found")
    return crop


@router.delete("/{crop_id}", status_code=204)
async def delete_crop(crop_id: int, db: AsyncSession = Depends(get_db)):
    crop = await db.get(CropRecord, crop_id)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop record not found")
    await db.delete(crop)
    await db.commit()
