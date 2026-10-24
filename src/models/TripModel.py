from datetime import date, time
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.enums import ACTIVE_BOOKING_STATUSES, TripStatus
from src.models.dbSchemes.booking import Booking
from src.models.dbSchemes.route import Route
from src.models.dbSchemes.trip import Trip


class TripModel:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_trip_by_id(self, trip_id: int) -> Trip | None:
       
        result = await self._session.execute(
            select(Trip).where(Trip.id == trip_id)
        )
        return result.scalar_one_or_none()

    async def get_trips_with_booked_seats(
        self, origin: str, destination: str, departure_date: date
    ) -> list[tuple[Trip, int]]:
        
        booked_subquery = (
            select(
                Booking.trip_id,
                func.coalesce(func.sum(Booking.number_of_seats), 0).label("booked_count")
            )
            .where(Booking.status.in_(ACTIVE_BOOKING_STATUSES))
            .group_by(Booking.trip_id)
            .subquery()
        )

        query = (
            select(Trip, func.coalesce(booked_subquery.c.booked_count, 0))
            .join(Trip.route)
            .outerjoin(booked_subquery, booked_subquery.c.trip_id == Trip.id)
            .where(
                Route.origin == origin,
                Route.destination == destination,
                Trip.departure_date == departure_date,
                Trip.status == TripStatus.SCHEDULED,
            )
            .order_by(Trip.departure_time)
        )

        result = await self._session.execute(query)
        
        return [(row[0], int(row[1])) for row in result.all()]