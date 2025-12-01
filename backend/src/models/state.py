"""Travel State definitions for LangGraph workflow."""

from datetime import datetime
from typing import Literal, TypedDict


class FlightOption(TypedDict):
    """항공권 옵션 타입."""

    type: Literal["budget", "standard", "premium"]
    price: int  # 왕복 가격 (원)
    airline: str
    outbound: dict  # departure_time, arrival_time, flight_time
    inbound: dict  # departure_time, arrival_time, flight_time


class HotelOption(TypedDict):
    """숙박 옵션 타입."""

    type: Literal["budget", "standard", "premium"]
    name: str
    price_per_night: int  # 1박 가격 (원)
    total_price: int  # 총 가격 (원)
    location: str
    rating: float
    amenities: list[str]
    distance_from_center: str


class Activity(TypedDict):
    """일정 내 활동 타입."""

    time: str
    activity: str
    type: Literal["transport", "sightseeing", "food", "shopping", "rest"]
    location: str | None
    duration: str | None
    description: str | None


class DayPlan(TypedDict):
    """하루 일정 타입."""

    date: str
    theme: str
    activities: list[Activity]


class Message(TypedDict):
    """채팅 메시지 타입."""

    role: Literal["user", "assistant", "system"]
    content: str


class TravelState(TypedDict, total=False):
    """여행 플래너 상태 관리.

    LangGraph workflow에서 사용되는 전체 상태를 정의합니다.
    """

    # === 사용자 입력 정보 ===
    destination: str  # 목적지 (예: "오사카")
    duration: int  # 기간, 박 (예: 3)
    budget: int  # 예산, 원 (예: 1000000)
    num_people: int  # 인원 (예: 2)
    travel_style: list[str]  # 여행 스타일 (예: ["관광", "맛집"])

    # === 진행 상태 ===
    info_collected: bool  # 정보 수집 완료 여부
    current_step: Literal[
        "collecting",  # 정보 수집 중
        "searching_flights",  # 항공권 검색 중
        "searching_hotels",  # 숙박 검색 중
        "planning",  # 일정 생성 중
        "done",  # 완료
    ]

    # === 검색 결과 ===
    flight_options: list[FlightOption]  # 항공권 옵션 (3개)
    hotel_options: list[HotelOption]  # 숙박 옵션 (3개)
    itinerary: dict[str, DayPlan]  # 일정 (day1, day2, ...)

    # === 대화 히스토리 ===
    messages: list[Message]  # 채팅 히스토리

    # === 메타 정보 ===
    session_id: str  # 세션 ID
    created_at: str  # 생성 시각 (ISO format)
    updated_at: str  # 수정 시각 (ISO format)

    # === 에러 처리 ===
    error: str | None  # 에러 메시지


def create_initial_state(session_id: str) -> TravelState:
    """초기 상태 생성.

    Args:
        session_id: 세션 ID

    Returns:
        초기화된 TravelState
    """
    now = datetime.now().isoformat()

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
        session_id=session_id,
        created_at=now,
        updated_at=now,
        error=None,
    )
