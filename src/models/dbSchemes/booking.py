from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.enums.enum import BookingStatus
from src.models.dbSchemes.base import SQLAlchemyBase


class Booking(SQLAlchemyBase):
    """A seat reservation on a trip, held in PENDING while awaiting payment."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="RESTRICT"), nullable=False
    )
    number_of_seats: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(
            BookingStatus,
            name="booking_status",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        server_default=BookingStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    customer: Mapped["Customer"] = relationship(back_populates="bookings")
    trip: Mapped["Trip"] = relationship(back_populates="bookings")

    __table_args__ = (
        CheckConstraint("number_of_seats > 0", name="number_of_seats_positive"),
        Index("ix_bookings_trip_id_status", "trip_id", "status"),
        Index("ix_bookings_status_expires_at", "status", "expires_at"),
        Index("ix_bookings_customer_id", "customer_id"),
    )