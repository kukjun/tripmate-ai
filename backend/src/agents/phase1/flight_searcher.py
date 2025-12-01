"""Flight Searcher Agent for Phase 1.

항공권 정보를 검색하고 옵션을 제공하는 Agent입니다.
MVP에서는 하드코딩된 데이터를 사용하고, 추후 크롤링/API로 확장합니다.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from src.models.state import FlightOption, TravelState

logger = logging.getLogger(__name__)

# 공항 코드 매핑
AIRPORT_CODES = {
    "오사카": "KIX",
    "도쿄": "NRT",
    "교토": "KIX",  # 오사카 간사이 공항 이용
    "방콕": "BKK",
    "파리": "CDG",
    "런던": "LHR",
    "뉴욕": "JFK",
    "하와이": "HNL",
    "괌": "GUM",
    "싱가포르": "SIN",
    "홍콩": "HKG",
    "제주": "CJU",
    "다낭": "DAD",
    "발리": "DPS",
    "세부": "CEB",
}

# 항공사 데이터
AIRLINES = {
    "budget": ["티웨이항공", "진에어", "제주항공", "에어서울", "이스타항공"],
    "standard": ["아시아나항공", "대한항공", "에어아시아", "피치항공"],
    "premium": ["대한항공", "아시아나항공", "싱가포르항공", "ANA", "JAL"],
}

# 목적지별 기본 비행 시간 (분)
FLIGHT_TIMES = {
    "오사카": 120,
    "도쿄": 150,
    "교토": 120,
    "방콕": 330,
    "파리": 720,
    "런던": 690,
    "뉴욕": 840,
    "하와이": 540,
    "괌": 240,
    "싱가포르": 390,
    "홍콩": 210,
    "제주": 65,
    "다낭": 270,
    "발리": 420,
    "세부": 270,
}

# 목적지별 기본 가격 (원, 왕복)
BASE_PRICES = {
    "오사카": {"budget": 250000, "standard": 350000, "premium": 550000},
    "도쿄": {"budget": 280000, "standard": 400000, "premium": 600000},
    "교토": {"budget": 250000, "standard": 350000, "premium": 550000},
    "방콕": {"budget": 300000, "standard": 450000, "premium": 700000},
    "파리": {"budget": 800000, "standard": 1200000, "premium": 2500000},
    "런던": {"budget": 750000, "standard": 1100000, "premium": 2300000},
    "뉴욕": {"budget": 900000, "standard": 1400000, "premium": 3000000},
    "하와이": {"budget": 700000, "standard": 1000000, "premium": 2000000},
    "괌": {"budget": 400000, "standard": 550000, "premium": 850000},
    "싱가포르": {"budget": 350000, "standard": 500000, "premium": 900000},
    "홍콩": {"budget": 250000, "standard": 380000, "premium": 600000},
    "제주": {"budget": 80000, "standard": 120000, "premium": 200000},
    "다낭": {"budget": 280000, "standard": 400000, "premium": 650000},
    "발리": {"budget": 450000, "standard": 650000, "premium": 1100000},
    "세부": {"budget": 300000, "standard": 420000, "premium": 700000},
}


def get_airport_code(city: str) -> str:
    """도시명으로 공항 코드 반환."""
    return AIRPORT_CODES.get(city, "ICN")


def format_flight_time(minutes: int) -> str:
    """분을 시:분 형식으로 변환."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def add_time(base_time: str, minutes: int) -> str:
    """시간에 분을 더함."""
    hour, minute = map(int, base_time.split(":"))
    total_minutes = hour * 60 + minute + minutes
    new_hour = (total_minutes // 60) % 24
    new_minute = total_minutes % 60
    return f"{new_hour:02d}:{new_minute:02d}"


def generate_flight_option(
    destination: str,
    flight_type: str,
    departure_date: str,
    return_date: str,
) -> FlightOption:
    """항공권 옵션 생성."""
    import random

    # 기본 가격
    prices = BASE_PRICES.get(destination, BASE_PRICES["오사카"])
    base_price = prices[flight_type]

    # 가격 변동 (-10% ~ +10%)
    price_variation = random.uniform(0.9, 1.1)
    final_price = int(base_price * price_variation)

    # 항공사 선택
    airlines = AIRLINES[flight_type]
    airline = random.choice(airlines)

    # 비행 시간
    flight_time_mins = FLIGHT_TIMES.get(destination, 120)

    # 출발 시간 생성 (타입별로 다름)
    if flight_type == "budget":
        # 저가항공은 이른 아침/늦은 밤
        outbound_departure = random.choice(["06:00", "06:30", "07:00", "21:00", "22:00"])
        inbound_departure = random.choice(["08:00", "09:00", "22:00", "23:00"])
    elif flight_type == "standard":
        # 중간 항공은 오전/오후
        outbound_departure = random.choice(["09:00", "10:00", "11:00", "14:00", "15:00"])
        inbound_departure = random.choice(["10:00", "11:00", "15:00", "16:00"])
    else:  # premium
        # 프리미엄은 편한 시간
        outbound_departure = random.choice(["10:00", "11:00", "12:00"])
        inbound_departure = random.choice(["12:00", "13:00", "14:00"])

    return FlightOption(
        type=flight_type,
        price=final_price,
        airline=airline,
        outbound={
            "departure_time": outbound_departure,
            "arrival_time": add_time(outbound_departure, flight_time_mins),
            "flight_time": format_flight_time(flight_time_mins),
            "date": departure_date,
        },
        inbound={
            "departure_time": inbound_departure,
            "arrival_time": add_time(inbound_departure, flight_time_mins),
            "flight_time": format_flight_time(flight_time_mins),
            "date": return_date,
        },
    )


def search_flights(
    destination: str,
    duration: int,
    departure_date: str | None = None,
) -> list[FlightOption]:
    """항공권 검색 (MVP: 하드코딩 데이터).

    Args:
        destination: 목적지 도시명
        duration: 여행 기간 (박)
        departure_date: 출발일 (없으면 30일 후)

    Returns:
        3개의 항공권 옵션 (budget, standard, premium)
    """
    # 날짜 계산
    if departure_date:
        dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    else:
        dep_date = datetime.now() + timedelta(days=30)

    return_date = dep_date + timedelta(days=duration + 1)

    dep_date_str = dep_date.strftime("%Y-%m-%d")
    ret_date_str = return_date.strftime("%Y-%m-%d")

    # 3가지 옵션 생성
    options = []
    for flight_type in ["budget", "standard", "premium"]:
        option = generate_flight_option(
            destination=destination,
            flight_type=flight_type,
            departure_date=dep_date_str,
            return_date=ret_date_str,
        )
        options.append(option)

    return options


def search_flights_node(state: TravelState) -> dict:
    """항공권 검색 Node.

    정보 수집이 완료된 후 항공권을 검색합니다.
    """
    # 정보 수집이 완료되지 않았으면 스킵
    if not state.get("info_collected"):
        return {}

    # 이미 항공권 검색이 완료되었으면 스킵
    if state.get("flight_options"):
        return {}

    destination = state.get("destination", "")
    duration = state.get("duration", 3)

    if not destination:
        return {
            "error": "목적지 정보가 없습니다.",
            "current_step": "searching_hotels",
        }

    try:
        logger.info(f"Searching flights to {destination} for {duration} nights")

        flight_options = search_flights(
            destination=destination,
            duration=duration,
        )

        logger.info(f"Found {len(flight_options)} flight options")

        return {
            "flight_options": flight_options,
            "current_step": "searching_hotels",
            "messages": [
                {
                    "role": "assistant",
                    "content": f"✈️ {destination}행 항공권 {len(flight_options)}개 옵션을 찾았습니다! 이제 숙박을 검색합니다...",
                }
            ],
        }

    except Exception as e:
        logger.error(f"Flight search failed: {e}")
        return {
            "error": f"항공권 검색 실패: {str(e)}",
            "flight_options": [],
            "current_step": "searching_hotels",
            "messages": [
                {
                    "role": "assistant",
                    "content": "항공권 정보를 가져오는 데 문제가 발생했습니다. 숙박 검색으로 넘어갑니다...",
                }
            ],
        }
