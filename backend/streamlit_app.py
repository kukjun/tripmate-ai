"""TripMate AI - Streamlit Chat UI.

Phase 1 프로토타입을 위한 간단한 채팅 인터페이스입니다.
"""

import streamlit as st
from uuid import uuid4

from src.graph.phase1_graph import get_phase1_graph
from src.models.state import create_initial_state, TravelState

# 페이지 설정
st.set_page_config(
    page_title="TripMate AI - 여행 플래너",
    page_icon="✈️",
    layout="wide",
)

# 스타일 커스터마이즈
st.markdown(
    """
    <style>
    .main {
        padding: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
    .progress-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .info-card {
        background-color: #e8f4ea;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state():
    """세션 상태 초기화."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid4())

    if "state" not in st.session_state:
        st.session_state.state = create_initial_state(st.session_state.session_id)
        # 첫 인사 메시지 추가
        st.session_state.state["messages"] = [
            {
                "role": "assistant",
                "content": "안녕하세요! 🌏 여행 계획을 도와드리겠습니다.\n\n어디로 여행을 가고 싶으세요?",
            }
        ]


def get_progress_info(state: TravelState) -> dict:
    """진행 상태 정보 반환."""
    total_fields = 5
    collected = 0

    if state.get("destination"):
        collected += 1
    if state.get("duration") and state.get("duration", 0) > 0:
        collected += 1
    if state.get("budget") and state.get("budget", 0) > 0:
        collected += 1
    if state.get("num_people") and state.get("num_people", 0) > 0:
        collected += 1
    if state.get("travel_style"):
        collected += 1

    current_step = state.get("current_step", "collecting")

    step_labels = {
        "collecting": "📝 정보 수집 중",
        "searching_flights": "✈️ 항공권 검색 중",
        "searching_hotels": "🏨 숙박 검색 중",
        "planning": "📅 일정 생성 중",
        "done": "✅ 완료",
    }

    return {
        "collected": collected,
        "total": total_fields,
        "percentage": int((collected / total_fields) * 100),
        "step": current_step,
        "step_label": step_labels.get(current_step, current_step),
    }


def display_collected_info(state: TravelState):
    """수집된 정보 표시."""
    with st.expander("📋 수집된 여행 정보", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            destination = state.get("destination", "")
            st.markdown(f"**목적지:** {destination if destination else '미정'}")

            duration = state.get("duration", 0)
            st.markdown(
                f"**기간:** {f'{duration}박 {duration + 1}일' if duration else '미정'}"
            )

            budget = state.get("budget", 0)
            st.markdown(f"**예산:** {f'{budget:,}원' if budget else '미정'}")

        with col2:
            num_people = state.get("num_people", 0)
            st.markdown(f"**인원:** {f'{num_people}명' if num_people else '미정'}")

            travel_style = state.get("travel_style", [])
            st.markdown(
                f"**여행 스타일:** {', '.join(travel_style) if travel_style else '미정'}"
            )


def display_progress(state: TravelState):
    """진행 상태 표시."""
    progress = get_progress_info(state)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.progress(progress["percentage"] / 100)

    with col2:
        st.markdown(f"**{progress['step_label']}**")

    with col3:
        st.markdown(f"**{progress['collected']}/{progress['total']}** 완료")


def display_results(state: TravelState):
    """검색 결과 표시."""
    if state.get("current_step") != "done":
        return

    st.markdown("---")
    st.markdown("## 🎉 여행 계획 결과")

    # 탭으로 구분
    tab1, tab2, tab3, tab4 = st.tabs(["✈️ 항공권", "🏨 숙박", "📅 일정", "💰 예산"])

    with tab1:
        display_flights(state)

    with tab2:
        display_hotels(state)

    with tab3:
        display_itinerary(state)

    with tab4:
        display_budget(state)


def display_flights(state: TravelState):
    """항공권 옵션 표시."""
    flight_options = state.get("flight_options", [])

    if not flight_options:
        st.warning("항공권 정보가 없습니다.")
        return

    for flight in flight_options:
        type_emoji = {"budget": "💰", "standard": "🎯", "premium": "👑"}.get(
            flight.get("type", ""), "✈️"
        )
        type_label = {"budget": "저가형", "standard": "추천", "premium": "프리미엄"}.get(
            flight.get("type", ""), ""
        )

        with st.container():
            st.markdown(f"### {type_emoji} {type_label} - {flight.get('airline', '')}")
            st.markdown(f"**왕복 가격:** {flight.get('price', 0):,}원")

            col1, col2 = st.columns(2)
            with col1:
                outbound = flight.get("outbound", {})
                st.markdown("**가는 편**")
                st.markdown(
                    f"{outbound.get('date', '')} {outbound.get('departure_time', '')} → {outbound.get('arrival_time', '')}"
                )
            with col2:
                inbound = flight.get("inbound", {})
                st.markdown("**오는 편**")
                st.markdown(
                    f"{inbound.get('date', '')} {inbound.get('departure_time', '')} → {inbound.get('arrival_time', '')}"
                )

            st.markdown("---")


def display_hotels(state: TravelState):
    """숙박 옵션 표시."""
    hotel_options = state.get("hotel_options", [])

    if not hotel_options:
        st.warning("숙박 정보가 없습니다.")
        return

    for hotel in hotel_options:
        type_emoji = {"budget": "💰", "standard": "🎯", "premium": "👑"}.get(
            hotel.get("type", ""), "🏨"
        )
        type_label = {"budget": "저가형", "standard": "추천", "premium": "프리미엄"}.get(
            hotel.get("type", ""), ""
        )

        with st.container():
            st.markdown(f"### {type_emoji} {type_label} - {hotel.get('name', '')}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**위치:** {hotel.get('location', '')}")
                st.markdown(f"**평점:** ⭐ {hotel.get('rating', 0)}/5.0")
            with col2:
                st.markdown(f"**1박:** {hotel.get('price_per_night', 0):,}원")
                st.markdown(f"**총:** {hotel.get('total_price', 0):,}원")

            st.markdown(f"**편의시설:** {', '.join(hotel.get('amenities', []))}")
            st.markdown("---")


def display_itinerary(state: TravelState):
    """일정 표시."""
    itinerary = state.get("itinerary", {})

    if not itinerary:
        st.warning("일정 정보가 없습니다.")
        return

    for day_key, day_plan in sorted(itinerary.items()):
        with st.expander(
            f"📅 {day_key.upper()} - {day_plan.get('theme', '')}", expanded=True
        ):
            st.markdown(f"**날짜:** {day_plan.get('date', '')}")

            for activity in day_plan.get("activities", []):
                time = activity.get("time", "")
                name = activity.get("activity", "")
                activity_type = activity.get("type", "")
                description = activity.get("description", "")

                type_emoji = {
                    "transport": "🚗",
                    "sightseeing": "🏛️",
                    "food": "🍽️",
                    "shopping": "🛍️",
                    "rest": "😴",
                }.get(activity_type, "📍")

                st.markdown(f"**{time}** {type_emoji} {name}")
                if description:
                    st.markdown(f"   _{description}_")


def display_budget(state: TravelState):
    """예산 표시."""
    num_people = state.get("num_people", 2)
    duration = state.get("duration", 3)
    budget = state.get("budget", 0)

    flight_options = state.get("flight_options", [])
    hotel_options = state.get("hotel_options", [])

    # 추천 옵션 기준
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

    total = flight_total + hotel_total + food_estimate + transport_estimate + activity_estimate
    budget_total = budget * num_people
    remaining = budget_total - total

    st.markdown("### 💰 예상 비용 (추천 옵션 기준)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**항공권:** {flight_total:,}원")
        st.markdown(f"**숙박:** {hotel_total:,}원")
        st.markdown(f"**식비 (예상):** {food_estimate:,}원")

    with col2:
        st.markdown(f"**교통비 (예상):** {transport_estimate:,}원")
        st.markdown(f"**관광/활동 (예상):** {activity_estimate:,}원")

    st.markdown("---")
    st.markdown(f"### 총 예상 비용: **{total:,}원**")
    st.markdown(f"### 예산: **{budget_total:,}원**")

    if remaining >= 0:
        st.success(f"✅ 예산 대비 **{remaining:,}원** 여유가 있습니다!")
    else:
        st.error(f"⚠️ 예산을 **{-remaining:,}원** 초과합니다. 저가 옵션을 고려해보세요.")


def process_user_input(user_message: str):
    """사용자 입력 처리."""
    state = st.session_state.state

    # 사용자 메시지 추가
    messages = list(state.get("messages", []))
    messages.append({"role": "user", "content": user_message})
    state["messages"] = messages

    # LangGraph 워크플로우 실행
    graph = get_phase1_graph()
    result = graph.invoke(dict(state))

    # 상태 업데이트
    st.session_state.state = {**state, **result}


def main():
    """메인 함수."""
    # 세션 초기화
    init_session_state()

    # 헤더
    st.title("✈️ TripMate AI")
    st.markdown("*AI 기반 여행 플래너*")

    # 사이드바
    with st.sidebar:
        st.markdown("## 📊 진행 상태")
        display_progress(st.session_state.state)

        st.markdown("---")
        display_collected_info(st.session_state.state)

        st.markdown("---")
        if st.button("🔄 새 여행 계획 시작", use_container_width=True):
            st.session_state.session_id = str(uuid4())
            st.session_state.state = create_initial_state(st.session_state.session_id)
            st.session_state.state["messages"] = [
                {
                    "role": "assistant",
                    "content": "안녕하세요! 🌏 여행 계획을 도와드리겠습니다.\n\n어디로 여행을 가고 싶으세요?",
                }
            ]
            st.rerun()

        st.markdown("---")
        st.markdown(f"**세션 ID:** `{st.session_state.session_id[:8]}...`")

    # 메인 컨텐츠
    # 채팅 히스토리 표시
    messages = st.session_state.state.get("messages", [])
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")

        if role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)
        elif role == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(content)

    # 결과 표시 (완료된 경우)
    if st.session_state.state.get("current_step") == "done":
        display_results(st.session_state.state)

    # 사용자 입력
    current_step = st.session_state.state.get("current_step", "collecting")

    if current_step != "done":
        if user_input := st.chat_input("메시지를 입력하세요..."):
            # 사용자 메시지 즉시 표시
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)

            # 처리 중 표시
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("생각 중..."):
                    process_user_input(user_input)

            # 페이지 새로고침
            st.rerun()


if __name__ == "__main__":
    main()
