from datetime import date, datetime
from dataclasses import dataclass
from src.helpers.text import normalize_location
from src.models import TripModel
from src.models.dbSchemes.trip import Trip
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo


@dataclass
class AvailableTripDTO:
    trip_id: int
    departure_time: str
    available_seats: int


class TripService:
    def __init__(self, session: AsyncSession) -> None:
        self._trip_model = TripModel(session)

    async def search_available_trips(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        seats_needed: int = 1,
    ) -> list[AvailableTripDTO]:

        origin, destination = await normalize_location(origin, destination)

        trips_data = await self._trip_model.get_trips_with_booked_seats(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
        )

        available_trips = []
        now = datetime.now(ZoneInfo("Africa/Cairo"))

        for trip, booked_seats in trips_data:
            if trip.departure_date == now.date() and trip.departure_time <= now.time():
                continue

            free_seats = trip.capacity - booked_seats

            if free_seats >= seats_needed:
                available_trips.append(
                    AvailableTripDTO(
                        trip_id=trip.id,
                        departure_time=trip.departure_time.strftime("%H:%M"),
                        available_seats=free_seats,
                    )
                )

        return available_trips

    async def get_trip(self, trip_id: int) -> Trip | None:
        return await self._trip_model.get_trip_by_id(trip_id)