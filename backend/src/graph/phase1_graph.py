"""Phase 1 LangGraph Workflow.

Single Agent 구조의 여행 플래너 워크플로우입니다.
"""

import logging
from datetime import datetime
from typing import Annotated, Literal
from operator import add

from langgraph.graph import END, StateGraph

from src.agents.phase1 import (
    info_collector_node,
    plan_itinerary_node,
    search_flights_node,
    search_hotels_node,
)
from src.models.state import TravelState, create_initial_state

logger = logging.getLogger(__name__)


def should_continue_collecting(state: TravelState) -> Literal["continue", "search"]:
    """정보 수집 계속 여부 결정.

    Returns:
        "continue": 정보 수집 계속
        "search": 검색 단계로 이동
    """
    if state.get("info_collected"):
        return "search"
    return "continue"


def should_continue_after_flights(state: TravelState) -> Literal["hotels", "end"]:
    """항공권 검색 후 다음 단계 결정."""
    # 에러가 있어도 숙박 검색으로 진행
    return "hotels"


def should_continue_after_hotels(state: TravelState) -> Literal["plan", "end"]:
    """숙박 검색 후 다음 단계 결정."""
    # 에러가 있어도 일정 계획으로 진행
    return "plan"


def generate_response_node(state: TravelState) -> dict:
    """최종 응답 생성 Node.

    모든 정보를 통합하여 사용자 친화적 응답을 생성합니다.
    """
    destination = state.get("destination", "")
    duration = state.get("duration", 3)
    budget = state.get("budget", 0)
    num_people = state.get("num_people", 2)
    travel_style = state.get("travel_style", [])

    flight_options = state.get("flight_options", [])
    hotel_options = state.get("hotel_options", [])
    itinerary = state.get("itinerary", {})

    # 마크다운 응답 생성
    response_parts = []

    # 헤더
    response_parts.append(f"# 🎉 {destination} {duration}박{duration + 1}일 여행 계획\n")

    # 여행 정보 요약
    response_parts.append("## 📋 여행 정보")
    response_parts.append(f"- **목적지**: {destination}")
    response_parts.append(f"- **기간**: {duration}박 {duration + 1}일")
    response_parts.append(f"- **인원**: {num_people}명")
    response_parts.append(f"- **1인 예산**: {budget:,}원")
    response_parts.append(f"- **여행 스타일**: {', '.join(travel_style)}\n")

    # 항공권 옵션
    if flight_options:
        response_parts.append("## ✈️ 항공권 옵션\n")
        for flight in flight_options:
            type_emoji = {"budget": "💰", "standard": "🎯", "premium": "👑"}.get(
                flight.get("type", ""), "✈️"
            )
            type_label = {"budget": "저가형", "standard": "추천", "premium": "프리미엄"}.get(
                flight.get("type", ""), ""
            )

            response_parts.append(f"### {type_emoji} {type_label} (왕복 {flight.get('price', 0):,}원)")
            response_parts.append(f"- **항공사**: {flight.get('airline', '-')}")

            outbound = flight.get("outbound", {})
            inbound = flight.get("inbound", {})
            response_parts.append(
                f"- **가는 편**: {outbound.get('date', '')} {outbound.get('departure_time', '')} → {outbound.get('arrival_time', '')} ({outbound.get('flight_time', '')})"
            )
            response_parts.append(
                f"- **오는 편**: {inbound.get('date', '')} {inbound.get('departure_time', '')} → {inbound.get('arrival_time', '')} ({inbound.get('flight_time', '')})\n"
            )

    # 숙박 옵션
    if hotel_options:
        response_parts.append("## 🏨 숙박 옵션\n")
        for hotel in hotel_options:
            type_emoji = {"budget": "💰", "standard": "🎯", "premium": "👑"}.get(
                hotel.get("type", ""), "🏨"
            )
            type_label = {"budget": "저가형", "standard": "추천", "premium": "프리미엄"}.get(
                hotel.get("type", ""), ""
            )

            response_parts.append(
                f"### {type_emoji} {type_label} - {hotel.get('name', '-')}"
            )
            response_parts.append(f"- **위치**: {hotel.get('location', '-')}")
            response_parts.append(f"- **평점**: ⭐ {hotel.get('rating', 0)}/5.0")
            response_parts.append(
                f"- **1박**: {hotel.get('price_per_night', 0):,}원 / **총**: {hotel.get('total_price', 0):,}원"
            )
            response_parts.append(
                f"- **편의시설**: {', '.join(hotel.get('amenities', []))}\n"
            )

    # 일정
    if itinerary:
        response_parts.append("## 📅 일정\n")
        for day_key, day_plan in sorted(itinerary.items()):
            response_parts.append(
                f"### {day_key.upper()} ({day_plan.get('date', '')}) - {day_plan.get('theme', '')}"
            )

            activities = day_plan.get("activities", [])
            for activity in activities:
                time = activity.get("time", "")
                name = activity.get("activity", "")
                description = activity.get("description", "")

                activity_line = f"- **{time}** {name}"
                if description:
                    activity_line += f" - {description}"
                response_parts.append(activity_line)
            response_parts.append("")

    # 예산 계산
    response_parts.append("## 💰 예상 총 비용\n")

    # 추천 옵션 기준으로 계산
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
    food_estimate = 50000 * (duration + 1) * num_people  # 1인 1일 5만원
    transport_estimate = 30000 * num_people  # 현지 교통비
    activity_estimate = 20000 * (duration + 1) * num_people  # 관광비

    total = flight_total + hotel_total + food_estimate + transport_estimate + activity_estimate
    budget_total = budget * num_people
    remaining = budget_total - total

    response_parts.append(f"| 항목 | 금액 |")
    response_parts.append(f"|------|------|")
    response_parts.append(f"| 항공권 (추천) | {flight_total:,}원 |")
    response_parts.append(f"| 숙박 (추천) | {hotel_total:,}원 |")
    response_parts.append(f"| 식비 (예상) | {food_estimate:,}원 |")
    response_parts.append(f"| 교통비 (예상) | {transport_estimate:,}원 |")
    response_parts.append(f"| 관광/활동 (예상) | {activity_estimate:,}원 |")
    response_parts.append(f"| **합계** | **{total:,}원** |")
    response_parts.append("")

    if remaining >= 0:
        response_parts.append(
            f"✅ 예산({budget_total:,}원) 대비 **{remaining:,}원 여유**가 있습니다!"
        )
    else:
        response_parts.append(
            f"⚠️ 예산({budget_total:,}원)을 **{-remaining:,}원 초과**합니다. 저가 옵션을 고려해보세요."
        )

    final_response = "\n".join(response_parts)

    return {
        "messages": [{"role": "assistant", "content": final_response}],
        "current_step": "done",
        "updated_at": datetime.now().isoformat(),
    }


def create_phase1_graph() -> StateGraph:
    """Phase 1 LangGraph 워크플로우 생성.

    Returns:
        컴파일된 LangGraph StateGraph
    """
    # State Graph 생성
    workflow = StateGraph(TravelState)

    # Node 추가
    workflow.add_node("collect_info", info_collector_node)
    workflow.add_node("search_flights", search_flights_node)
    workflow.add_node("search_hotels", search_hotels_node)
    workflow.add_node("plan_itinerary", plan_itinerary_node)
    workflow.add_node("generate_response", generate_response_node)

    # Entry Point
    workflow.set_entry_point("collect_info")

    # Conditional Edge: 정보 수집 완료 여부에 따라 분기
    workflow.add_conditional_edges(
        "collect_info",
        should_continue_collecting,
        {
            "continue": END,  # 정보 수집 중이면 여기서 종료 (사용자 입력 대기)
            "search": "search_flights",  # 정보 수집 완료되면 검색으로
        },
    )

    # 순차 Edge
    workflow.add_edge("search_flights", "search_hotels")
    workflow.add_edge("search_hotels", "plan_itinerary")
    workflow.add_edge("plan_itinerary", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow


# 컴파일된 그래프 인스턴스
_compiled_graph = None


def get_phase1_graph():
    """컴파일된 Phase 1 그래프 반환."""
    global _compiled_graph
    if _compiled_graph is None:
        workflow = create_phase1_graph()
        _compiled_graph = workflow.compile()
    return _compiled_graph


def run_phase1_workflow(state: TravelState) -> TravelState:
    """Phase 1 워크플로우 실행.

    Args:
        state: 현재 TravelState

    Returns:
        업데이트된 TravelState
    """
    graph = get_phase1_graph()
    result = graph.invoke(state)
    return result


async def arun_phase1_workflow(state: TravelState) -> TravelState:
    """Phase 1 워크플로우 비동기 실행.

    Args:
        state: 현재 TravelState

    Returns:
        업데이트된 TravelState
    """
    graph = get_phase1_graph()
    result = await graph.ainvoke(state)
    return result
