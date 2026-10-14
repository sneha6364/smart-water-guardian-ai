"""
Demo data seeder — populates three demo scenarios for hackathon presentation.
Run: python seed_demo.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.session import Base
from app.db.models import (
    Farmer, Farm, CropRecord, WaterStorageRecord,
    IrrigationRecommendation,
)

DATABASE_URL = "sqlite+aiosqlite:///./smart_water.db"

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


DEMO_DATA = [
    {
        "farmer": {"name": "Ravi Kumar", "phone": "+91-9876543210", "location_name": "Bangalore Rural, Karnataka"},
        "farm": {
            "name": "Ravi's Rice Farm",
            "latitude": 13.08,
            "longitude": 77.59,
            "area_hectares": 1.5,
            "soil_type": "loam",
            "irrigation_method": "flood",
            "water_storage_litres": 55000,
        },
        "crop": {"crop_type": "rice", "growth_stage": "mid", "notes": "Demo Scenario 1: Rain forecast — should we wait?"},
        "water": {"storage_litres": 55000, "source": "farm pond"},
    },
    {
        "farmer": {"name": "Lakshmi Devi", "phone": "+91-9123456789", "location_name": "Anantapur, Andhra Pradesh"},
        "farm": {
            "name": "Lakshmi's Groundnut Farm",
            "latitude": 14.68,
            "longitude": 77.59,
            "area_hectares": 0.8,
            "soil_type": "sandy loam",
            "irrigation_method": "drip",
            "water_storage_litres": 2500,  # Low water — shortage scenario
        },
        "crop": {"crop_type": "groundnut", "growth_stage": "mid", "notes": "Demo Scenario 2: Water storage critically low"},
        "water": {"storage_litres": 2500, "source": "bore well"},
    },
    {
        "farmer": {"name": "Suresh Patil", "phone": "+91-9988776655", "location_name": "Solapur, Maharashtra"},
        "farm": {
            "name": "Suresh's Wheat Field",
            "latitude": None,   # No coordinates — missing data scenario
            "longitude": None,
            "area_hectares": None,  # Area unknown
            "soil_type": "unknown",
            "irrigation_method": "furrow",
            "water_storage_litres": 20000,
        },
        "crop": {"crop_type": "wheat", "growth_stage": None, "notes": "Demo Scenario 3: Missing coordinates and area — system must explain uncertainty"},
        "water": {"storage_litres": 20000, "source": "canal"},
    },
]


async def seed():
    from app.db import models  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # Check if demo data already exists
        from sqlalchemy import select
        existing = await db.execute(select(Farmer).limit(1))
        if existing.scalars().first():
            print("Demo data already exists. Skipping seed.")
            return

        for d in DEMO_DATA:
            farmer = Farmer(**d["farmer"])
            db.add(farmer)
            await db.flush()

            farm = Farm(farmer_id=farmer.id, **d["farm"])
            db.add(farm)
            await db.flush()

            crop = CropRecord(farm_id=farm.id, **d["crop"])
            db.add(crop)

            water = WaterStorageRecord(farm_id=farm.id, **d["water"])
            db.add(water)
            await db.flush()

            print(f"[OK] Created: {farmer.name} - {farm.name}")

        await db.commit()
        print("\nDemo data seeded successfully!")
        print("Open http://localhost:5173 and select a farmer from the navigation bar.")


if __name__ == "__main__":
    asyncio.run(seed())
