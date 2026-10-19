from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dbSchemes.booking import Booking


class BookingModel:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_booking(self, customer_id: int, trip_id: int, number_of_seats: int, expires_at: datetime | None) -> Booking:

        booking = Booking(
            customer_id=customer_id,
            trip_id=trip_id,
            number_of_seats=number_of_seats,
            expires_at=expires_at,
        )

        self._session.add(booking)
        await self._session.flush()

        return booking

    async def get_booking_by_id(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(
            select(Booking).where(Booking.id == booking_id)
        )

        return result.scalar_one_or_none()

    async def get_customer_bookings(self, customer_id: int) -> list[Booking]:

        result = await self._session.execute(
            select(Booking)
            .where(Booking.customer_id == customer_id)
            .order_by(Booking.id.desc())
        )

        return list(result.scalars().all())

    async def get_trip_bookings(self, trip_id: int) -> list[Booking]:

        result = await self._session.execute(
            select(Booking)
            .where(Booking.trip_id == trip_id)
            .order_by(Booking.id)
        )

        return list(result.scalars().all())
