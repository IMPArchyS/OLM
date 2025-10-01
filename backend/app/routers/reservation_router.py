from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_session
from app.models.reservation import Reservation
from app.schemas.reservation_bodies import ReservationCreate, ReservationUpdate, ReservationResponse
from app.repositories.reservation_repository import ReservationRepository
from app.services.reservation_service import ReservationService


router = APIRouter(tags=["Reservations"], prefix="/reservation")


def get_reservation_repo(session: Session = Depends(get_session)) -> ReservationRepository:
    return ReservationRepository(session)


def get_reservation_service(reserv_repo: ReservationRepository = Depends(get_reservation_repo)) -> ReservationService:
    return ReservationService(reserv_repo)

RvService = Annotated[ReservationService, Depends(get_reservation_service)]


@router.get("/", response_model=List[ReservationResponse])
def get_all_reservations(service: RvService) -> List[Reservation]:
    return service.get_all_reservations() 


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation_by_id(reservation_id: int, service: RvService) -> Reservation:
    reservation = service.get_reservation_by_id(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reservation with id {reservation_id} not found")
    return reservation


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(reservation_data: ReservationCreate, service: RvService) -> Reservation:
    try:
        return service.create_reservation(reservation_data)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))


@router.patch("/{reservation_id}", response_model=ReservationResponse)
def update_reservation(reservation_id: int, reservation_data: ReservationUpdate, service: RvService) -> Reservation:
    try:
        return service.update_reservation(reservation_id, reservation_data)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation(reservation_id: int, service: RvService) -> None:
    try:
        service.delete_reservation(reservation_id)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))