"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient


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


@pytest.fixture
def initial_state():
    """Initial state for testing."""
    from src.models.state import create_initial_state

    return create_initial_state("test-session-456")


@pytest.fixture
def client():
    """FastAPI test client."""
    from app import app

    return TestClient(app)


@pytest.fixture
def collecting_state():
    """State in collecting phase."""
    from src.models.state import TravelState

    return TravelState(
        destination="",
        duration=0,
        budget=0,
        num_people=0,
        travel_style=[],
        info_collected=False,
        current_step="collecting",
        flight_options=[],
        hotel_options=[],
        itinerary={},
        messages=[],
        session_id="test-session-789",
        created_at="2024-12-01T00:00:00",
        updated_at="2024-12-01T00:00:00",
        error=None,
    )


@pytest.fixture
def partial_state():
    """State with partial information."""
    from src.models.state import TravelState

    return TravelState(
        destination="오사카",
        duration=3,
        budget=0,
        num_people=0,
        travel_style=[],
        info_collected=False,
        current_step="collecting",
        flight_options=[],
        hotel_options=[],
        itinerary={},
        messages=[
            {"role": "assistant", "content": "어디로 여행 가고 싶으세요?"},
            {"role": "user", "content": "오사카 3박4일로"},
        ],
        session_id="test-session-partial",
        created_at="2024-12-01T00:00:00",
        updated_at="2024-12-01T00:00:00",
        error=None,
    )
