from fastapi import APIRouter

from app.api.endpoints import (
    argument,
    device_type,
    device,
    server,
    experiment,
    reserved_experiment,
    schema,
    option,
    software,
    reservation,
    admin
)


api_router = APIRouter()


api_router.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Admin"],
)

api_router.include_router(
    argument.router,
    prefix="/api/argument",
    tags=["Argument"],
)

api_router.include_router(
    option.router,
    prefix="/api/option",
    tags=["Option"],
)

api_router.include_router(
    reservation.router,
    prefix="/api/reservation",
    tags=["Reservations"],
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


