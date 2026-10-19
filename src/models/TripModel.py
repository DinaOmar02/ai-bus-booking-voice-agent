from datetime import date, time
from typing import NamedTuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.enums.enum import ACTIVE_BOOKING_STATUSES, TripStatus
from src.models.dbSchemes.booking import Booking
from src.models.dbSchemes.route import Route
from src.models.dbSchemes.trip import Trip


class TripModel:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_trip(self, route_id: int, departure_date: date,
                        departure_time: time, capacity: int) -> Trip:

        trip = Trip(
            route_id=route_id,
            departure_date=departure_date,
            departure_time=departure_time,
            capacity=capacity,
            status=TripStatus.SCHEDULED,
        )

        self._session.add(trip)
        await self._session.flush()

        return trip

    async def get_available_trips(self, origin: str, destination: str, departure_date: date,) -> list[Trip]:

        statement = (
        select(Trip)
        .join(Trip.route)
        .where(
            Route.origin == origin,
            Route.destination == destination,
            Trip.departure_date == departure_date,
            Trip.status == TripStatus.SCHEDULED,
        )
        .order_by(Trip.departure_time)
        )

        result = await self._session.execute(statement)
        return list(result.scalars().all())

