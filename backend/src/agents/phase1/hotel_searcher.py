"""Hotel Searcher Agent for Phase 1.

숙박 정보를 검색하고 옵션을 제공하는 Agent입니다.
MVP에서는 하드코딩된 데이터를 사용하고, 추후 크롤링/API로 확장합니다.
"""

import logging
import random
from typing import Any

from src.models.state import HotelOption, TravelState

logger = logging.getLogger(__name__)

# 목적지별 숙박 데이터
HOTELS_DATA = {
    "오사카": {
        "budget": [
            {"name": "게스트하우스 난바", "location": "난바", "rating": 4.2, "base_price": 35000},
            {"name": "더 게스트 하우스 우메다", "location": "우메다", "rating": 4.0, "base_price": 38000},
            {"name": "J-호프 오사카 호스텔", "location": "신사이바시", "rating": 4.1, "base_price": 32000},
        ],
        "standard": [
            {"name": "호텔 난바 오리엔탈", "location": "난바", "rating": 4.4, "base_price": 75000},
            {"name": "크로스 호텔 오사카", "location": "신사이바시", "rating": 4.5, "base_price": 85000},
            {"name": "호텔 그레이스리 오사카 난바", "location": "난바", "rating": 4.3, "base_price": 70000},
        ],
        "premium": [
            {"name": "힐튼 오사카", "location": "우메다", "rating": 4.7, "base_price": 180000},
            {"name": "세인트 레지스 오사카", "location": "신사이바시", "rating": 4.8, "base_price": 350000},
            {"name": "리츠칼튼 오사카", "location": "우메다", "rating": 4.9, "base_price": 400000},
        ],
    },
    "도쿄": {
        "budget": [
            {"name": "사쿠라 호텔 이케부쿠로", "location": "이케부쿠로", "rating": 4.1, "base_price": 45000},
            {"name": "카오산 월드 아사쿠사", "location": "아사쿠사", "rating": 4.0, "base_price": 40000},
            {"name": "앤호스텔 시부야", "location": "시부야", "rating": 4.2, "base_price": 50000},
        ],
        "standard": [
            {"name": "호텔 선루트 신주쿠", "location": "신주쿠", "rating": 4.3, "base_price": 90000},
            {"name": "시타딘 신주쿠 도쿄", "location": "신주쿠", "rating": 4.4, "base_price": 100000},
            {"name": "레미아 프리미어 긴자", "location": "긴자", "rating": 4.5, "base_price": 110000},
        ],
        "premium": [
            {"name": "파크 하얏트 도쿄", "location": "신주쿠", "rating": 4.9, "base_price": 450000},
            {"name": "만다린 오리엔탈 도쿄", "location": "니혼바시", "rating": 4.8, "base_price": 400000},
            {"name": "아만 도쿄", "location": "오테마치", "rating": 4.9, "base_price": 600000},
        ],
    },
    "방콕": {
        "budget": [
            {"name": "럽디 방콕 실롬", "location": "실롬", "rating": 4.3, "base_price": 25000},
            {"name": "NapPark 호스텔 @ Khao San", "location": "카오산", "rating": 4.1, "base_price": 20000},
            {"name": "호텔 도어즈 방콕", "location": "사톤", "rating": 4.0, "base_price": 28000},
        ],
        "standard": [
            {"name": "아마리 워터게이트", "location": "프랏남", "rating": 4.4, "base_price": 60000},
            {"name": "노보텔 방콕 스쿰빗", "location": "수쿰빗", "rating": 4.3, "base_price": 65000},
            {"name": "웨스틴 그란데 수쿰빗", "location": "수쿰빗", "rating": 4.5, "base_price": 75000},
        ],
        "premium": [
            {"name": "만다린 오리엔탈 방콕", "location": "차오프라야", "rating": 4.9, "base_price": 350000},
            {"name": "페닌슐라 방콕", "location": "차오프라야", "rating": 4.8, "base_price": 300000},
            {"name": "시암 켐핀스키 호텔", "location": "시암", "rating": 4.8, "base_price": 280000},
        ],
    },
    "제주": {
        "budget": [
            {"name": "제주 에코 호스텔", "location": "제주시", "rating": 4.0, "base_price": 35000},
            {"name": "공항 게스트하우스", "location": "제주시", "rating": 3.9, "base_price": 30000},
            {"name": "월정리 해변 게스트하우스", "location": "월정리", "rating": 4.2, "base_price": 40000},
        ],
        "standard": [
            {"name": "그라벨 호텔 제주", "location": "제주시", "rating": 4.4, "base_price": 80000},
            {"name": "메종 글래드 제주", "location": "중문", "rating": 4.5, "base_price": 90000},
            {"name": "호텔 아름드리 제주", "location": "서귀포", "rating": 4.3, "base_price": 75000},
        ],
        "premium": [
            {"name": "롯데호텔 제주", "location": "중문", "rating": 4.7, "base_price": 200000},
            {"name": "신라스테이 제주", "location": "제주시", "rating": 4.6, "base_price": 180000},
            {"name": "하얏트 리젠시 제주", "location": "중문", "rating": 4.8, "base_price": 250000},
        ],
    },
}

# 기본 호텔 데이터 (목적지가 없을 경우 사용)
DEFAULT_HOTELS = {
    "budget": [
        {"name": "시티 게스트하우스", "location": "시내", "rating": 4.0, "base_price": 40000},
    ],
    "standard": [
        {"name": "시티 호텔", "location": "시내", "rating": 4.4, "base_price": 80000},
    ],
    "premium": [
        {"name": "그랜드 호텔", "location": "시내", "rating": 4.7, "base_price": 200000},
    ],
}

# 편의시설 목록
AMENITIES = {
    "budget": ["WiFi", "공용 주방", "라운지"],
    "standard": ["WiFi", "조식", "피트니스", "세탁", "룸서비스"],
    "premium": ["WiFi", "조식", "피트니스", "스파", "수영장", "발레파킹", "컨시어지"],
}


def get_distance_from_center(hotel_type: str) -> str:
    """호텔 타입에 따른 중심가 거리 반환."""
    distances = {
        "budget": random.choice(["0.8km", "1.0km", "1.2km", "1.5km"]),
        "standard": random.choice(["0.3km", "0.5km", "0.7km"]),
        "premium": random.choice(["0.1km", "0.2km", "0.3km"]),
    }
    return distances.get(hotel_type, "0.5km")


def generate_hotel_option(
    destination: str,
    hotel_type: str,
    duration: int,
    num_people: int,
) -> HotelOption:
    """숙박 옵션 생성."""
    # 목적지별 호텔 데이터 가져오기
    hotels = HOTELS_DATA.get(destination, DEFAULT_HOTELS)
    hotel_list = hotels.get(hotel_type, DEFAULT_HOTELS[hotel_type])

    # 랜덤 호텔 선택
    hotel = random.choice(hotel_list)

    # 가격 변동 (-5% ~ +15%)
    price_variation = random.uniform(0.95, 1.15)
    price_per_night = int(hotel["base_price"] * price_variation)

    # 인원 추가 요금 (2인 초과시)
    if num_people > 2:
        extra_person_fee = 20000 * (num_people - 2)
        price_per_night += extra_person_fee

    # 총 가격 계산
    total_price = price_per_night * duration

    # 편의시설
    amenities = AMENITIES.get(hotel_type, AMENITIES["standard"])

    return HotelOption(
        type=hotel_type,
        name=hotel["name"],
        price_per_night=price_per_night,
        total_price=total_price,
        location=hotel["location"],
        rating=hotel["rating"],
        amenities=amenities,
        distance_from_center=get_distance_from_center(hotel_type),
    )


def search_hotels(
    destination: str,
    duration: int,
    num_people: int = 2,
) -> list[HotelOption]:
    """숙박 검색 (MVP: 하드코딩 데이터).

    Args:
        destination: 목적지 도시명
        duration: 숙박 기간 (박)
        num_people: 인원

    Returns:
        3개의 숙박 옵션 (budget, standard, premium)
    """
    options = []
    for hotel_type in ["budget", "standard", "premium"]:
        option = generate_hotel_option(
            destination=destination,
            hotel_type=hotel_type,
            duration=duration,
            num_people=num_people,
        )
        options.append(option)

    return options


def search_hotels_node(state: TravelState) -> dict:
    """숙박 검색 Node.

    항공권 검색 후 숙박을 검색합니다.
    """
    # 정보 수집이 완료되지 않았으면 스킵
    if not state.get("info_collected"):
        return {}

    # 이미 숙박 검색이 완료되었으면 스킵
    if state.get("hotel_options"):
        return {}

    destination = state.get("destination", "")
    duration = state.get("duration", 3)
    num_people = state.get("num_people", 2)

    if not destination:
        return {
            "error": "목적지 정보가 없습니다.",
            "current_step": "planning",
        }

    try:
        logger.info(
            f"Searching hotels in {destination} for {duration} nights, {num_people} people"
        )

        hotel_options = search_hotels(
            destination=destination,
            duration=duration,
            num_people=num_people,
        )

        logger.info(f"Found {len(hotel_options)} hotel options")

        return {
            "hotel_options": hotel_options,
            "current_step": "planning",
            "messages": [
                {
                    "role": "assistant",
                    "content": f"🏨 {destination} 숙박 {len(hotel_options)}개 옵션을 찾았습니다! 이제 일정을 계획합니다...",
                }
            ],
        }

    except Exception as e:
        logger.error(f"Hotel search failed: {e}")
        return {
            "error": f"숙박 검색 실패: {str(e)}",
            "hotel_options": [],
            "current_step": "planning",
            "messages": [
                {
                    "role": "assistant",
                    "content": "숙박 정보를 가져오는 데 문제가 발생했습니다. 일정 계획으로 넘어갑니다...",
                }
            ],
        }
