from typing import Any, Iterable

from pydantic import ValidationError

from sqlmodel import select, col

from app.api.dependencies import DbSession
from app.models.device import Device, DeviceSyncPayload
from app.models.device_type import DeviceType
from app.models.server import ServerPublic
from app.models.software import Software
from app.models.utils import ensure, now


# --- Payload parsing ---

def _parse_payload(payload: list[dict]) -> list[DeviceSyncPayload]:
    devices = []
    for i, p in enumerate(payload):
        try:
            devices.append(DeviceSyncPayload.model_validate(p))
        except ValidationError as e:
            raise ValueError(f"Invalid device payload at index {i}: {e}") from e
    return devices


# --- Lookup builders ---

def _get_or_create_software_map(db: DbSession, names: Iterable[str]) -> dict[str, Software]:
    names = sorted(set(names))
    if not names:
        return {}
    existing = db.exec(select(Software).where(col(Software.name).in_(names))).all()
    by_name = {s.name: s for s in existing}
    for name in names:
        if name not in by_name:
            by_name[name] = Software(name=name)
            db.add(by_name[name])
    return by_name


def _get_or_create_device_type_map(db: DbSession, names: Iterable[str]) -> dict[str, DeviceType]:
    names = sorted(set(names))
    if not names:
        return {}
    existing = db.exec(select(DeviceType).where(col(DeviceType.name).in_(names))).all()
    by_name = {dt.name: dt for dt in existing}
    for name in names:
        if name not in by_name:
            by_name[name] = DeviceType(name=name)
            db.add(by_name[name])
    return by_name


# --- Device sync helpers ---

def _create_device(db: DbSession, server_id: int, p: DeviceSyncPayload, device_type_id: int) -> Device:
    device = Device(
        name=p.name,
        maintenance_start=p.maintenance_start,
        maintenance_end=p.maintenance_end,
        device_type_id=device_type_id,
        server_id=server_id,
    )
    db.add(device)
    return device


def _update_device(db: DbSession, device: Device, server_id: int, p: DeviceSyncPayload, device_type_id: int) -> Device:
    device.maintenance_start = p.maintenance_start
    device.maintenance_end = p.maintenance_end
    device.device_type_id = device_type_id
    device.server_id = server_id
    device.deleted_at = None
    device.modified_at = now()
    db.add(device)
    return device


def _upsert_device(
    db: DbSession,
    server_id: int,
    p: DeviceSyncPayload,
    existing_by_name: dict[str, Device],
    device_type_id: int,
) -> Device:
    db_device = existing_by_name.get(p.name)
    if db_device is None:
        db_device = _create_device(db, server_id, p, device_type_id)
        existing_by_name[p.name] = db_device  # guard against duplicate names in payload
    else:
        db_device = _update_device(db, db_device, server_id, p, device_type_id)
    return db_device


def _sync_device_softwares(device: Device, software_names: list[str], software_by_name: dict[str, Software]) -> None:
    unique_names = list(dict.fromkeys(software_names))
    device.softwares = [software_by_name[name] for name in unique_names if name in software_by_name]


def _mark_missing_as_deleted(db: DbSession, server_devices: list[Device], present_names: set[str]) -> None:
    deleted_at = now()
    for device in server_devices:
        if device.name not in present_names and device.deleted_at is None:
            device.deleted_at = deleted_at
            db.add(device)


# --- Public entrypoint ---

def sync_add_server_stack(db: DbSession, server: ServerPublic, payload: list[dict]) -> None:
    devices = _parse_payload(payload)

    software_by_name = _get_or_create_software_map(db, (sw.name for d in devices for sw in d.softwares))
    device_type_by_name = _get_or_create_device_type_map(db, (d.device_type.name for d in devices))

    db.flush()

    server_devices = list(db.exec(select(Device).where(Device.server_id == server.id)).all())
    existing_by_name = {d.name: d for d in server_devices}

    for p in devices:
        device_type = device_type_by_name[p.device_type.name]
        db_device = _upsert_device(db, server.id, p, existing_by_name, ensure(device_type.id))
        _sync_device_softwares(db_device, [sw.name for sw in p.softwares], software_by_name)

    _mark_missing_as_deleted(db, server_devices, {d.name for d in devices})

    db.commit()