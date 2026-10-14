from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Farmer
from app.schemas import FarmerCreate, FarmerRead

router = APIRouter()


@router.post("/", response_model=FarmerRead, status_code=201)
async def create_farmer(data: FarmerCreate, db: AsyncSession = Depends(get_db)):
    farmer = Farmer(**data.model_dump())
    db.add(farmer)
    await db.commit()
    await db.refresh(farmer)
    return farmer


@router.get("/", response_model=list[FarmerRead])
async def list_farmers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Farmer).order_by(Farmer.id))
    return result.scalars().all()


@router.get("/{farmer_id}", response_model=FarmerRead)
async def get_farmer(farmer_id: int, db: AsyncSession = Depends(get_db)):
    farmer = await db.get(Farmer, farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return farmer


@router.delete("/{farmer_id}", status_code=204)
async def delete_farmer(farmer_id: int, db: AsyncSession = Depends(get_db)):
    farmer = await db.get(Farmer, farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    await db.delete(farmer)
    await db.commit()
