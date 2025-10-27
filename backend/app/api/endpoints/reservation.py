from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.reservation import Reservation, ReservationCreate, ReservationPublic, ReservationUpdate
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema, SchemaCreate, SchemaPublic, SchemaUpdate
from app.models.server import Server


router = APIRouter()



@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Reservation)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=ReservationPublic)
def get_by_id(db: DbSession, id: int): 
    db_reservation = db.get(Reservation, id)
    if not db_reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reservation with {id} not found!")
    return db_reservation


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, reservation: ReservationCreate):
    db_reservation = Reservation.model_validate(reservation)
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@router.patch("/{id}", response_model=ReservationPublic)
def update(db: DbSession, id: int, reservation: ReservationUpdate):
    db_reservation = db.get(Reservation, id)
    if not db_reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reservation with {id} not found!")
    reservation_data = reservation.model_dump(exclude_unset=True)
    db_reservation.sqlmodel_update(reservation_data)
    
    if not db.get(Device, reservation.device_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {reservation.device_id} not found!")    
    
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_reservation = db.get(Reservation, id)
    if not db_reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reservation with {id} not found!")
    db.delete(db_reservation)
    db.commit()
    return db_reservation