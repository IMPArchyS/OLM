from fastapi import APIRouter

from app.api.endpoints import (
    device_type,
    device,
    server,
    experiment,
    reserved_experiment,
    schema,
    software,
    admin
)


api_router = APIRouter()


api_router.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Admin"],
)

api_router.include_router(
    device_type.router,
    prefix="/api/device_type",
    tags=["Device types"],
)

api_router.include_router(
    device.router,
    prefix="/api/device",
    tags=["Devices"],
)

api_router.include_router(
    software.router,
    prefix="/api/software",
    tags=["Softwares"],
)

api_router.include_router(
    schema.router,
    prefix="/api/schema",
    tags=["Schemas"],
)

api_router.include_router(
    experiment.router,
    prefix="/api/experiment",
    tags=["Experiments"],
)

api_router.include_router(
    reserved_experiment.router,
    prefix="/api/reserved_experiment",
    tags=["Reserved Experiments"],
)

api_router.include_router(
    server.router,
    prefix="/api/server",
    tags=["Servers"],
)


