"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_travel_state():
    """Sample travel state for testing."""
    from src.models.state import TravelState

    return TravelState(
        destination="오사카",
        duration=3,
        budget=1000000,
        num_people=2,
        travel_style=["관광", "맛집"],
        info_collected=True,
        current_step="done",
        flight_options=[],
        hotel_options=[],
        itinerary={},
        messages=[],
        session_id="test-session-123",
        created_at="2024-12-01T00:00:00",
        updated_at="2024-12-01T00:00:00",
        error=None,
    )
