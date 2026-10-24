from datetime import date, datetime, time

from sqlalchemy import (CheckConstraint, Date, DateTime, Enum, ForeignKey, Index,
    SmallInteger, Time, func)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.enums.enum import TripStatusEnum
from src.models.dbSchemes.base import SQLAlchemyBase


class Trip(SQLAlchemyBase):
    #Example: Minya -> Cairo on 2026-10-05 at 08:00 with a capacity of 30.

    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False
    )
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    capacity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[TripStatusEnum] = mapped_column(
        Enum(
            TripStatusEnum,
            name="trip_status",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        server_default=TripStatusEnum.SCHEDULED.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    route: Mapped["Route"] = relationship(back_populates="trips")
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="trip", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint("capacity > 0", name="capacity_positive"),
        Index("ix_trips_route_id_departure_date", "route_id", "departure_date"),
        Index("ix_trips_status_departure_date", "status", "departure_date"),
    )