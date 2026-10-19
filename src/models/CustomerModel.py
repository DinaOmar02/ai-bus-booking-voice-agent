from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dbSchemes.customer import Customer


class CustomerModel:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_customer(self, name: str, phone: str) -> Customer:

        customer = Customer(
            full_name=name,
            phone=phone,
        )

        self._session.add(customer)
        await self._session.flush()

        return customer

    async def get_customer_by_id(self, customer_id: int) -> Customer | None:

        result = await self._session.execute(
            select(Customer).where(Customer.id == customer_id)
        )

        return result.scalar_one_or_none()

    async def get_customer_by_phone(self, phone: str) -> Customer | None:

        result = await self._session.execute(
            select(Customer).where(Customer.phone == phone)
        )

        return result.scalar_one_or_none()
    