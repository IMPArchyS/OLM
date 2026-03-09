from sqlmodel import select

from app.api.dependencies import DbSession
from app.api.endpoints.device import create, update
from app.api.endpoints.device_type import sync_device_type
from app.api.endpoints.software import sync_software, get_by_name
from app.models.device import Device, DeviceCreate, DeviceUpdate
from app.models.device_type import DeviceTypeSync
from app.models.server import ServerPublic
from app.models.software import SoftwareSync
from app.models.utils import ensure, now


def sync_add_server_stack(db: DbSession, server: ServerPublic, payload: list[dict]):
    # Software sync
    for p in payload:
        for server_sw in p.get("software", []):
            sync_software(db, SoftwareSync.model_validate(server_sw))

    # Device type sync    
    synced_device_types: list[DeviceTypeSync] = []
    seen = set()
    for p in payload:
        dt = DeviceTypeSync.model_validate(p["device_type"])
        if dt.name not in seen:
            synced_device_types.append(sync_device_type(db, dt))
            seen.add(dt.name)
    
    # Device 
    for p in payload:
        db_device = db.exec(select(Device).where(Device.name == p["name"])).first()
        synced_device_type = next(d for d in synced_device_types if d.name == p["device_type"]["name"])
        
        if not db_device:            
            db_device = create(
                db, DeviceCreate(
                    name=p["name"], 
                    maintenance_start=p["maintenance_start"], 
                    maintenance_end=p["maintenance_end"], 
                    device_type_id=synced_device_type.id,
                    server_id=server.id
                )
            )
        else:
            db_device = update(
                db, ensure(db_device.id), DeviceUpdate(
                    name=p["name"],
                    maintenance_start=p["maintenance_start"],
                    maintenance_end=p["maintenance_end"],
                    server_id=server.id,
                    device_type_id=synced_device_type.id
                )
            )
        
        # sync sw with device
        softwares = []
        for sw in p.get("software", []):
            softwares.append(get_by_name(db, sw["name"]))
        db_device.softwares = softwares
        
        db.add(db_device)
        
    # Mark devices not in payload as deleted
    server_devices = db.exec(select(Device).where(Device.server_id == server.id)).all()
    for db_device in server_devices:
        if db_device.name not in {d["name"] for d in payload}:
            db_device.deleted_at = now()
            db.add(db_device)
    db.commit()