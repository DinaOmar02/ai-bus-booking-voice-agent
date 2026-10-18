from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.dbSchemes import Trip


class Route(Base):

    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    origin: Mapped[str] = mapped_column(String(120), nullable=False)
    destination: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    trips: Mapped[list[Trip]] = relationship(
        back_populates="route",
        passive_deletes=True,
        lazy="selectin",
    )

    __table_args__ = (
    UniqueConstraint(
        "origin",
        "destination",
        name="uq_routes_origin_destination",
    ),
    )
    