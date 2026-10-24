from enum import Enum


class TripStatusEnum(str, Enum):
    """Lifecycle status of a scheduled trip departure."""

    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class BookingStatusEnum(str, Enum):
    """Lifecycle status of a seat reservation.

    A PENDING booking temporarily holds seats while the customer completes
    payment. If payment is not completed before ``expires_at``, the booking
    becomes EXPIRED and the held seats are released.
    """

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class BookingHoldDurationEnum(int, Enum):
    STANDARD_MINUTES = 10

ACTIVE_BOOKING_STATUSES = [
    BookingStatusEnum.PENDING,
    BookingStatusEnum.CONFIRMED
]
