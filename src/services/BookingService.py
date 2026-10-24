from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.enums import TripStatusEnum, BookingHoldDurationEnum
from src.models import BookingModel, CustomerModel  

class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._booking_model = BookingModel(session)
        self._customer_model = CustomerModel(session)

    async def create_booking(
        self,
        trip_id: int,
        customer_phone: str,
        customer_name: str,
        seats_needed: int = 1,
    ):
        if seats_needed <= 0:
            raise ValueError("Seats needed must be positive")

        async with self._session.begin():
            
            customer = await self._customer_model.get_customer_by_phone(customer_phone)
            if not customer:
                customer = await self._customer_model.create_customer(
                    name=customer_name,
                    phone=customer_phone
                )

            trip = await self._booking_model.get_trip_for_update(trip_id)
            if trip is None:
                raise ValueError("Trip not found")
            if trip.status != TripStatusEnum.SCHEDULED:
                raise ValueError("Trip is not available for booking")

            booked_seats = await self._booking_model.get_booked_seats(trip_id)
            free_seats = trip.capacity - booked_seats
            if free_seats < seats_needed:
                raise ValueError(f"Not enough seats available. Only {free_seats} seat(s) left.")

            booking = await self._booking_model.create_booking(
                trip_id=trip_id,
                customer_id=customer.id,
                number_of_seats=seats_needed,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=BookingHoldDurationEnum.STANDARD_MINUTES),
            )

        return booking
    