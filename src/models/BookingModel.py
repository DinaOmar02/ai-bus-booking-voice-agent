from datetime import datetime
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.enums import ACTIVE_BOOKING_STATUSES, BookingStatusEnum
from src.models.dbSchemes.booking import Booking
from src.models.dbSchemes.trip import Trip


class BookingModel:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_booking(
        self, customer_id: int, trip_id: int,
        number_of_seats: int, expires_at: datetime | None,) -> Booking:
        
        booking = Booking(
            customer_id=customer_id,
            trip_id=trip_id,
            number_of_seats=number_of_seats,
            expires_at=expires_at,
            status=BookingStatusEnum.PENDING,
        )
        self._session.add(booking)
        await self._session.flush()
        return booking

    async def get_booking_by_id(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_trip_for_update(self, trip_id: int) -> Trip | None:

        result = await self._session.execute(
            select(Trip).where(Trip.id == trip_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_booked_seats(self, trip_id: int) -> int:

        result = await self._session.execute(
            select(func.coalesce(func.sum(Booking.number_of_seats), 0)).where(
                Booking.trip_id == trip_id,
                Booking.status.in_(ACTIVE_BOOKING_STATUSES),
            )
        )
        return int(result.scalar_one())

    async def update_status(self, booking_id: int, status: BookingStatusEnum) -> Booking | None:
        
        booking = await self.get_booking_by_id(booking_id)
        if booking:
            booking.status = status
            await self._session.flush()
        return booking

    async def get_customer_bookings(self, customer_id: int) -> list[Booking]:
        result = await self._session.execute(
            select(Booking)
            .where(Booking.customer_id == customer_id)
            .order_by(Booking.id.desc())
        )
        return list(result.scalars().all())