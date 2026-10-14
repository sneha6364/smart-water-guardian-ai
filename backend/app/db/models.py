"""SQLAlchemy ORM models for Smart Water Guardian."""
from datetime import datetime, timezone

def _utcnow():
    return datetime.now(timezone.utc)
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    location_name = Column(String(300), nullable=True)
    preferred_language = Column(String(20), default="en")
    created_at = Column(DateTime, default=_utcnow)

    farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area_hectares = Column(Float, nullable=True)       # farm area in hectares
    soil_type = Column(String(100), nullable=True)     # e.g. sandy, loam, clay
    irrigation_method = Column(String(100), nullable=True)  # drip, sprinkler, flood
    water_storage_litres = Column(Float, nullable=True)     # current stored water
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    farmer = relationship("Farmer", back_populates="farms")
    crops = relationship("CropRecord", back_populates="farm", cascade="all, delete-orphan")
    water_records = relationship("WaterStorageRecord", back_populates="farm", cascade="all, delete-orphan")
    recommendations = relationship("IrrigationRecommendation", back_populates="farm", cascade="all, delete-orphan")
    events = relationship("IrrigationEvent", back_populates="farm", cascade="all, delete-orphan")
    simulations = relationship("ScenarioSimulation", back_populates="farm", cascade="all, delete-orphan")


class CropRecord(Base):
    __tablename__ = "crop_records"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    crop_type = Column(String(100), nullable=False)    # rice, wheat, maize, etc.
    growth_stage = Column(String(100), nullable=True)  # initial, development, mid, late
    planting_date = Column(DateTime, nullable=True)
    soil_moisture_pct = Column(Float, nullable=True)   # % volumetric, if known
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    farm = relationship("Farm", back_populates="crops")


class WaterStorageRecord(Base):
    __tablename__ = "water_storage_records"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    storage_litres = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=_utcnow)
    source = Column(String(100), nullable=True)   # well, tank, pond, etc.
    notes = Column(Text, nullable=True)

    farm = relationship("Farm", back_populates="water_records")


class IrrigationRecommendation(Base):
    __tablename__ = "irrigation_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    recommended_action = Column(String(200), nullable=False)
    reason = Column(Text, nullable=True)
    weather_summary = Column(Text, nullable=True)
    water_budget_summary = Column(Text, nullable=True)
    estimated_water_requirement_litres = Column(Float, nullable=True)
    uncertainty = Column(Text, nullable=True)
    missing_information = Column(Text, nullable=True)
    evidence_sources = Column(JSON, nullable=True)
    next_steps = Column(Text, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    ai_available = Column(Boolean, default=False)
    calculation_inputs = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    farm = relationship("Farm", back_populates="recommendations")


class IrrigationEvent(Base):
    __tablename__ = "irrigation_events"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    irrigated_at = Column(DateTime, default=_utcnow)
    water_used_litres = Column(Float, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    method = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    farm = relationship("Farm", back_populates="events")


class ScenarioSimulation(Base):
    __tablename__ = "scenario_simulations"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    scenario_name = Column(String(200), nullable=False)
    inputs = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    farm = relationship("Farm", back_populates="simulations")


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    publisher = Column(String(300), nullable=True)
    url = Column(String(1000), nullable=True)
    file_path = Column(String(1000), nullable=True)
    content_text = Column(Text, nullable=True)
    chunk_index = Column(Integer, default=0)
    retrieved_date = Column(DateTime, default=_utcnow)
