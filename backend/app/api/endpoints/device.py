from datetime import date, datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, select
from app.api.dependencies import CurrentUser, DbSession

from app.models.device import Device, DevicePublic, DeviceWithSoftware
from app.models.server import Server


router = APIRouter()


@router.get("/", response_model=list[DeviceWithSoftware])
def get_all(db: DbSession, _: CurrentUser):
    stmt = select(Device)
    return db.exec(stmt).all()


@router.get("/available", response_model=list[DeviceWithSoftware])
def get_all_available(db: DbSession, _: CurrentUser):
    stmt = (
        select(Device)
        .where(col(Device.server_id).is_not(None), col(Device.deleted_at).is_(None))
        .join(Server)
        .where(
            col(Server.available).is_(True),
            col(Server.enabled).is_(True),
            col(Server.production).is_(True),
        )
    )
    return db.exec(stmt).all()


@router.get("/{id}", response_model=DevicePublic)
def get_by_id(db: DbSession, id: int, _: CurrentUser):
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    return db_device


@router.get("/{id}/software")
def get_device_software(db: DbSession, id: int, _: CurrentUser):
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    return db_device.softwares


@router.get("/{id}/maintenance-events")
def get_maintenance_events(
    db: DbSession,
    id: int,
    _: CurrentUser,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
):
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")

    if not db_device.maintenance_start or not db_device.maintenance_end:
        return []

    events = []
    current = from_date
    while current <= to_date:
        events.append({
            "id": f"maintenance-{current.isoformat()}",
            "title": "Maintenance",
            "start": datetime.combine(current, db_device.maintenance_start).isoformat(),
            "end": datetime.combine(current, db_device.maintenance_end).isoformat(),
            "backgroundColor": "#ef4444",
            "borderColor": "#dc2626",
            "extendedProps": {"deviceId": id, "isMaintenance": True},
        })
        current += timedelta(days=1)

    return events
