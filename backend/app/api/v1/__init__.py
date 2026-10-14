"""API v1 router — aggregates all route modules."""
from fastapi import APIRouter

from app.api.v1 import farmers, farms, crops, water, weather, recommendations, scenarios, knowledge, dashboard

router = APIRouter()
router.include_router(farmers.router, prefix="/farmers", tags=["farmers"])
router.include_router(farms.router, prefix="/farms", tags=["farms"])
router.include_router(crops.router, prefix="/crops", tags=["crops"])
router.include_router(water.router, prefix="/water", tags=["water"])
router.include_router(weather.router, prefix="/weather", tags=["weather"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
