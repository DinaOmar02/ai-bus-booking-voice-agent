from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dbSchemes.route import Route


class RouteModel:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_route(self, origin: str, destination: str) -> Route:
        route = Route(origin=origin, destination=destination)
        self._session.add(route)
        await self._session.flush()
        return route

    async def get_route_by_locations(self, origin: str, destination: str) -> Route | None:
        result = await self._session.execute(
            select(Route).where(
                Route.origin == origin,
                Route.destination == destination,
            )
        )
        return result.scalar_one_or_none()

    async def list_routes(self) -> list[Route]:
        result = await self._session.execute(select(Route).order_by(Route.origin, Route.destination))
        return list(result.scalars().all())