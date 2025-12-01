"""Itinerary Planner Agent for Phase 1.

여행 일정을 생성하는 Agent입니다.
MVP에서는 하드코딩된 데이터를 사용하고, 추후 LLM/API로 확장합니다.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.models.state import Activity, DayPlan, TravelState
from src.utils.prompts import (
    ITINERARY_PLANNER_SYSTEM_PROMPT,
    ITINERARY_PLANNER_USER_PROMPT,
)

logger = logging.getLogger(__name__)

# 목적지별 추천 장소 데이터
DESTINATION_SPOTS = {
    "오사카": {
        "sightseeing": [
            {"name": "오사카성", "duration": "2시간", "description": "일본 3대 명성 중 하나, 역사적인 성곽"},
            {"name": "도톤보리", "duration": "2시간", "description": "오사카의 상징적인 번화가, 글리코 사인"},
            {"name": "신사이바시", "duration": "2시간", "description": "쇼핑과 먹거리의 천국"},
            {"name": "유니버셜 스튜디오 재팬", "duration": "8시간", "description": "해리포터, 슈퍼 닌텐도 월드"},
            {"name": "텐노지 동물원", "duration": "3시간", "description": "일본에서 가장 오래된 동물원 중 하나"},
            {"name": "아베노 하루카스", "duration": "1시간", "description": "일본에서 가장 높은 빌딩, 전망대"},
            {"name": "구로몬 시장", "duration": "2시간", "description": "오사카의 부엌, 신선한 해산물"},
        ],
        "food": [
            {"name": "타코야키 맛집", "duration": "1시간", "description": "문어가 들어간 오사카 명물"},
            {"name": "오코노미야키 맛집", "duration": "1시간", "description": "철판에 구운 일본식 전"},
            {"name": "쿠시카츠 맛집", "duration": "1시간", "description": "꼬치 튀김, 난바 소스에 찍어 먹는"},
            {"name": "라멘 이치란", "duration": "1시간", "description": "개인 칸막이에서 즐기는 돈코츠 라멘"},
            {"name": "카이센동 (해산물 덮밥)", "duration": "1시간", "description": "신선한 회 덮밥"},
        ],
        "shopping": [
            {"name": "신사이바시 쇼핑", "duration": "3시간", "description": "패션, 잡화, 드럭스토어"},
            {"name": "돈키호테", "duration": "2시간", "description": "디스카운트 스토어, 다양한 상품"},
            {"name": "난바 파크스", "duration": "2시간", "description": "대형 쇼핑몰, 루프탑 가든"},
        ],
    },
    "도쿄": {
        "sightseeing": [
            {"name": "센소지", "duration": "2시간", "description": "도쿄에서 가장 오래된 절, 아사쿠사"},
            {"name": "도쿄 스카이트리", "duration": "2시간", "description": "634m 높이의 전망대"},
            {"name": "시부야 스크램블 교차로", "duration": "1시간", "description": "세계에서 가장 바쁜 교차로"},
            {"name": "메이지 신궁", "duration": "2시간", "description": "도심 속 힐링 공간, 하라주쿠"},
            {"name": "도쿄타워", "duration": "1.5시간", "description": "도쿄의 상징, 야경 명소"},
            {"name": "우에노 공원", "duration": "3시간", "description": "박물관, 동물원, 벚꽃 명소"},
            {"name": "츠키지 시장", "duration": "2시간", "description": "신선한 해산물과 먹거리"},
        ],
        "food": [
            {"name": "스시 오마카세", "duration": "1.5시간", "description": "셰프에게 맡기는 초밥 코스"},
            {"name": "라멘 요코초", "duration": "1시간", "description": "다양한 라멘을 한 곳에서"},
            {"name": "규카츠", "duration": "1시간", "description": "소고기 커틀릿"},
            {"name": "몬자야키", "duration": "1시간", "description": "도쿄식 철판 요리"},
            {"name": "야키토리 골목", "duration": "1.5시간", "description": "꼬치구이와 사케"},
        ],
        "shopping": [
            {"name": "하라주쿠 타케시타 거리", "duration": "2시간", "description": "트렌디한 패션의 중심"},
            {"name": "긴자 쇼핑", "duration": "3시간", "description": "고급 브랜드 쇼핑가"},
            {"name": "아키하바라", "duration": "3시간", "description": "전자제품, 애니메이션, 게임"},
        ],
    },
    "방콕": {
        "sightseeing": [
            {"name": "왓 프라깨우 (에메랄드 사원)", "duration": "2시간", "description": "태국에서 가장 신성한 사원"},
            {"name": "왕궁", "duration": "2시간", "description": "화려한 태국 건축의 정수"},
            {"name": "왓 아룬", "duration": "1.5시간", "description": "새벽 사원, 아름다운 일몰"},
            {"name": "짜뚜짝 시장", "duration": "4시간", "description": "세계 최대 규모의 주말 시장"},
            {"name": "카오산 로드", "duration": "3시간", "description": "배낭여행자의 성지"},
            {"name": "짐 톰슨 하우스", "duration": "1.5시간", "description": "태국 실크 왕의 저택"},
        ],
        "food": [
            {"name": "팟타이", "duration": "1시간", "description": "태국식 볶음 쌀국수"},
            {"name": "똠얌꿍", "duration": "1시간", "description": "새우 들어간 매콤한 수프"},
            {"name": "망고 스티키 라이스", "duration": "0.5시간", "description": "달콤한 태국 디저트"},
            {"name": "길거리 음식 투어", "duration": "2시간", "description": "다양한 로컬 음식 체험"},
            {"name": "루프탑 바", "duration": "2시간", "description": "방콕 야경과 칵테일"},
        ],
        "shopping": [
            {"name": "터미널 21", "duration": "3시간", "description": "공항 테마 쇼핑몰"},
            {"name": "씨암 파라곤", "duration": "3시간", "description": "럭셔리 쇼핑몰"},
            {"name": "아시아티크", "duration": "3시간", "description": "강변 야시장"},
        ],
    },
    "제주": {
        "sightseeing": [
            {"name": "성산일출봉", "duration": "2시간", "description": "유네스코 세계자연유산"},
            {"name": "한라산", "duration": "6시간", "description": "대한민국 최고봉 등반"},
            {"name": "만장굴", "duration": "1시간", "description": "세계 최장의 용암동굴"},
            {"name": "우도", "duration": "4시간", "description": "아름다운 섬 안의 섬"},
            {"name": "주상절리대", "duration": "1시간", "description": "기둥 모양의 절벽"},
            {"name": "협재해변", "duration": "2시간", "description": "에메랄드빛 해변"},
        ],
        "food": [
            {"name": "흑돼지 구이", "duration": "1.5시간", "description": "제주 대표 먹거리"},
            {"name": "해물뚝배기", "duration": "1시간", "description": "신선한 해산물 요리"},
            {"name": "고기국수", "duration": "1시간", "description": "제주 소울푸드"},
            {"name": "빙떡", "duration": "0.5시간", "description": "메밀전에 무채 싸먹는"},
            {"name": "카페 투어", "duration": "2시간", "description": "제주 감성 카페"},
        ],
        "shopping": [
            {"name": "동문시장", "duration": "2시간", "description": "제주 전통시장, 야시장"},
            {"name": "애월 카페거리", "duration": "2시간", "description": "카페와 소품샵"},
        ],
    },
}

# 기본 장소 데이터 (목적지가 없을 경우)
DEFAULT_SPOTS = {
    "sightseeing": [
        {"name": "시내 관광", "duration": "2시간", "description": "주요 명소 둘러보기"},
        {"name": "전망대", "duration": "1시간", "description": "도시 전경 감상"},
    ],
    "food": [
        {"name": "현지 맛집", "duration": "1시간", "description": "현지 대표 음식"},
        {"name": "카페", "duration": "1시간", "description": "휴식과 커피"},
    ],
    "shopping": [
        {"name": "쇼핑몰", "duration": "2시간", "description": "쇼핑과 기념품"},
    ],
}


def get_spots_for_style(destination: str, travel_style: list[str]) -> dict:
    """여행 스타일에 맞는 장소 가져오기."""
    spots = DESTINATION_SPOTS.get(destination, DEFAULT_SPOTS)

    # 여행 스타일에 따른 장소 비중 조정
    style_mapping = {
        "관광": "sightseeing",
        "맛집": "food",
        "쇼핑": "shopping",
        "휴양": "sightseeing",  # 휴양은 관광지 중 편한 곳으로
        "액티비티": "sightseeing",
        "문화": "sightseeing",
    }

    relevant_spots = {}
    for style in travel_style:
        category = style_mapping.get(style, "sightseeing")
        if category in spots:
            relevant_spots[category] = spots[category]

    # 최소한 관광과 음식은 포함
    if "sightseeing" not in relevant_spots:
        relevant_spots["sightseeing"] = spots.get("sightseeing", DEFAULT_SPOTS["sightseeing"])
    if "food" not in relevant_spots:
        relevant_spots["food"] = spots.get("food", DEFAULT_SPOTS["food"])

    return relevant_spots


def create_activity(
    time: str,
    name: str,
    activity_type: str,
    location: str = "",
    duration: str = "1시간",
    description: str = "",
) -> Activity:
    """Activity 객체 생성."""
    return Activity(
        time=time,
        activity=name,
        type=activity_type,
        location=location if location else None,
        duration=duration if duration else None,
        description=description if description else None,
    )


def generate_day_plan(
    day_num: int,
    date: str,
    destination: str,
    spots: dict,
    is_first_day: bool = False,
    is_last_day: bool = False,
    travel_style: list[str] = None,
) -> DayPlan:
    """하루 일정 생성."""
    import random

    activities = []
    travel_style = travel_style or []

    if is_first_day:
        # 첫날: 오후부터 시작
        activities.append(create_activity(
            time="09:00",
            name="인천공항 출발",
            activity_type="transport",
            description="출국 수속 및 탑승",
        ))
        activities.append(create_activity(
            time="12:00",
            name=f"{destination} 도착",
            activity_type="transport",
            description="입국 수속 및 숙소 이동",
        ))
        activities.append(create_activity(
            time="14:00",
            name="숙소 체크인",
            activity_type="rest",
            duration="1시간",
            description="짐 정리 및 휴식",
        ))

        # 오후 활동
        sightseeing_spots = spots.get("sightseeing", [])
        if sightseeing_spots:
            spot = random.choice(sightseeing_spots)
            activities.append(create_activity(
                time="15:00",
                name=spot["name"],
                activity_type="sightseeing",
                location=spot["name"],
                duration=spot["duration"],
                description=spot["description"],
            ))

        food_spots = spots.get("food", [])
        if food_spots:
            spot = random.choice(food_spots)
            activities.append(create_activity(
                time="18:00",
                name=f"저녁 - {spot['name']}",
                activity_type="food",
                location=spot["name"],
                duration=spot["duration"],
                description=spot["description"],
            ))

        theme = f"도착 & {destination} 첫 탐방"

    elif is_last_day:
        # 마지막 날: 오전까지
        food_spots = spots.get("food", [])
        if food_spots:
            spot = random.choice(food_spots)
            activities.append(create_activity(
                time="08:00",
                name=f"아침 식사 - {spot['name']}",
                activity_type="food",
                location=spot["name"],
                duration="1시간",
                description=spot["description"],
            ))

        activities.append(create_activity(
            time="10:00",
            name="숙소 체크아웃",
            activity_type="rest",
            duration="30분",
            description="짐 챙기기",
        ))

        shopping_spots = spots.get("shopping", [])
        if shopping_spots:
            spot = random.choice(shopping_spots)
            activities.append(create_activity(
                time="10:30",
                name=f"마지막 쇼핑 - {spot['name']}",
                activity_type="shopping",
                location=spot["name"],
                duration="1시간",
                description=spot["description"],
            ))

        activities.append(create_activity(
            time="12:00",
            name="공항 이동",
            activity_type="transport",
            description="공항 버스 또는 택시",
        ))
        activities.append(create_activity(
            time="15:00",
            name="인천공항 도착",
            activity_type="transport",
            description="귀국 완료",
        ))

        theme = "마지막 쇼핑 & 귀국"

    else:
        # 중간 날: 하루 종일
        # 아침
        food_spots = spots.get("food", [])
        if food_spots:
            spot = random.choice(food_spots)
            activities.append(create_activity(
                time="08:00",
                name=f"아침 식사",
                activity_type="food",
                duration="1시간",
                description="호텔 조식 또는 현지 식당",
            ))

        # 오전 관광
        sightseeing_spots = spots.get("sightseeing", [])
        random.shuffle(sightseeing_spots)
        for i, spot in enumerate(sightseeing_spots[:2]):
            time = f"{9 + i * 2:02d}:00"
            activities.append(create_activity(
                time=time,
                name=spot["name"],
                activity_type="sightseeing",
                location=spot["name"],
                duration=spot["duration"],
                description=spot["description"],
            ))

        # 점심
        if food_spots:
            spot = random.choice(food_spots)
            activities.append(create_activity(
                time="12:30",
                name=f"점심 - {spot['name']}",
                activity_type="food",
                location=spot["name"],
                duration=spot["duration"],
                description=spot["description"],
            ))

        # 오후 활동 (스타일에 따라)
        if "쇼핑" in travel_style:
            shopping_spots = spots.get("shopping", [])
            if shopping_spots:
                spot = random.choice(shopping_spots)
                activities.append(create_activity(
                    time="14:00",
                    name=spot["name"],
                    activity_type="shopping",
                    location=spot["name"],
                    duration=spot["duration"],
                    description=spot["description"],
                ))
        else:
            if len(sightseeing_spots) > 2:
                spot = sightseeing_spots[2]
                activities.append(create_activity(
                    time="14:00",
                    name=spot["name"],
                    activity_type="sightseeing",
                    location=spot["name"],
                    duration=spot["duration"],
                    description=spot["description"],
                ))

        # 저녁
        if food_spots:
            spot = random.choice(food_spots)
            activities.append(create_activity(
                time="18:30",
                name=f"저녁 - {spot['name']}",
                activity_type="food",
                location=spot["name"],
                duration=spot["duration"],
                description=spot["description"],
            ))

        # 야간 활동
        if "맛집" in travel_style or "쇼핑" in travel_style:
            activities.append(create_activity(
                time="20:00",
                name="야경 감상 & 산책",
                activity_type="sightseeing",
                duration="1시간",
                description="도심 야경 즐기기",
            ))

        theme = f"Day {day_num} - {destination} 탐방"

    return DayPlan(
        date=date,
        theme=theme,
        activities=activities,
    )


def generate_itinerary(
    destination: str,
    duration: int,
    travel_style: list[str],
    departure_date: str | None = None,
) -> dict[str, DayPlan]:
    """여행 일정 생성 (MVP: 하드코딩 데이터).

    Args:
        destination: 목적지
        duration: 여행 기간 (박)
        travel_style: 여행 스타일 리스트
        departure_date: 출발일 (없으면 30일 후)

    Returns:
        day1, day2, ... 형식의 일정
    """
    # 날짜 계산
    if departure_date:
        start_date = datetime.strptime(departure_date, "%Y-%m-%d")
    else:
        start_date = datetime.now() + timedelta(days=30)

    total_days = duration + 1  # N박 N+1일

    # 스타일에 맞는 장소 가져오기
    spots = get_spots_for_style(destination, travel_style)

    # 일정 생성
    itinerary = {}
    for day_num in range(1, total_days + 1):
        date = (start_date + timedelta(days=day_num - 1)).strftime("%Y-%m-%d")
        is_first = day_num == 1
        is_last = day_num == total_days

        day_plan = generate_day_plan(
            day_num=day_num,
            date=date,
            destination=destination,
            spots=spots,
            is_first_day=is_first,
            is_last_day=is_last,
            travel_style=travel_style,
        )
        itinerary[f"day{day_num}"] = day_plan

    return itinerary


def plan_itinerary_node(state: TravelState) -> dict:
    """일정 생성 Node.

    항공권, 숙박 검색 후 일정을 생성합니다.
    """
    # 정보 수집이 완료되지 않았으면 스킵
    if not state.get("info_collected"):
        return {}

    # 이미 일정이 생성되었으면 스킵
    if state.get("itinerary"):
        return {}

    destination = state.get("destination", "")
    duration = state.get("duration", 3)
    travel_style = state.get("travel_style", ["관광"])

    if not destination:
        return {
            "error": "목적지 정보가 없습니다.",
            "current_step": "done",
        }

    try:
        logger.info(
            f"Planning itinerary for {destination}, {duration} nights, styles: {travel_style}"
        )

        itinerary = generate_itinerary(
            destination=destination,
            duration=duration,
            travel_style=travel_style,
        )

        logger.info(f"Created itinerary with {len(itinerary)} days")

        return {
            "itinerary": itinerary,
            "current_step": "done",
            "messages": [
                {
                    "role": "assistant",
                    "content": f"📅 {duration}박 {duration + 1}일 일정이 완성되었습니다! 결과를 정리해드릴게요.",
                }
            ],
        }

    except Exception as e:
        logger.error(f"Itinerary planning failed: {e}")
        return {
            "error": f"일정 생성 실패: {str(e)}",
            "itinerary": {},
            "current_step": "done",
            "messages": [
                {
                    "role": "assistant",
                    "content": "일정을 생성하는 데 문제가 발생했습니다.",
                }
            ],
        }


async def plan_itinerary_with_llm(state: TravelState) -> dict:
    """LLM을 사용한 일정 생성 (선택적).

    더 자연스럽고 맞춤화된 일정을 원할 경우 LLM을 사용합니다.
    """
    if not settings.openai_api_key:
        return plan_itinerary_node(state)

    destination = state.get("destination", "")
    duration = state.get("duration", 3)
    travel_style = state.get("travel_style", ["관광"])

    try:
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4-turbo-preview",
            temperature=0.8,
        )

        prompt = ITINERARY_PLANNER_USER_PROMPT.format(
            destination=destination,
            duration=duration,
            days=duration + 1,
            travel_style=", ".join(travel_style),
        )

        response = await llm.ainvoke([
            SystemMessage(content=ITINERARY_PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        # LLM 응답 파싱
        itinerary = json.loads(response.content)

        return {
            "itinerary": itinerary,
            "current_step": "done",
            "messages": [
                {
                    "role": "assistant",
                    "content": f"📅 AI가 {duration}박 {duration + 1}일 맞춤 일정을 생성했습니다!",
                }
            ],
        }

    except Exception as e:
        logger.warning(f"LLM itinerary planning failed: {e}, falling back to rule-based")
        return plan_itinerary_node(state)
