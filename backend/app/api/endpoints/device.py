from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device, DeviceCreate, DevicePublic, DeviceUpdate
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.software import Software, SoftwarePublic
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server
from app.models.reservation import Reservation


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Device)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=DevicePublic)
def get_by_id(db: DbSession, id: int): 
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    return db_device


@router.get("/{id}/software")
def get_device_software(db: DbSession, id: int):
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    return db_device.softwares


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, device: DeviceCreate):
    if device.maintenance_start and device.maintenance_end:
        if device.maintenance_start > device.maintenance_end:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maintenance start date cannot be after maintenance end date!")
    
    db_device = Device.model_validate(device)
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.post("/{id}/software/{software_id}", status_code=status.HTTP_201_CREATED)
def add_software_to_device(db: DbSession, id: int, software_id: int):
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    
    db_software = db.get(Software, software_id)
    if not db_software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Software with {software_id} not found!")
    
    if db_software in db_device.softwares:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Software {software_id} already assigned to device {id}!")
    
    db_device.softwares.append(db_software)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)


@router.patch("/{id}", response_model=DevicePublic)
def update(db: DbSession, id: int, device: DeviceUpdate):
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    
    reserved_device_data = device.model_dump(exclude_unset=True)
    db_device.sqlmodel_update(reserved_device_data)
    
    maintenance_start = device.maintenance_start if device.maintenance_start is not None else db_device.maintenance_start
    maintenance_end = device.maintenance_end if device.maintenance_end is not None else db_device.maintenance_end
    
    if maintenance_start and maintenance_end:
        if maintenance_start > maintenance_end:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maintenance start date cannot be after maintenance end date!")
    
    if device.device_type_id is not None and not db.get(DeviceType, device.device_type_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device Type with {device.device_type_id} not found!")    
    
    if device.server_id is not None and not db.get(Server, device.server_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {device.server_id} not found!")    
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    db.delete(db_device)
    db.commit()
    return db_device