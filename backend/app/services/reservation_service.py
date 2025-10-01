from typing import List, Optional
from app.repositories.reservation_repository import ReservationRepository
from app.models.reservation import Reservation
from app.schemas.reservation_bodies import ReservationCreate, ReservationUpdate


class ReservationService:
    def __init__(self, reservation_repository: ReservationRepository) -> None:
        self.reservation_repository = reservation_repository

    def get_reservation_by_id(self, reservation_id: int) -> Optional[Reservation]:
        return self.reservation_repository.get_reservation_by_id(reservation_id)

    def get_all_reservations(self) -> List[Reservation]:
        return self.reservation_repository.get_all_reservations()

    def create_reservation(self, reservation_data: ReservationCreate) -> Reservation:
        reservation = Reservation(start_time=reservation_data.start_time, end_time=reservation_data.end_time, user_id=reservation_data.user_id, tool_id=reservation_data.tool_id)
        return self.reservation_repository.create_reservation(reservation)

    def update_reservation(self, reservation_id: int, reservation_data: ReservationUpdate) -> Reservation:
        reservation = self.reservation_repository.get_reservation_by_id(reservation_id)
        if not reservation:
            raise ValueError(f"Reservation with id {reservation_id} not found")
        reservation.start_time = reservation_data.start_time if reservation_data.start_time is not None else reservation.start_time
        reservation.end_time = reservation_data.end_time if reservation_data.end_time is not None else reservation.end_time
        reservation.user_id = reservation_data.user_id if reservation_data.user_id is not None else reservation.user_id
        reservation.tool_id = reservation_data.tool_id if reservation_data.tool_id is not None else reservation.tool_id
        return self.reservation_repository.update_reservation(reservation)

    def delete_reservation(self, reservation_id: int) -> None:
        reservation = self.reservation_repository.get_reservation_by_id(reservation_id)
        if not reservation:
            raise ValueError(f"Reservation with id {reservation_id} not found")
        return self.reservation_repository.delete_reservation(reservation)