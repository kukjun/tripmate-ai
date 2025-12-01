"""Plan API Router for TripMate AI.

여행 계획 조회 API 엔드포인트입니다.
"""

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.models.state import TravelState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plan", tags=["plan"])

# 세션 파일 저장 경로
SESSIONS_DIR = "sessions"


def load_session(session_id: str) -> TravelState | None:
    """세션을 파일에서 로드."""
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


class FlightOptionResponse(BaseModel):
    """항공권 옵션 응답 모델."""

    type: str
    price: int
    airline: str
    outbound: dict
    inbound: dict


class HotelOptionResponse(BaseModel):
    """숙박 옵션 응답 모델."""

    type: str
    name: str
    price_per_night: int
    total_price: int
    location: str
    rating: float
    amenities: list[str]
    distance_from_center: str


class BudgetBreakdown(BaseModel):
    """예산 내역 모델."""

    flights: int
    accommodation: int
    food: int
    transport: int
    attractions: int
    total: int


class PlanResponse(BaseModel):
    """여행 계획 응답 모델."""

    session_id: str
    status: str
    user_info: dict
    plan: dict
    created_at: str
    updated_at: str


@router.get("/{session_id}", response_model=PlanResponse)
async def get_plan(session_id: str):
    """완성된 여행 계획 조회.

    Args:
        session_id: 세션 ID

    Returns:
        완성된 여행 계획
    """
    state = load_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    current_step = state.get("current_step", "collecting")

    if current_step != "done":
        status = "in_progress"
        status_message = {
            "collecting": "정보 수집 중입니다",
            "searching_flights": "항공권을 검색하고 있습니다",
            "searching_hotels": "숙박을 검색하고 있습니다",
            "planning": "일정을 생성하고 있습니다",
        }.get(current_step, "처리 중입니다")
    else:
        status = "completed"
        status_message = "여행 계획이 완료되었습니다"

    # 사용자 정보
    user_info = {
        "destination": state.get("destination", ""),
        "duration": state.get("duration", 0),
        "budget": state.get("budget", 0),
        "num_people": state.get("num_people", 0),
        "travel_style": state.get("travel_style", []),
    }

    # 계획 정보
    flight_options = state.get("flight_options", [])
    hotel_options = state.get("hotel_options", [])
    itinerary = state.get("itinerary", {})

    # 예산 계산
    num_people = state.get("num_people", 2)
    duration = state.get("duration", 3)

    recommended_flight = next(
        (f for f in flight_options if f.get("type") == "standard"),
        flight_options[0] if flight_options else {"price": 0},
    )
    recommended_hotel = next(
        (h for h in hotel_options if h.get("type") == "standard"),
        hotel_options[0] if hotel_options else {"total_price": 0},
    )

    flight_total = recommended_flight.get("price", 0) * num_people
    hotel_total = recommended_hotel.get("total_price", 0)
    food_estimate = 50000 * (duration + 1) * num_people
    transport_estimate = 30000 * num_people
    activity_estimate = 20000 * (duration + 1) * num_people

    budget_breakdown = {
        "flights": flight_total,
        "accommodation": hotel_total,
        "food": food_estimate,
        "transport": transport_estimate,
        "attractions": activity_estimate,
        "total": flight_total + hotel_total + food_estimate + transport_estimate + activity_estimate,
    }

    plan = {
        "flights": flight_options,
        "hotels": hotel_options,
        "itinerary": itinerary,
        "budget_breakdown": budget_breakdown,
        "status_message": status_message,
    }

    return PlanResponse(
        session_id=session_id,
        status=status,
        user_info=user_info,
        plan=plan,
        created_at=state.get("created_at", ""),
        updated_at=state.get("updated_at", ""),
    )


@router.get("/{session_id}/flights")
async def get_flight_options(session_id: str):
    """항공권 옵션만 조회."""
    state = load_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    flight_options = state.get("flight_options", [])
    if not flight_options:
        raise HTTPException(status_code=404, detail="항공권 정보가 없습니다")

    return {
        "session_id": session_id,
        "destination": state.get("destination", ""),
        "duration": state.get("duration", 0),
        "flights": flight_options,
    }


@router.get("/{session_id}/hotels")
async def get_hotel_options(session_id: str):
    """숙박 옵션만 조회."""
    state = load_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    hotel_options = state.get("hotel_options", [])
    if not hotel_options:
        raise HTTPException(status_code=404, detail="숙박 정보가 없습니다")

    return {
        "session_id": session_id,
        "destination": state.get("destination", ""),
        "duration": state.get("duration", 0),
        "hotels": hotel_options,
    }


@router.get("/{session_id}/itinerary")
async def get_itinerary(session_id: str):
    """일정만 조회."""
    state = load_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    itinerary = state.get("itinerary", {})
    if not itinerary:
        raise HTTPException(status_code=404, detail="일정 정보가 없습니다")

    return {
        "session_id": session_id,
        "destination": state.get("destination", ""),
        "duration": state.get("duration", 0),
        "travel_style": state.get("travel_style", []),
        "itinerary": itinerary,
    }


@router.get("/{session_id}/summary")
async def get_plan_summary(session_id: str):
    """여행 계획 요약 조회 (마크다운 형식)."""
    state = load_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if state.get("current_step") != "done":
        raise HTTPException(status_code=400, detail="여행 계획이 아직 완성되지 않았습니다")

    # 마지막 메시지가 마크다운 요약
    messages = state.get("messages", [])
    assistant_messages = [m for m in messages if m.get("role") == "assistant"]

    if assistant_messages:
        summary = assistant_messages[-1]["content"]
    else:
        summary = "요약을 생성할 수 없습니다"

    return {
        "session_id": session_id,
        "summary": summary,
        "format": "markdown",
    }
