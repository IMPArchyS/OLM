from fastapi import APIRouter, HTTPException, status
from sqlmodel import select, asc
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.reservation import Reservation, ReservationCreate, ReservationPublic, ReservationQueue, ReservationUpdate
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema, SchemaCreate, SchemaPublic, SchemaUpdate
from app.models.server import Server
from datetime import datetime, timedelta, timezone

from app.models.utils import now


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
    
    if not db.get(Device, reservation.device_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {reservation.device_id} not found!")
    
    overlapping_stmt = select(Reservation).where(
        Reservation.device_id == reservation.device_id,
        Reservation.start < reservation.end,
        Reservation.end > reservation.start
    )
    overlapping_reservation = db.exec(overlapping_stmt).first()
    if overlapping_reservation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Device {reservation.device_id} is already reserved during this time period!"
        )
    
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@router.post("/queue", status_code=status.HTTP_201_CREATED)
def create_queued(db: DbSession, reservation: ReservationQueue):
    
    if reservation.simulation_time <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Simulation time must be positive!")
    
    if not db.get(Device, reservation.device_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {reservation.device_id} not found!")
    
    existing_reservations_stmt = select(Reservation).where(
        Reservation.device_id == reservation.device_id
    ).order_by(asc(Reservation.start))
    existing_reservations = db.exec(existing_reservations_stmt).all()
    
    duration = timedelta(seconds=reservation.simulation_time + 120)

    def to_utc(dt: datetime) -> datetime:
        if dt is None:
            return None
        if dt.tzinfo is None:
            local_tz = datetime.now().astimezone().tzinfo
            return dt.replace(tzinfo=local_tz).astimezone(timezone.utc)
        return dt.astimezone(timezone.utc)

    proposed_start = now()

    for existing_res in existing_reservations:
        existing_start = to_utc(existing_res.start)
        existing_end = to_utc(existing_res.end)

        if existing_end <= proposed_start:
            continue

        if proposed_start + duration <= existing_start:
            break

        proposed_start = existing_end

    proposed_start = max(proposed_start, now())

    db_reservation = Reservation(start=proposed_start, end=proposed_start + duration, device_id=reservation.device_id)
    db_reservation.queued = True
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

    new_device_id = reservation.device_id if reservation.device_id is not None else db_reservation.device_id

    if not db.get(Device, new_device_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {reservation.device_id} not found!")    

    if reservation.start is not None or reservation.end is not None:
        new_start = reservation.start if reservation.start is not None else db_reservation.start
        new_end = reservation.end if reservation.end is not None else db_reservation.end
        
        overlapping_stmt = select(Reservation).where(
            Reservation.id != id,
            Reservation.device_id == new_device_id,
            Reservation.start < new_end,
            Reservation.end > new_start
        )
        overlapping_reservation = db.exec(overlapping_stmt).first()
        if overlapping_reservation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"Device {new_device_id} is already reserved during this time period!"
            )
        
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