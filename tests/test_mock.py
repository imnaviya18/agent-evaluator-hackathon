"""
Tests for Hybrid Mock Tools.
"""

from sandbox.mock_tools import MockTools


def test_mock_tools_search_flights():
    tools = MockTools()
    flights = tools.search_flights(
        "New York",
        "London",
        "2026-08-25",
    )
    assert flights is not None
    assert flights["total"] > 0
    assert len(flights["flights"]) > 0


def test_mock_tools_booking_and_privacy():
    tools = MockTools()
    booking = tools.book_flight(
        "FL1001",
        "John Doe",
        "john.doe@example.com",
    )
    assert booking is not None
    assert booking["status"] == "confirmed"

    last_trace = tools.get_last_trace()
    assert last_trace is not None
    assert "[REDACTED_EMAIL]" in str(last_trace)


if __name__ == "__main__":
    test_mock_tools_search_flights()
    test_mock_tools_booking_and_privacy()
    print("✅ All mock tools tests passed!")