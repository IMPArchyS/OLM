from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.reservation import Reservation


class ReservationRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_reservation_by_id(self, reservation_id: int) -> Optional[Reservation]:
        statement = select(Reservation).where(Reservation.id == reservation_id)
        return self.db_session.execute(statement).scalar_one_or_none()

    def get_all_reservations(self) -> List[Reservation]:
        statement = select(Reservation)
        return list(self.db_session.execute(statement).scalars().all())

    def create_reservation(self, reservation: Reservation) -> Reservation:
        self.db_session.add(reservation)
        self.db_session.commit()
        self.db_session.refresh(reservation)
        return reservation

    def update_reservation(self, reservation: Reservation) -> Reservation:
        self.db_session.merge(reservation)
        self.db_session.commit()
        self.db_session.refresh(reservation)
        return reservation

    def delete_reservation(self, reservation: Reservation) -> None:
        self.db_session.delete(reservation)
        self.db_session.commit()