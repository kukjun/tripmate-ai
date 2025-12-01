"""Information Collector Agent for Phase 1.

사용자와 대화하며 여행 정보를 수집하는 Agent입니다.
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.models.state import TravelState
from src.utils.prompts import INFO_COLLECTOR_SYSTEM_PROMPT, INFO_COLLECTOR_USER_PROMPT

logger = logging.getLogger(__name__)

# 도시명 매핑 (한글 -> 영어)
CITY_MAPPING = {
    "오사카": "오사카",
    "osaka": "오사카",
    "도쿄": "도쿄",
    "tokyo": "도쿄",
    "교토": "교토",
    "kyoto": "교토",
    "방콕": "방콕",
    "bangkok": "방콕",
    "파리": "파리",
    "paris": "파리",
    "런던": "런던",
    "london": "런던",
    "뉴욕": "뉴욕",
    "new york": "뉴욕",
    "하와이": "하와이",
    "hawaii": "하와이",
    "괌": "괌",
    "guam": "괌",
    "싱가포르": "싱가포르",
    "singapore": "싱가포르",
    "홍콩": "홍콩",
    "hongkong": "홍콩",
    "제주": "제주",
    "jeju": "제주",
    "다낭": "다낭",
    "danang": "다낭",
    "발리": "발리",
    "bali": "발리",
    "세부": "세부",
    "cebu": "세부",
}

# 여행 스타일 키워드
TRAVEL_STYLES = ["관광", "맛집", "쇼핑", "휴양", "액티비티", "문화", "자연", "역사"]


def extract_destination(text: str) -> str | None:
    """텍스트에서 목적지 추출."""
    text_lower = text.lower()
    for keyword, city in CITY_MAPPING.items():
        if keyword in text_lower:
            return city
    return None


def extract_duration(text: str) -> int | None:
    """텍스트에서 기간(박) 추출."""
    # "3박", "3박4일", "3박 4일" 패턴
    patterns = [
        r"(\d+)\s*박",
        r"(\d+)\s*일",  # "3일" -> 2박으로 변환
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            num = int(match.group(1))
            if "일" in pattern and "박" not in text:
                # 일만 있는 경우 박으로 변환 (3일 -> 2박)
                return max(1, num - 1)
            return num
    return None


def extract_budget(text: str) -> int | None:
    """텍스트에서 예산 추출."""
    # "100만원", "100만", "1000000원", "백만원" 등
    patterns = [
        (r"(\d+)\s*만\s*원?", 10000),  # 100만원 -> 1000000
        (r"(\d{4,})\s*원?", 1),  # 1000000원 -> 1000000
    ]

    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1)) * multiplier

    # 텍스트로 된 숫자
    text_nums = {
        "백만": 1000000,
        "이백만": 2000000,
        "삼백만": 3000000,
        "오십만": 500000,
    }
    for word, value in text_nums.items():
        if word in text:
            return value

    return None


def extract_num_people(text: str) -> int | None:
    """텍스트에서 인원 추출."""
    # "2명", "둘이서", "혼자", "가족" 등
    patterns = [
        (r"(\d+)\s*명", lambda x: int(x)),
        (r"(\d+)\s*인", lambda x: int(x)),
    ]

    for pattern, converter in patterns:
        match = re.search(pattern, text)
        if match:
            return converter(match.group(1))

    # 텍스트 매칭
    if "혼자" in text or "나혼자" in text:
        return 1
    if "둘" in text or "커플" in text:
        return 2
    if "셋" in text:
        return 3
    if "넷" in text or "가족" in text:
        return 4

    return None


def extract_travel_style(text: str) -> list[str] | None:
    """텍스트에서 여행 스타일 추출."""
    found_styles = []
    for style in TRAVEL_STYLES:
        if style in text:
            found_styles.append(style)

    # 동의어 처리
    if "먹방" in text or "음식" in text or "맛있는" in text:
        if "맛집" not in found_styles:
            found_styles.append("맛집")
    if "구경" in text or "명소" in text:
        if "관광" not in found_styles:
            found_styles.append("관광")
    if "쉬" in text or "휴식" in text:
        if "휴양" not in found_styles:
            found_styles.append("휴양")

    return found_styles if found_styles else None


def get_missing_fields(state: TravelState) -> list[str]:
    """아직 수집되지 않은 필드 목록 반환."""
    missing = []

    if not state.get("destination"):
        missing.append("destination")
    if not state.get("duration") or state.get("duration", 0) == 0:
        missing.append("duration")
    if not state.get("budget") or state.get("budget", 0) == 0:
        missing.append("budget")
    if not state.get("num_people") or state.get("num_people", 0) == 0:
        missing.append("num_people")
    if not state.get("travel_style"):
        missing.append("travel_style")

    return missing


def validate_field(field: str, value: Any) -> tuple[bool, str | None]:
    """필드 값 검증."""
    if field == "duration":
        if not isinstance(value, int) or value < 1 or value > 14:
            return False, "기간은 1박에서 14박 사이여야 합니다."
    elif field == "budget":
        if not isinstance(value, int) or value < 100000 or value > 10000000:
            return False, "예산은 10만원에서 1000만원 사이여야 합니다."
    elif field == "num_people":
        if not isinstance(value, int) or value < 1 or value > 10:
            return False, "인원은 1명에서 10명 사이여야 합니다."

    return True, None


def generate_next_question(missing_fields: list[str]) -> str:
    """다음 질문 생성."""
    questions = {
        "destination": "어디로 여행을 가고 싶으세요? (예: 오사카, 도쿄, 방콕 등)",
        "duration": "몇 박 며칠로 여행을 계획하고 계세요?",
        "budget": "1인 기준 예산은 얼마 정도 생각하고 계세요? (예: 100만원)",
        "num_people": "몇 분이서 여행하시나요?",
        "travel_style": "어떤 스타일의 여행을 원하세요? (관광/맛집/쇼핑/휴양 등)",
    }

    if missing_fields:
        return questions.get(missing_fields[0], "더 필요한 정보가 있으신가요?")
    return "정보 수집이 완료되었습니다! 최적의 여행 계획을 찾아볼게요."


def info_collector_node(state: TravelState) -> dict:
    """정보 수집 Node.

    사용자 메시지에서 여행 정보를 추출하고,
    아직 수집되지 않은 정보에 대해 질문합니다.
    """
    # 이미 정보 수집이 완료된 경우 스킵
    if state.get("info_collected"):
        return {}

    # 메시지가 없으면 첫 인사 메시지 반환
    messages = state.get("messages", [])
    if not messages:
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "안녕하세요! 여행 계획을 도와드리겠습니다. 어디로 여행을 가고 싶으세요?",
                }
            ]
        }

    # 마지막 사용자 메시지 가져오기
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "어디로 여행을 가고 싶으세요?",
                }
            ]
        }

    last_user_message = user_messages[-1]["content"]

    # 정보 추출
    updates: dict[str, Any] = {}

    # 목적지 추출
    if not state.get("destination"):
        destination = extract_destination(last_user_message)
        if destination:
            updates["destination"] = destination

    # 기간 추출
    if not state.get("duration") or state.get("duration", 0) == 0:
        duration = extract_duration(last_user_message)
        if duration:
            is_valid, error = validate_field("duration", duration)
            if is_valid:
                updates["duration"] = duration

    # 예산 추출
    if not state.get("budget") or state.get("budget", 0) == 0:
        budget = extract_budget(last_user_message)
        if budget:
            is_valid, error = validate_field("budget", budget)
            if is_valid:
                updates["budget"] = budget

    # 인원 추출
    if not state.get("num_people") or state.get("num_people", 0) == 0:
        num_people = extract_num_people(last_user_message)
        if num_people:
            is_valid, error = validate_field("num_people", num_people)
            if is_valid:
                updates["num_people"] = num_people

    # 여행 스타일 추출
    if not state.get("travel_style"):
        travel_style = extract_travel_style(last_user_message)
        if travel_style:
            updates["travel_style"] = travel_style

    # 현재 상태 업데이트 후 missing fields 확인
    current_state = {**state, **updates}
    missing_fields = get_missing_fields(current_state)

    # 모든 정보가 수집되었는지 확인
    if not missing_fields:
        updates["info_collected"] = True
        updates["current_step"] = "searching_flights"
        updates["messages"] = [
            {
                "role": "assistant",
                "content": f"완벽해요! {current_state.get('destination')} "
                f"{current_state.get('duration')}박 {current_state.get('duration', 0) + 1}일 여행을 "
                f"{current_state.get('num_people')}명이서, "
                f"1인 예산 {current_state.get('budget', 0):,}원으로 계획하시는군요. "
                f"여행 스타일은 {', '.join(current_state.get('travel_style', []))}이시네요! "
                "지금 최적의 여행 계획을 찾고 있습니다...",
            }
        ]
    else:
        # 다음 질문 생성
        next_question = generate_next_question(missing_fields)

        # 이전에 추출한 정보가 있으면 확인 메시지 추가
        confirmation_parts = []
        if "destination" in updates:
            confirmation_parts.append(f"{updates['destination']}")
        if "duration" in updates:
            confirmation_parts.append(f"{updates['duration']}박")
        if "budget" in updates:
            confirmation_parts.append(f"{updates['budget']:,}원")
        if "num_people" in updates:
            confirmation_parts.append(f"{updates['num_people']}명")
        if "travel_style" in updates:
            confirmation_parts.append(f"{', '.join(updates['travel_style'])}")

        if confirmation_parts:
            confirmation = f"{', '.join(confirmation_parts)} - 좋아요! "
            response = confirmation + next_question
        else:
            response = next_question

        updates["messages"] = [{"role": "assistant", "content": response}]

    logger.info(f"Info collector updates: {updates}")
    return updates


async def info_collector_node_with_llm(state: TravelState) -> dict:
    """LLM을 사용한 정보 수집 Node (선택적).

    규칙 기반 추출이 실패할 경우 LLM을 사용합니다.
    """
    # 먼저 규칙 기반으로 시도
    result = info_collector_node(state)

    # 정보가 추출되지 않고, OpenAI API 키가 있으면 LLM 사용
    if (
        not result.get("destination")
        and not result.get("duration")
        and not result.get("budget")
        and not result.get("num_people")
        and not result.get("travel_style")
        and settings.openai_api_key
    ):
        try:
            llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4-turbo-preview",
                temperature=0.7,
            )

            # 현재 상태 정보 포맷팅
            current_info = {
                "destination": state.get("destination") or "미정",
                "duration": f"{state.get('duration')}박" if state.get("duration") else "미정",
                "budget": f"{state.get('budget'):,}원" if state.get("budget") else "미정",
                "num_people": f"{state.get('num_people')}명" if state.get("num_people") else "미정",
                "travel_style": ", ".join(state.get("travel_style", [])) or "미정",
            }

            messages = state.get("messages", [])
            user_message = messages[-1]["content"] if messages else ""

            prompt = INFO_COLLECTOR_USER_PROMPT.format(
                user_message=user_message,
                **current_info,
            )

            response = await llm.ainvoke([
                SystemMessage(content=INFO_COLLECTOR_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])

            # LLM 응답 파싱
            try:
                llm_result = json.loads(response.content)
                extracted = llm_result.get("extracted_info", {})

                if extracted.get("destination"):
                    result["destination"] = extracted["destination"]
                if extracted.get("duration"):
                    result["duration"] = int(extracted["duration"])
                if extracted.get("budget"):
                    result["budget"] = int(extracted["budget"])
                if extracted.get("num_people"):
                    result["num_people"] = int(extracted["num_people"])
                if extracted.get("travel_style"):
                    result["travel_style"] = extracted["travel_style"]

                if llm_result.get("response"):
                    result["messages"] = [
                        {"role": "assistant", "content": llm_result["response"]}
                    ]

                if llm_result.get("info_complete"):
                    result["info_collected"] = True
                    result["current_step"] = "searching_flights"

            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON")

        except Exception as e:
            logger.error(f"LLM info extraction failed: {e}")

    return result
