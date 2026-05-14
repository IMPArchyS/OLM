import asyncio
from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import select, asc
from app.api.dependencies import AuthUser, CurrentUser, DbSession, Permission, check_permission, fetch_username
from app.core.config import settings

from app.models.device import Device
from app.models.reservation import Reservation, ReservationCreate, ReservationPublic, ReservationUpdate, ReservationWithUsername
from app.models.utils import now


router = APIRouter()


@router.get("/", response_model=list[ReservationWithUsername])
async def get_all(db: DbSession, _: CurrentUser, device_id: int | None = Query(default=None)):
    stmt = select(Reservation)
    if device_id is not None:
        stmt = stmt.where(Reservation.device_id == device_id)
    reservations = db.exec(stmt).all()

    unique_user_ids = list({r.user_id for r in reservations})

    user_map: dict[int, str] = {}
    if unique_user_ids:
        results = await asyncio.gather(*[fetch_username(uid) for uid in unique_user_ids])
        user_map = dict(results)

    return [
        ReservationWithUsername(**r.model_dump(), username=user_map.get(r.user_id, "Unknown User"))
        for r in reservations
    ]


@router.get("/me")
def get_user_all(db: DbSession, user: CurrentUser):
    stmt = select(Reservation).where(Reservation.user_id == user.id).order_by(asc(Reservation.start))
    db_reservation = db.exec(stmt).all()
    return db_reservation


@router.get("/current", response_model=ReservationPublic)
def get_current(db: DbSession, user: CurrentUser):
    stmt = select(Reservation).where(
        Reservation.user_id == user.id,
        Reservation.start <= now(), 
        Reservation.end >= now()
    ).order_by(asc(Reservation.start))
    db_reservation = db.exec(stmt).first()
    if not db_reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current reservation found!")
    return db_reservation


@router.get("/{id}", response_model=ReservationPublic)
def get_by_id(db: DbSession, id: int, _: CurrentUser):
    db_reservation = db.get(Reservation, id)
    if not db_reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reservation with {id} not found!")
    return db_reservation


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, reservation: ReservationCreate, user: CurrentUser):
    db_reservation = Reservation.model_validate({**reservation.model_dump(), "user_id": user.id})
    db_reservation.user_id = user.id

    if reservation.end <= reservation.start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reservation end time must be after start time"
        )

    duration_minutes = (reservation.end - reservation.start).total_seconds() / 60
    if duration_minutes > settings.RESERVATION_MAX_MINUTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Reservation cannot be longer than {settings.RESERVATION_MAX_MINUTES} minutes"
        )

    if not db.get(Device, reservation.device_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {reservation.device_id} not found!")

    device_overlap_stmt = select(Reservation).where(
        Reservation.device_id == reservation.device_id,
        Reservation.start < reservation.end,
        Reservation.end > reservation.start
    )
    if db.exec(device_overlap_stmt).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device {reservation.device_id} is already reserved during this time period!"
        )

    user_overlap_stmt = select(Reservation).where(
        Reservation.user_id == user.id,
        Reservation.start < reservation.end,
        Reservation.end > reservation.start
    )
    if db.exec(user_overlap_stmt).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a reservation during this time period!"
        )

    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@router.patch("/{id}", response_model=ReservationPublic)
async def update(db: DbSession, id: int, reservation: ReservationUpdate, user: CurrentUser):
    db_reservation = db.get(Reservation, id)
    if not db_reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reservation with {id} not found!")

    if db_reservation.user_id != user.id:
        can_update_all = await check_permission(user.access_token, "olm.reservation.update_all")
        if not can_update_all:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    new_start = reservation.start if reservation.start is not None else db_reservation.start
    new_end = reservation.end if reservation.end is not None else db_reservation.end

    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reservation end time must be after start time"
        )

    duration_minutes = (new_end - new_start).total_seconds() / 60
    if duration_minutes > settings.RESERVATION_MAX_MINUTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Reservation cannot be longer than {settings.RESERVATION_MAX_MINUTES} minutes"
        )

    reservation_data = reservation.model_dump(exclude_unset=True)
    db_reservation.sqlmodel_update(reservation_data)

    new_device_id = reservation.device_id if reservation.device_id is not None else db_reservation.device_id

    if not db.get(Device, new_device_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {new_device_id} not found!")    

    if reservation.start is not None or reservation.end is not None:
        device_overlap_stmt = select(Reservation).where(
            Reservation.id != id,
            Reservation.device_id == new_device_id,
            Reservation.start < new_end,
            Reservation.end > new_start
        )
        if db.exec(device_overlap_stmt).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Device {new_device_id} is already reserved during this time period!"
            )

        user_overlap_stmt = select(Reservation).where(
            Reservation.id != id,
            Reservation.user_id == db_reservation.user_id,
            Reservation.start < new_end,
            Reservation.end > new_start
        )
        if db.exec(user_overlap_stmt).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has a reservation during this time period!"
            )
        
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(db: DbSession, id: int, user: CurrentUser):
    db_reservation = db.get(Reservation, id)
    if not db_reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reservation with {id} not found!")

    if db_reservation.user_id != user.id:
        can_delete_all = await check_permission(user.access_token, "olm.reservation.delete_all")
        if not can_delete_all:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    db.delete(db_reservation)
    db.commit()
    return db_reservation