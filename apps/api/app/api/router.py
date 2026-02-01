from fastapi import APIRouter

from app.api.ads import router as ads_router
from app.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(ads_router)
