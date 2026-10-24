from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from livekit.agents import Agent, RunContext, function_tool

from src.main import session_factory as async_session_maker
from src.services import TripService, BookingService
from src.helpers import validate_egyptian_phone
from src.enums import BookingHoldDurationEnum

logger = logging.getLogger("booking")


class BookingAgent(Agent):
    def __init__(self) -> None:
        today = datetime.now(ZoneInfo("Africa/Cairo")).date()
        today_info = today.strftime("%A, %Y-%m-%d")

        super().__init__(
            instructions=(f"""You are a professional voice assistant for a bus booking service. Today is {today_info}.


        ### Voice Style
        - You are speaking out loud on a phone call. Never use emojis, markdown, lists, tables or dashes.
        - Keep every reply to one or two short sentences.
        - Say times and dates naturally, for example "three PM" and "October twenty-fifth".
        - Never read trip IDs aloud. Refer to trips by their departure time.
 
        ### Communication
        - Speak naturally, clearly, and concisely.
        - Ask one question at a time.
        - Avoid unnecessary repetition and do not ask for information the customer has already provided.
 
        ### Required Details
        - Before searching you must have all four, from the customer's own words: departure city, destination city, travel date, and number of seats.
        - Before booking you also need the passenger's full name and phone number.
        - If anything is missing, ask for it. Never fill a missing value with a default such as 0, 1, or today's date.
        - When the customer names a weekday or says tomorrow, take the date from the upcoming dates list above.
        - Pass city names to tools in English, exactly as written in the cities list.
        - Speech recognition can mishear city names (for example Mania for Minya). If a name does not match a city we serve, say what you heard and ask the customer to confirm.

        ### Tool Selection
        - Understand the customer's intent and select the appropriate tool based on its description and required parameters.
        - For a new booking, always search for available trips first. Never call the booking tool before a suitable trip has been found and selected by the customer.
        - Use other tools only when they match the customer's request and the required information is available.
        
        ### Phone Number
        - Ask for the phone number once, then wait quietly. Customers say it in pieces, so do not reply until you have heard all 11 digits.
        - Read the number back digit by digit and ask if it is correct. Accept it only after a clear yes.
        - Copy the digits exactly in the order spoken. Never reorder, add or drop digits.
        
        ### Booking Rules
        - After the customer selects a trip, collect any remaining required booking details.
        - When you have the trip, seats, name and a confirmed phone number, give ONE short summary and ask the customer if you should book it. Then stop and wait.
        - Call the booking tool only after the customer answers yes to that summary, in a new message. Never summarize and book in the same turn.
        - Never treat providing information or selecting a trip as confirmation to book.
        - Never claim success unless the tool confirms the operation succeeded.
        
        ### General Rules
        - Never invent information or guess missing parameters.
        - Convert relative travel dates to YYYY-MM-DD using the upcoming dates list.
        - If a tool fails or no suitable trip is available, explain the result briefly and clearly.
 
                """
            )
        )
 
    @function_tool()
    async def search_bus_trips(
    self,
    context: RunContext,
    origin: str | None = None,
    destination: str | None = None,
    departure_date: str | None = None,
    seats_needed: int | None = None,
    ) -> str:
        """Search for available bus trips between two cities on a specific date and number of seats.
 
        Call this only after the customer has told you the departure city, destination city,
        travel date and number of seats. If any of these is unknown, do NOT guess: leave it
        out and the tool will tell you what to ask.
 
        Args:
            origin: Departure city as stored in the database.
            destination: Arrival city as stored in the database.
            departure_date: Travel date in YYYY-MM-DD format.
            seats_needed: Number of seats requested.
 
        Returns:
            Matching trips with departure times and remaining seats,
            or a message explaining that no trips are available or
            the search failed.
        """
 
        logger.info(
            "[TOOL] search origin=%r destination=%r date=%r seats=%r",
            origin,
            destination,
            departure_date,
            seats_needed,
        )
 
        missing = []
        if not origin or not origin.strip():
            missing.append("departure city")
        if not destination or not destination.strip():
            missing.append("destination city")
        if not departure_date or not departure_date.strip():
            missing.append("travel date")
        if not seats_needed or seats_needed < 1:
            missing.append("number of seats")
 
        if missing:
            return (
            "Cannot search yet. Still missing: " + ", ".join(missing) + ". "
            "Ask the customer for these, one question at a time. Do not guess."
        )
 
        try:
            parsed_date = datetime.strptime(
                departure_date.strip(), "%Y-%m-%d"
            ).date()
        except (ValueError, AttributeError):
            return "Sorry, the date format is invalid. Please try again."
 
        if parsed_date < datetime.now(ZoneInfo("Africa/Cairo")).date():
            return "That date is in the past. Ask the customer for a date from today onwards."
 
        try:
            async with async_session_maker() as session:
                trip_service = TripService(session)
 
                trips = await trip_service.search_available_trips(
                    origin=origin.strip(),
                    destination=destination.strip(),
                    departure_date=parsed_date,
                    seats_needed=seats_needed,
                )
 
        except Exception:
            logger.exception("[TOOL] search_bus_trips failed")
            return "Sorry, I couldn't check the trips right now."
 
        logger.info("[TOOL] search returned %d trips", len(trips))
 
        if not trips:
            return (
                f"No trips are available from {origin} to {destination} "
                f"on {parsed_date.isoformat()} for {seats_needed} seats."
            )
 
        trips_summary = "\n".join([
        f"Departure time: {t.departure_time} "
        f"(internal trip ID {t.trip_id}, never say the ID aloud)."
        for t in trips
        ])
 
        return (
            f"Available trips from {origin} to {destination} "
            f"on {parsed_date.isoformat()} for {seats_needed} seats:\n"
            f"{trips_summary}"
            )
 
 
    @function_tool()
    async def reserve_bus_seats(
        self,
        context: RunContext,
        trip_id: int | None = None,
        passenger_name: str | None = None,
        passenger_phone: str | None = None,
        seats_needed: int | None = None,
        customer_confirmed: bool = False,
    ) -> str:
        """Reserve seats on a specific bus trip for a passenger.
 
        Call this tool only after the customer has selected a trip, provided their
        full name and phone number, confirmed the phone number after you read it back,
        and said yes to the final summary. If any detail is unknown, do NOT guess:
        leave it out and the tool will tell you what to ask.
 
        Args:
            trip_id: The internal ID of the trip the customer chose.
            passenger_name: Full name of the passenger.
            passenger_phone: Phone number of the passenger, digits exactly as spoken.
            seats_needed: Number of seats to reserve.
            customer_confirmed: True only if the customer said yes to the full
            summary (trip, seats, name, phone) in their most recent message.
        """
 
        logger.info(
            "[TOOL] reserve trip_id=%r name=%r phone=%r seats=%r confirmed=%r",
            trip_id, passenger_name, passenger_phone, seats_needed, customer_confirmed
        )
 
        missing = []
        if trip_id is None:
            missing.append("which trip the customer chose")
        if not passenger_name or not passenger_name.strip():
            missing.append("passenger full name")
        if not passenger_phone or not passenger_phone.strip():
            missing.append("phone number")
        if not seats_needed or seats_needed < 1:
            missing.append("number of seats")
        if missing:
            return (
        "Cannot book yet. Still missing: " + ", ".join(missing) + ". "
        "Ask the customer for these, one question at a time. Do not guess."
        )
 
        is_valid, clean_phone = validate_egyptian_phone(passenger_phone)
 
        if not is_valid:
            logger.warning("[TOOL] Invalid phone format received: %r", passenger_phone)
            return (
            "That is not a valid 11-digit Egyptian phone number. "
            "It must start with 010, 011, 012, or 015. Please ask the customer to repeat their phone number."
            )
 
        if not customer_confirmed:
            return (
            "Not booked yet. Give the customer one short summary (trip time, seats, "
            "name and phone), ask if you should book it, and wait for a clear yes."
            )
 
        try:
            async with async_session_maker() as session:
                booking_service = BookingService(session)
                booking = await booking_service.create_booking(
                    trip_id=trip_id,
                    customer_phone=clean_phone,
                    customer_name=passenger_name.strip(),
                    seats_needed=seats_needed,
                )
 
        except ValueError as ve:
            logger.warning("[TOOL] Reservation rejected: %s", ve)
            return f"Sorry, could not complete the reservation: {str(ve)}"
        except Exception:
            logger.exception("[TOOL] reserve_bus_seats failed unexpectedly")
            return "Sorry, an unexpected error occurred while booking. Please try again."
 
 
        return (
            f"Your booking is confirmed for {passenger_name.strip()}. "
            f"{seats_needed} seat(s) are held for {BookingHoldDurationEnum.STANDARD_MINUTES.value} minutes pending payment."
            )
 