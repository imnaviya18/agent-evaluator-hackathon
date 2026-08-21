"""
Hybrid Mock Tools for the Agent Evaluator.

Properties:
- Zero internet access
- Deterministic normal evaluation
- Stateful inventory and bookings
- Structured traces for every tool call
- Error traces for failed calls
- Privacy-safe trace arguments/results
- Optional simulated latency
- Resettable state for isolated test runs
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import copy
import re
import time
import uuid


# ============================================================
# TRACE MODEL
# ============================================================

@dataclass
class ToolTrace:
    """Structured record of one tool invocation."""

    trace_id: str
    timestamp: str
    tool_name: str
    operation: str
    arguments: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str]
    latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# PRIVACY / REDACTION
# ============================================================

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

_PHONE_RE = re.compile(
    r"\b(?:\+?\d[\d\s().-]{7,}\d)\b"
)

_SECRET_KEYS = {
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "secret",
    "authorization",
    "access_token",
    "refresh_token",
    "driver_license",
}


def redact_sensitive(value: Any, key: Optional[str] = None) -> Any:
    """Recursively redact sensitive values before storing traces."""

    if key and key.lower() in _SECRET_KEYS:
        return "[REDACTED]"

    if isinstance(value, dict):
        return {
            k: redact_sensitive(v, k)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            redact_sensitive(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return tuple(
            redact_sensitive(item)
            for item in value
        )

    if isinstance(value, str):
        value = _EMAIL_RE.sub("[REDACTED_EMAIL]", value)
        value = _PHONE_RE.sub("[REDACTED_PHONE]", value)
        return value

    return value


# ============================================================
# DETERMINISTIC DATA
# ============================================================

class FakeDataGenerator:
    """
    Deterministic fixture provider.

    The class name is retained for compatibility with the
    original implementation, but normal evaluation does not
    use random generation.
    """

    CITIES = [
        "New York",
        "London",
        "Tokyo",
        "Paris",
        "Sydney",
        "Dubai",
        "Singapore",
        "Mumbai",
        "Berlin",
        "Toronto",
    ]

    AIRLINES = [
        "United",
        "British Airways",
        "Virgin Atlantic",
        "Japan Airlines",
        "Air France",
        "Qantas",
        "Emirates",
    ]

    HOTELS = [
        "Grand London Hotel",
        "River Thames Inn",
        "Central London Suites",
        "Paris Garden Hotel",
        "Tokyo Central Hotel",
    ]

    CAR_RENTALS = [
        "Hertz",
        "Avis",
        "Enterprise",
        "Budget",
        "Alamo",
        "National",
    ]

    @classmethod
    def flights(cls) -> List[Dict[str, Any]]:
        return [
            {
                "flight_id": "FL1001",
                "airline": "United",
                "origin": "New York",
                "destination": "London",
                "departure_time": "2026-08-25T08:00:00",
                "arrival_time": "2026-08-25T20:00:00",
                "price": 650.0,
                "currency": "USD",
                "seats_available": 12,
                "class": "Economy",
            },
            {
                "flight_id": "FL1002",
                "airline": "British Airways",
                "origin": "New York",
                "destination": "London",
                "departure_time": "2026-08-25T14:30:00",
                "arrival_time": "2026-08-26T02:30:00",
                "price": 720.0,
                "currency": "USD",
                "seats_available": 5,
                "class": "Economy",
            },
            {
                "flight_id": "FL1003",
                "airline": "Virgin Atlantic",
                "origin": "New York",
                "destination": "London",
                "departure_time": "2026-08-25T19:00:00",
                "arrival_time": "2026-08-26T07:00:00",
                "price": 590.0,
                "currency": "USD",
                "seats_available": 8,
                "class": "Business",
            },
            {
                "flight_id": "FL2001",
                "airline": "Air France",
                "origin": "Paris",
                "destination": "London",
                "departure_time": "2026-08-25T09:15:00",
                "arrival_time": "2026-08-25T10:35:00",
                "price": 180.0,
                "currency": "EUR",
                "seats_available": 15,
                "class": "Economy",
            },
            {
                "flight_id": "FL3001",
                "airline": "Japan Airlines",
                "origin": "Tokyo",
                "destination": "Paris",
                "departure_time": "2026-08-26T11:00:00",
                "arrival_time": "2026-08-26T18:30:00",
                "price": 890.0,
                "currency": "USD",
                "seats_available": 9,
                "class": "Economy",
            },
        ]

    @classmethod
    def hotels(cls) -> List[Dict[str, Any]]:
        return [
            {
                "hotel_id": "HT1001",
                "name": "Grand London Hotel",
                "city": "London",
                "price_per_night": 180.0,
                "currency": "USD",
                "rating": 4.6,
                "amenities": ["WiFi", "Gym", "Restaurant"],
                "rooms_available": 7,
            },
            {
                "hotel_id": "HT1002",
                "name": "River Thames Inn",
                "city": "London",
                "price_per_night": 145.0,
                "currency": "USD",
                "rating": 4.4,
                "amenities": ["WiFi", "Parking", "Restaurant"],
                "rooms_available": 4,
            },
            {
                "hotel_id": "HT1003",
                "name": "Central London Suites",
                "city": "London",
                "price_per_night": 225.0,
                "currency": "USD",
                "rating": 4.8,
                "amenities": ["WiFi", "Pool", "Gym"],
                "rooms_available": 3,
            },
            {
                "hotel_id": "HT2001",
                "name": "Paris Garden Hotel",
                "city": "Paris",
                "price_per_night": 160.0,
                "currency": "EUR",
                "rating": 4.5,
                "amenities": ["WiFi", "Restaurant", "Spa"],
                "rooms_available": 6,
            },
            {
                "hotel_id": "HT3001",
                "name": "Tokyo Central Hotel",
                "city": "Tokyo",
                "price_per_night": 195.0,
                "currency": "USD",
                "rating": 4.7,
                "amenities": ["WiFi", "Gym", "Restaurant"],
                "rooms_available": 5,
            },
        ]

    @classmethod
    def cars(cls) -> List[Dict[str, Any]]:
        return [
            {
                "car_id": "CR1001",
                "company": "Hertz",
                "location": "Tokyo",
                "car_type": "Compact",
                "daily_rate": 65.0,
                "currency": "USD",
                "available": True,
            },
            {
                "car_id": "CR1002",
                "company": "Enterprise",
                "location": "Tokyo",
                "car_type": "SUV",
                "daily_rate": 110.0,
                "currency": "USD",
                "available": True,
            },
            {
                "car_id": "CR1003",
                "company": "Avis",
                "location": "Tokyo",
                "car_type": "Luxury",
                "daily_rate": 220.0,
                "currency": "USD",
                "available": False,
            },
            {
                "car_id": "CR2001",
                "company": "Budget",
                "location": "Paris",
                "car_type": "Sedan",
                "daily_rate": 75.0,
                "currency": "EUR",
                "available": True,
            },
        ]

    @classmethod
    def weather(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "London": {
                "temperature_c": 18,
                "condition": "Partly cloudy",
                "humidity": 68,
                "wind_kph": 14,
            },
            "New York": {
                "temperature_c": 24,
                "condition": "Sunny",
                "humidity": 55,
                "wind_kph": 11,
            },
            "Paris": {
                "temperature_c": 21,
                "condition": "Cloudy",
                "humidity": 62,
                "wind_kph": 9,
            },
            "Tokyo": {
                "temperature_c": 27,
                "condition": "Clear",
                "humidity": 61,
                "wind_kph": 12,
            },
            "Mumbai": {
                "temperature_c": 29,
                "condition": "Humid",
                "humidity": 78,
                "wind_kph": 15,
            },
        }


# ============================================================
# MOCK TOOLS
# ============================================================

class MockTools:
    """
    Local deterministic mock APIs.

    Public tool surface:
        search_flights
        book_flight
        cancel_flight
        search_hotels
        book_hotel
        search_cars
        book_car
        get_booking_details
        get_weather
    """

    def __init__(
        self,
        simulate_latency: bool = False,
        latency_ms: float = 25.0,
    ) -> None:
        self.simulate_latency = simulate_latency
        self.latency_ms = max(0.0, float(latency_ms))

        self.call_history: List[Dict[str, Any]] = []
        self.traces: List[ToolTrace] = []

        self.trace_id: Optional[str] = None

        self._initial_flights = FakeDataGenerator.flights()
        self._initial_hotels = FakeDataGenerator.hotels()
        self._initial_cars = FakeDataGenerator.cars()

        self.reset()

    # ========================================================
    # STATE
    # ========================================================

    def reset(self) -> None:
        """Reset inventory, bookings, and trace history."""

        self.flights = copy.deepcopy(self._initial_flights)
        self.hotels = copy.deepcopy(self._initial_hotels)
        self.cars = copy.deepcopy(self._initial_cars)

        self.bookings: Dict[str, Dict[str, Any]] = {}

        self.call_history = []
        self.traces = []
        self.trace_id = None

    # ========================================================
    # TRACE HELPERS
    # ========================================================

    def set_trace_id(self, trace_id: str) -> None:
        """Attach an external evaluation trace/session ID."""

        self.trace_id = trace_id

    def _simulate_delay(self) -> None:
        if self.simulate_latency and self.latency_ms > 0:
            time.sleep(self.latency_ms / 1000.0)

    def _record(
        self,
        *,
        tool_name: str,
        operation: str,
        arguments: Dict[str, Any],
        result: Any,
        success: bool,
        error: Optional[str],
        started_at: float,
    ) -> None:
        trace = ToolTrace(
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_name=tool_name,
            operation=operation,
            arguments=redact_sensitive(arguments),
            result=redact_sensitive(result),
            success=success,
            error=redact_sensitive(error),
            latency_ms=round(
                (time.perf_counter() - started_at) * 1000,
                3,
            ),
        )

        self.traces.append(trace)

        self.call_history.append(trace.to_dict())

    def _execute(
        self,
        *,
        tool_name: str,
        operation: str,
        arguments: Dict[str, Any],
        fn,
    ) -> Any:
        started_at = time.perf_counter()

        try:
            self._simulate_delay()
            result = fn()

            self._record(
                tool_name=tool_name,
                operation=operation,
                arguments=arguments,
                result=result,
                success=True,
                error=None,
                started_at=started_at,
            )

            return result

        except Exception as exc:
            self._record(
                tool_name=tool_name,
                operation=operation,
                arguments=arguments,
                result=None,
                success=False,
                error=str(exc),
                started_at=started_at,
            )

            raise

    # ========================================================
    # FLIGHTS
    # ========================================================

    def search_flights(
        self,
        origin: str,
        destination: str,
        date: str,
    ) -> Dict[str, Any]:
        """Search available flights."""

        arguments = {
            "origin": origin,
            "destination": destination,
            "date": date,
        }

        def operation() -> Dict[str, Any]:
            if not origin or not destination or not date:
                raise ValueError(
                    "Origin, destination, and date are required."
                )

            matches = [
                copy.deepcopy(flight)
                for flight in self.flights
                if (
                    flight["origin"].lower() == origin.lower()
                    and flight["destination"].lower() == destination.lower()
                    and flight["departure_time"].startswith(date)
                    and flight["seats_available"] > 0
                )
            ]

            return {
                "flights": matches,
                "total": len(matches),
            }

        return self._execute(
            tool_name="flight_api",
            operation="search_flights",
            arguments=arguments,
            fn=operation,
        )

    def book_flight(
        self,
        flight_id: str,
        passenger_name: str,
        passenger_email: str,
    ) -> Dict[str, Any]:
        """Book a flight from deterministic inventory."""

        arguments = {
            "flight_id": flight_id,
            "passenger_name": passenger_name,
            "passenger_email": passenger_email,
        }

        def operation() -> Dict[str, Any]:
            if not flight_id or not passenger_name:
                raise ValueError(
                    "Flight ID and passenger name are required."
                )

            flight = next(
                (
                    item
                    for item in self.flights
                    if item["flight_id"] == flight_id
                ),
                None,
            )

            if flight is None:
                raise ValueError(
                    f"Flight '{flight_id}' not found."
                )

            if flight["seats_available"] <= 0:
                raise RuntimeError(
                    f"Flight '{flight_id}' has no seats available."
                )

            flight["seats_available"] -= 1

            booking_id = (
                f"BK-F-{len(self.bookings) + 1:04d}"
            )

            booking = {
                "booking_id": booking_id,
                "type": "flight",
                "flight_id": flight_id,
                "passenger_name": passenger_name,
                "passenger_email": passenger_email,
                "status": "confirmed",
                "booking_time": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            self.bookings[booking_id] = booking

            return copy.deepcopy(booking)

        return self._execute(
            tool_name="flight_api",
            operation="book_flight",
            arguments=arguments,
            fn=operation,
        )

    def cancel_flight(
        self,
        booking_id: str,
    ) -> Dict[str, Any]:
        """Cancel an existing flight booking."""

        arguments = {
            "booking_id": booking_id,
        }

        def operation() -> Dict[str, Any]:
            if not booking_id:
                raise ValueError("Booking ID is required.")

            booking = self.bookings.get(booking_id)

            if booking is None:
                raise ValueError(
                    f"Booking '{booking_id}' not found."
                )

            if booking["type"] != "flight":
                raise ValueError(
                    f"Booking '{booking_id}' is not a flight booking."
                )

            if booking["status"] == "cancelled":
                return copy.deepcopy(booking)

            booking["status"] = "cancelled"

            flight = next(
                (
                    item
                    for item in self.flights
                    if item["flight_id"] == booking["flight_id"]
                ),
                None,
            )

            if flight is not None:
                flight["seats_available"] += 1

            return {
                "booking_id": booking_id,
                "status": "cancelled",
                "refund_amount": 590.0,
                "refund_currency": "USD",
                "refund_status": "processed",
            }

        return self._execute(
            tool_name="flight_api",
            operation="cancel_flight",
            arguments=arguments,
            fn=operation,
        )

    # ========================================================
    # HOTELS
    # ========================================================

    def search_hotels(
        self,
        city: str,
        check_in: str,
        check_out: str,
        guests: int = 2,
        max_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Search hotels."""

        arguments = {
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "max_price": max_price,
        }

        def operation() -> Dict[str, Any]:
            if not city:
                raise ValueError("City is required.")

            if guests <= 0:
                raise ValueError(
                    "Guests must be greater than zero."
                )

            matches = [
                copy.deepcopy(hotel)
                for hotel in self.hotels
                if (
                    hotel["city"].lower() == city.lower()
                    and hotel["rooms_available"] > 0
                    and (
                        max_price is None
                        or hotel["price_per_night"] <= max_price
                    )
                )
            ]

            return {
                "hotels": matches,
                "total": len(matches),
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
            }

        return self._execute(
            tool_name="hotel_api",
            operation="search_hotels",
            arguments=arguments,
            fn=operation,
        )

    def book_hotel(
        self,
        hotel_id: str,
        guest_name: str,
        room_type: str = "Standard",
        nights: int = 1,
    ) -> Dict[str, Any]:
        """Book a hotel room."""

        arguments = {
            "hotel_id": hotel_id,
            "guest_name": guest_name,
            "room_type": room_type,
            "nights": nights,
        }

        def operation() -> Dict[str, Any]:
            if not hotel_id or not guest_name:
                raise ValueError(
                    "Hotel ID and guest name are required."
                )

            if nights <= 0:
                raise ValueError(
                    "Nights must be greater than zero."
                )

            hotel = next(
                (
                    item
                    for item in self.hotels
                    if item["hotel_id"] == hotel_id
                ),
                None,
            )

            if hotel is None:
                raise ValueError(
                    f"Hotel '{hotel_id}' not found."
                )

            if hotel["rooms_available"] <= 0:
                raise RuntimeError(
                    f"Hotel '{hotel_id}' has no rooms available."
                )

            hotel["rooms_available"] -= 1

            booking_id = (
                f"BK-H-{len(self.bookings) + 1:04d}"
            )

            total_price = (
                hotel["price_per_night"] * nights
            )

            booking = {
                "booking_id": booking_id,
                "type": "hotel",
                "hotel_id": hotel_id,
                "guest_name": guest_name,
                "room_type": room_type,
                "nights": nights,
                "status": "confirmed",
                "total_price": total_price,
                "currency": hotel["currency"],
                "booking_time": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            self.bookings[booking_id] = booking

            return copy.deepcopy(booking)

        return self._execute(
            tool_name="hotel_api",
            operation="book_hotel",
            arguments=arguments,
            fn=operation,
        )

    # ========================================================
    # CAR RENTALS
    # ========================================================

    def search_cars(
        self,
        location: str,
        pickup_date: str,
        dropoff_date: str,
    ) -> Dict[str, Any]:
        """Search available cars."""

        arguments = {
            "location": location,
            "pickup_date": pickup_date,
            "dropoff_date": dropoff_date,
        }

        def operation() -> Dict[str, Any]:
            if not location:
                raise ValueError("Location is required.")

            matches = [
                copy.deepcopy(car)
                for car in self.cars
                if (
                    car["location"].lower() == location.lower()
                    and car["available"]
                )
            ]

            return {
                "cars": matches,
                "total": len(matches),
                "pickup_date": pickup_date,
                "dropoff_date": dropoff_date,
            }

        return self._execute(
            tool_name="car_api",
            operation="search_cars",
            arguments=arguments,
            fn=operation,
        )

    def book_car(
        self,
        car_id: str,
        driver_name: str,
        driver_license: str,
    ) -> Dict[str, Any]:
        """Book a rental car."""

        arguments = {
            "car_id": car_id,
            "driver_name": driver_name,
            "driver_license": driver_license,
        }

        def operation() -> Dict[str, Any]:
            if not car_id or not driver_name:
                raise ValueError(
                    "Car ID and driver name are required."
                )

            car = next(
                (
                    item
                    for item in self.cars
                    if item["car_id"] == car_id
                ),
                None,
            )

            if car is None:
                raise ValueError(
                    f"Car '{car_id}' not found."
                )

            if not car["available"]:
                raise RuntimeError(
                    f"Car '{car_id}' is unavailable."
                )

            car["available"] = False

            booking_id = (
                f"BK-C-{len(self.bookings) + 1:04d}"
            )

            booking = {
                "booking_id": booking_id,
                "type": "car",
                "car_id": car_id,
                "driver_name": driver_name,
                "driver_license": driver_license,
                "status": "confirmed",
                "booking_time": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            self.bookings[booking_id] = booking

            return copy.deepcopy(booking)

        return self._execute(
            tool_name="car_api",
            operation="book_car",
            arguments=arguments,
            fn=operation,
        )

    # ========================================================
    # BOOKING LOOKUP
    # ========================================================

    def get_booking_details(
        self,
        booking_id: str,
    ) -> Dict[str, Any]:
        """Return an existing booking."""

        arguments = {
            "booking_id": booking_id,
        }

        def operation() -> Dict[str, Any]:
            if not booking_id:
                raise ValueError("Booking ID is required.")

            booking = self.bookings.get(booking_id)

            if booking is None:
                return {
                    "booking_id": booking_id,
                    "found": False,
                    "error": "Booking not found",
                }

            return {
                "booking_id": booking_id,
                "found": True,
                "details": copy.deepcopy(booking),
            }

        return self._execute(
            tool_name="booking_api",
            operation="get_booking_details",
            arguments=arguments,
            fn=operation,
        )

    # ========================================================
    # WEATHER
    # ========================================================

    def get_weather(
        self,
        city: str,
    ) -> Dict[str, Any]:
        """Return deterministic weather information."""

        arguments = {
            "city": city,
        }

        def operation() -> Dict[str, Any]:
            if not city:
                raise ValueError("City is required.")

            data = FakeDataGenerator.weather().get(
                city
            )

            if data is None:
                return {
                    "city": city,
                    "available": False,
                    "message": (
                        "Weather data unavailable "
                        "for this city."
                    ),
                }

            return {
                "city": city,
                "available": True,
                **copy.deepcopy(data),
            }

        return self._execute(
            tool_name="weather_api",
            operation="get_weather",
            arguments=arguments,
            fn=operation,
        )

    # ========================================================
    # TRACE ACCESS
    # ========================================================

    def get_traces(self) -> List[Dict[str, Any]]:
        """Return all structured traces."""

        return [
            trace.to_dict()
            for trace in self.traces
        ]

    def get_last_trace(self) -> Optional[Dict[str, Any]]:
        """Return the latest trace."""

        if not self.traces:
            return None

        return self.traces[-1].to_dict()

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Compatibility alias for the original implementation."""

        return copy.deepcopy(self.call_history)

    def clear_history(self) -> None:
        """Clear trace/call history without resetting inventory."""

        self.call_history.clear()
        self.traces.clear()

    def available_tools(self) -> List[str]:
        """Return the public tool names."""

        return [
            "search_flights",
            "book_flight",
            "cancel_flight",
            "search_hotels",
            "book_hotel",
            "search_cars",
            "book_car",
            "get_booking_details",
            "get_weather",
        ]


# ============================================================
# LOCAL SMOKE TEST
# ============================================================

def main() -> None:
    print("🧪 Testing Hybrid Mock Tools (No Internet Required)")
    print("=" * 60)

    tools = MockTools()

    # --------------------------------------------------------
    # Flight search
    # --------------------------------------------------------

    print("✈️  Flight search")

    flights = tools.search_flights(
        "New York",
        "London",
        "2026-08-25",
    )

    print(f"Found {flights['total']} flights")

    if flights["flights"]:
        first = flights["flights"][0]
        print(
            f"First: {first['airline']} / "
            f"{first['flight_id']}"
        )

    # --------------------------------------------------------
    # Booking
    # --------------------------------------------------------

    print("\n📅 Flight booking")

    booking = tools.book_flight(
        "FL1001",
        "John Doe",
        "john@example.com",
    )

    print(
        f"Booking: {booking['booking_id']} / "
        f"{booking['status']}"
    )

    # --------------------------------------------------------
    # Booking lookup
    # --------------------------------------------------------

    print("\n🔎 Booking lookup")

    lookup = tools.get_booking_details(
        booking["booking_id"]
    )

    print(
        f"Status: "
        f"{lookup['details']['status']}"
    )

    # --------------------------------------------------------
    # Hotels
    # --------------------------------------------------------

    print("\n🏨 Hotel search")

    hotels = tools.search_hotels(
        "London",
        "2026-08-25",
        "2026-08-28",
    )

    print(f"Found {hotels['total']} hotels")

    # --------------------------------------------------------
    # Cars
    # --------------------------------------------------------

    print("\n🚗 Car search")

    cars = tools.search_cars(
        "Tokyo",
        "2026-08-25",
        "2026-08-28",
    )

    print(f"Found {cars['total']} cars")

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    print("\n🌤️  Weather")

    weather = tools.get_weather("London")

    print(
        f"London: {weather['condition']}"
    )

    # --------------------------------------------------------
    # Trace check
    # --------------------------------------------------------

    print("\n🧾 Trace check")

    traces = tools.get_traces()

    print(
        f"Generated {len(traces)} "
        f"structured traces"
    )

    if traces:
        print(
            "Last operation:",
            traces[-1]["operation"]
        )

    # --------------------------------------------------------
    # Determinism check
    # --------------------------------------------------------

    tools.reset()

    first = tools.search_flights(
        "New York",
        "London",
        "2026-08-25",
    )

    tools.reset()

    second = tools.search_flights(
        "New York",
        "London",
        "2026-08-25",
    )

    # Compare business results only.
    # Trace metadata intentionally changes.
    assert first == second, (
        "Determinism check failed: "
        "business results differ."
    )

    print("\n🔁 Determinism check: PASS")

    # --------------------------------------------------------
    # Error tracing check
    # --------------------------------------------------------

    tools.reset()

    try:
        tools.search_flights(
            "",
            "London",
            "2026-08-25",
        )
    except ValueError:
        pass

    error_trace = tools.get_last_trace()

    assert error_trace is not None
    assert error_trace["success"] is False
    assert error_trace["error"] is not None

    print("🛡️  Error trace check: PASS")

    # --------------------------------------------------------
    # Privacy check
    # --------------------------------------------------------

    tools.reset()

    tools.book_flight(
        "FL1001",
        "John Doe",
        "john@example.com",
    )

    privacy_trace = tools.get_last_trace()

    assert privacy_trace is not None

    serialized_trace = str(privacy_trace)

    assert "john@example.com" not in serialized_trace
    assert "[REDACTED_EMAIL]" in serialized_trace

    print("🔐 Privacy redaction check: PASS")

    print("\n" + "=" * 60)
    print("✅ Hybrid MockTools working locally!")
    print("🛑 No internet connection required!")


if __name__ == "__main__":
    main()