"""Tests for Phase 1 Agents."""

import pytest

from src.agents.phase1.info_collector import (
    extract_budget,
    extract_destination,
    extract_duration,
    extract_num_people,
    extract_travel_style,
    get_missing_fields,
    info_collector_node,
)
from src.agents.phase1.flight_searcher import (
    get_airport_code,
    search_flights,
    search_flights_node,
)
from src.agents.phase1.hotel_searcher import (
    search_hotels,
    search_hotels_node,
)
from src.agents.phase1.itinerary_planner import (
    generate_itinerary,
    plan_itinerary_node,
)


class TestInfoCollector:
    """Info Collector Agent 테스트."""

    def test_extract_destination_korean(self):
        """한글 목적지 추출 테스트."""
        assert extract_destination("오사카 가고 싶어요") == "오사카"
        assert extract_destination("도쿄로 여행 갈래요") == "도쿄"
        assert extract_destination("방콕 어때요?") == "방콕"

    def test_extract_destination_english(self):
        """영어 목적지 추출 테스트."""
        assert extract_destination("osaka trip") == "오사카"
        assert extract_destination("Let's go to tokyo") == "도쿄"

    def test_extract_destination_none(self):
        """목적지 없을 때 테스트."""
        assert extract_destination("여행 가고 싶어요") is None
        assert extract_destination("안녕하세요") is None

    def test_extract_duration(self):
        """기간 추출 테스트."""
        assert extract_duration("3박 4일") == 3
        assert extract_duration("3박4일") == 3
        assert extract_duration("2박 3일이요") == 2
        assert extract_duration("5박") == 5

    def test_extract_duration_days_only(self):
        """일수만 있을 때 기간 추출 테스트."""
        assert extract_duration("4일") == 3  # 4일 -> 3박

    def test_extract_duration_none(self):
        """기간 없을 때 테스트."""
        assert extract_duration("여행 가고 싶어요") is None

    def test_extract_budget(self):
        """예산 추출 테스트."""
        assert extract_budget("100만원") == 1000000
        assert extract_budget("50만원") == 500000
        assert extract_budget("150만원 정도") == 1500000
        assert extract_budget("1000000원") == 1000000

    def test_extract_budget_text(self):
        """텍스트 예산 추출 테스트."""
        assert extract_budget("백만원") == 1000000

    def test_extract_budget_none(self):
        """예산 없을 때 테스트."""
        assert extract_budget("적당히") is None

    def test_extract_num_people(self):
        """인원 추출 테스트."""
        assert extract_num_people("2명") == 2
        assert extract_num_people("3명이서") == 3
        assert extract_num_people("4인") == 4

    def test_extract_num_people_text(self):
        """텍스트 인원 추출 테스트."""
        assert extract_num_people("혼자") == 1
        assert extract_num_people("둘이서") == 2
        assert extract_num_people("커플") == 2

    def test_extract_num_people_none(self):
        """인원 없을 때 테스트."""
        assert extract_num_people("여럿이서") is None

    def test_extract_travel_style(self):
        """여행 스타일 추출 테스트."""
        assert "관광" in extract_travel_style("관광 위주로")
        assert "맛집" in extract_travel_style("맛집 탐방")
        styles = extract_travel_style("관광이랑 맛집")
        assert "관광" in styles
        assert "맛집" in styles

    def test_extract_travel_style_synonyms(self):
        """동의어 여행 스타일 추출 테스트."""
        assert "맛집" in extract_travel_style("먹방 좋아해요")
        assert "관광" in extract_travel_style("명소 구경")

    def test_extract_travel_style_none(self):
        """스타일 없을 때 테스트."""
        assert extract_travel_style("그냥 가고 싶어요") is None

    def test_get_missing_fields_all(self, collecting_state):
        """모든 필드 누락 테스트."""
        missing = get_missing_fields(collecting_state)
        assert "destination" in missing
        assert "duration" in missing
        assert "budget" in missing
        assert "num_people" in missing
        assert "travel_style" in missing

    def test_get_missing_fields_partial(self, partial_state):
        """일부 필드 누락 테스트."""
        missing = get_missing_fields(partial_state)
        assert "destination" not in missing
        assert "duration" not in missing
        assert "budget" in missing
        assert "num_people" in missing
        assert "travel_style" in missing

    def test_get_missing_fields_complete(self, sample_travel_state):
        """모든 필드 완료 테스트."""
        missing = get_missing_fields(sample_travel_state)
        assert len(missing) == 0

    def test_info_collector_node_first_message(self, collecting_state):
        """첫 메시지 테스트."""
        result = info_collector_node(collecting_state)
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert "여행" in result["messages"][0]["content"]

    def test_info_collector_node_extracts_info(self, collecting_state):
        """정보 추출 테스트."""
        collecting_state["messages"] = [
            {"role": "user", "content": "오사카 3박4일 100만원 2명 관광 맛집"}
        ]
        result = info_collector_node(collecting_state)

        assert result.get("destination") == "오사카"
        assert result.get("duration") == 3
        assert result.get("budget") == 1000000
        assert result.get("num_people") == 2
        assert "관광" in result.get("travel_style", [])
        assert "맛집" in result.get("travel_style", [])


class TestFlightSearcher:
    """Flight Searcher Agent 테스트."""

    def test_get_airport_code(self):
        """공항 코드 변환 테스트."""
        assert get_airport_code("오사카") == "KIX"
        assert get_airport_code("도쿄") == "NRT"
        assert get_airport_code("방콕") == "BKK"
        assert get_airport_code("제주") == "CJU"

    def test_search_flights_returns_3_options(self):
        """항공권 검색이 3개 옵션 반환 테스트."""
        flights = search_flights("오사카", 3)
        assert len(flights) == 3

    def test_search_flights_has_types(self):
        """항공권 옵션 타입 테스트."""
        flights = search_flights("오사카", 3)
        types = [f["type"] for f in flights]
        assert "budget" in types
        assert "standard" in types
        assert "premium" in types

    def test_search_flights_price_order(self):
        """항공권 가격 순서 테스트."""
        flights = search_flights("오사카", 3)
        budget = next(f for f in flights if f["type"] == "budget")
        standard = next(f for f in flights if f["type"] == "standard")
        premium = next(f for f in flights if f["type"] == "premium")

        assert budget["price"] <= standard["price"]
        assert standard["price"] <= premium["price"]

    def test_search_flights_node(self, sample_travel_state):
        """항공권 검색 노드 테스트."""
        sample_travel_state["flight_options"] = []
        result = search_flights_node(sample_travel_state)

        assert "flight_options" in result
        assert len(result["flight_options"]) == 3


class TestHotelSearcher:
    """Hotel Searcher Agent 테스트."""

    def test_search_hotels_returns_3_options(self):
        """숙박 검색이 3개 옵션 반환 테스트."""
        hotels = search_hotels("오사카", 3, 2)
        assert len(hotels) == 3

    def test_search_hotels_has_types(self):
        """숙박 옵션 타입 테스트."""
        hotels = search_hotels("오사카", 3, 2)
        types = [h["type"] for h in hotels]
        assert "budget" in types
        assert "standard" in types
        assert "premium" in types

    def test_search_hotels_price_order(self):
        """숙박 가격 순서 테스트."""
        hotels = search_hotels("오사카", 3, 2)
        budget = next(h for h in hotels if h["type"] == "budget")
        standard = next(h for h in hotels if h["type"] == "standard")
        premium = next(h for h in hotels if h["type"] == "premium")

        assert budget["price_per_night"] <= standard["price_per_night"]
        assert standard["price_per_night"] <= premium["price_per_night"]

    def test_search_hotels_total_price(self):
        """숙박 총 가격 계산 테스트."""
        hotels = search_hotels("오사카", 3, 2)
        for hotel in hotels:
            # 총 가격이 1박 가격 * 박수와 대략 일치하는지
            expected_min = hotel["price_per_night"] * 3 * 0.9
            expected_max = hotel["price_per_night"] * 3 * 1.2
            assert expected_min <= hotel["total_price"] <= expected_max

    def test_search_hotels_node(self, sample_travel_state):
        """숙박 검색 노드 테스트."""
        sample_travel_state["hotel_options"] = []
        result = search_hotels_node(sample_travel_state)

        assert "hotel_options" in result
        assert len(result["hotel_options"]) == 3


class TestItineraryPlanner:
    """Itinerary Planner Agent 테스트."""

    def test_generate_itinerary_correct_days(self):
        """일정 일수 테스트."""
        itinerary = generate_itinerary("오사카", 3, ["관광"])
        assert len(itinerary) == 4  # 3박 4일

    def test_generate_itinerary_has_activities(self):
        """일정에 활동이 있는지 테스트."""
        itinerary = generate_itinerary("오사카", 3, ["관광"])
        for day_key, day_plan in itinerary.items():
            assert "activities" in day_plan
            assert len(day_plan["activities"]) > 0

    def test_generate_itinerary_first_day(self):
        """첫날 일정 테스트 (오후 시작)."""
        itinerary = generate_itinerary("오사카", 3, ["관광"])
        first_day = itinerary["day1"]

        # 첫 활동이 출발인지
        first_activity = first_day["activities"][0]
        assert "출발" in first_activity["activity"] or first_activity["type"] == "transport"

    def test_generate_itinerary_last_day(self):
        """마지막 날 일정 테스트 (귀국)."""
        itinerary = generate_itinerary("오사카", 3, ["관광"])
        last_day = itinerary["day4"]

        # 마지막 활동이 도착인지
        last_activity = last_day["activities"][-1]
        assert "도착" in last_activity["activity"] or last_activity["type"] == "transport"

    def test_plan_itinerary_node(self, sample_travel_state):
        """일정 생성 노드 테스트."""
        sample_travel_state["itinerary"] = {}
        result = plan_itinerary_node(sample_travel_state)

        assert "itinerary" in result
        assert len(result["itinerary"]) == 4  # 3박 4일
