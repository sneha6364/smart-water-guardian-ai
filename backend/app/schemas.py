"""Pydantic schemas for request / response validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ── Farmer ─────────────────────────────────────────────────────────────────

class FarmerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = None
    email: Optional[str] = None
    location_name: Optional[str] = None
    preferred_language: str = "en"


class FarmerRead(FarmerCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Farm ────────────────────────────────────────────────────────────────────

class FarmCreate(BaseModel):
    farmer_id: int
    name: str = Field(..., min_length=1, max_length=200)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    area_hectares: Optional[float] = Field(None, gt=0)
    soil_type: Optional[str] = None
    irrigation_method: Optional[str] = None
    water_storage_litres: Optional[float] = Field(None, ge=0)


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    area_hectares: Optional[float] = Field(None, gt=0)
    soil_type: Optional[str] = None
    irrigation_method: Optional[str] = None
    water_storage_litres: Optional[float] = Field(None, ge=0)


class FarmRead(FarmCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Crop ────────────────────────────────────────────────────────────────────

class CropCreate(BaseModel):
    farm_id: int
    crop_type: str = Field(..., min_length=1, max_length=100)
    growth_stage: Optional[str] = None
    planting_date: Optional[datetime] = None
    soil_moisture_pct: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class CropRead(CropCreate):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Water Storage ────────────────────────────────────────────────────────────

class WaterStorageCreate(BaseModel):
    farm_id: int
    storage_litres: float = Field(..., ge=0)
    source: Optional[str] = None
    notes: Optional[str] = None


class WaterStorageRead(WaterStorageCreate):
    id: int
    recorded_at: datetime

    model_config = {"from_attributes": True}


# ── Irrigation Event ─────────────────────────────────────────────────────────

class IrrigationEventCreate(BaseModel):
    farm_id: int
    water_used_litres: Optional[float] = Field(None, ge=0)
    duration_minutes: Optional[float] = Field(None, ge=0)
    method: Optional[str] = None
    notes: Optional[str] = None


class IrrigationEventRead(IrrigationEventCreate):
    id: int
    irrigated_at: datetime

    model_config = {"from_attributes": True}


# ── Recommendation Request ───────────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    farm_id: int


# ── Recommendation Response ──────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    farm_id: int
    recommended_action: str
    reason: str
    weather_summary: str
    water_budget_summary: str
    estimated_water_requirement_litres: Optional[float]
    uncertainty: str
    missing_information: str
    evidence_sources: List[Dict[str, Any]] = []
    next_steps: str
    ai_explanation: Optional[str] = None
    ai_available: bool
    calculation_inputs: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Scenario Simulation ──────────────────────────────────────────────────────

class ScenarioRequest(BaseModel):
    farm_id: int
    scenarios: Optional[List[str]] = None  # if None, run all defaults


class ScenarioResult(BaseModel):
    scenario_name: str
    description: str
    estimated_water_use_litres: Optional[float]
    remaining_storage_litres: Optional[float]
    days_remaining: Optional[float]
    recommendation: str
    assumptions: List[str]
    limitations: List[str]


class ScenarioResponse(BaseModel):
    farm_id: int
    scenarios: List[ScenarioResult]
    ai_comparison: Optional[str] = None
    ai_available: bool


# ── Dashboard ────────────────────────────────────────────────────────────────

class DashboardResponse(BaseModel):
    farmer: Optional[FarmerRead]
    farms: List[FarmRead]
    active_crops: List[CropRead]
    latest_water_storage: Optional[WaterStorageRead]
    latest_recommendation: Optional[RecommendationResponse]
    recent_events: List[IrrigationEventRead]
    water_shortage_alert: bool
    days_water_remaining: Optional[float]


# ── Knowledge Search ─────────────────────────────────────────────────────────

class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    top_k: int = Field(5, ge=1, le=20)


class KnowledgeSearchResult(BaseModel):
    title: str
    publisher: Optional[str]
    url: Optional[str]
    passage: str
    relevance_score: Optional[float]


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: List[KnowledgeSearchResult]
    ai_summary: Optional[str] = None
    ai_available: bool
