from sqlalchemy.ext.asyncio import AsyncSession

from src.models import RouteModel


class RouteService:
    def __init__(self, session: AsyncSession) -> None:
        self._route_model = RouteModel(session)

    async def get_available_cities(self) -> list[str]:
        routes = await self._route_model.list_routes()

        cities = {
            city.strip()
            for route in routes
            for city in (route.origin, route.destination)
            if city and city.strip()
        }

        return sorted(cities, key=str.casefold)