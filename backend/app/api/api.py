from fastapi import APIRouter

from app.api.endpoints import device_type


api_router = APIRouter()


api_router.include_router(
    device_type.router,
    prefix="/api/device_type",
    tags=["device types"],
)