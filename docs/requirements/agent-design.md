# Agent 설계 문서

## 1. 개요

각 Agent는 특정 역할과 책임을 가지며, LangGraph를 통해 협업합니다.

**설계 원칙:**
- Single Responsibility: 각 Agent는 하나의 명확한 역할
- Stateless: Agent는 State에만 의존, 내부 상태 없음
- Composable: Agent를 조합하여 복잡한 워크플로우 구성

---

## 2. Phase 1: Single Agent 구조

### 2.1 Info Collector

**역할**: 사용자와 대화하며 여행 정보 수집

**Input:**
```python
{
    "messages": [...],
    "destination": None,
    "duration": None,
    ...
}
```

**Output:**
```python
{
    "destination": "오사카",
    "messages": [... + 새 질문]
}
```

**구현:**
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

INFO_COLLECTOR_PROMPT = """
당신은 친절한 여행 상담사입니다.
사용자와 대화하며 다음 정보를 수집하세요:

필수 정보:
1. 목적지 (도시명)
2. 기간 (몇 박 며칠)
3. 예산 (1인 기준, 원)
4. 인원
5. 여행 스타일 (관광/맛집/쇼핑/휴양)

현재 수집된 정보:
목적지: {destination}
기간: {duration}
예산: {budget}
인원: {num_people}
스타일: {travel_style}

사용자 메시지: {user_message}

다음에 물어볼 질문을 자연스럽게 생성하세요.
모든 정보가 수집되었다면 "정보 수집 완료"라고 말하세요.
"""

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
prompt = ChatPromptTemplate.from_template(INFO_COLLECTOR_PROMPT)

def info_collector_node(state: TravelState) -> dict:
    """정보 수집 Node"""
    
    # 이미 수집 완료면 스킵
    if state.get("info_collected"):
        return {}
    
    # 마지막 사용자 메시지
    user_message = state["messages"][-1]["content"]
    
    # LLM 호출
    chain = prompt | llm
    response = chain.invoke({
        "destination": state.get("destination", "미정"),
        "duration": state.get("duration", "미정"),
        "budget": state.get("budget", "미정"),
        "num_people": state.get("num_people", "미정"),
        "travel_style": ", ".join(state.get("travel_style", [])) or "미정",
        "user_message": user_message
    })
    
    assistant_message = response.content
    
    # "정보 수집 완료" 감지
    if "정보 수집 완료" in assistant_message:
        return {
            "info_collected": True,
            "current_step": "searching",
            "messages": [
                {"role": "assistant", "content": "완벽해요! 최적의 여행 계획을 찾고 있습니다..."}
            ]
        }
    
    # 사용자 메시지에서 정보 추출 (간단한 예시)
    updates = extract_info(user_message, state)
    
    # 메시지 추가
    updates["messages"] = [
        {"role": "assistant", "content": assistant_message}
    ]
    
    return updates

def extract_info(user_message: str, state: dict) -> dict:
    """사용자 메시지에서 정보 추출 (규칙 기반 or LLM)"""
    
    updates = {}
    
    # 목적지 추출 (예시)
    cities = ["오사카", "도쿄", "방콕", "제주"]
    for city in cities:
        if city in user_message:
            updates["destination"] = city
            break
    
    # 기간 추출
    import re
    duration_match = re.search(r'(\d+)박', user_message)
    if duration_match:
        updates["duration"] = int(duration_match.group(1))
    
    # 예산 추출
    budget_match = re.search(r'(\d+)만원', user_message)
    if budget_match:
        updates["budget"] = int(budget_match.group(1)) * 10000
    
    # 인원 추출
    people_match = re.search(r'(\d+)명', user_message)
    if people_match:
        updates["num_people"] = int(people_match.group(1))
    
    # 여행 스타일
    styles = ["관광", "맛집", "쇼핑", "휴양"]
    found_styles = [s for s in styles if s in user_message]
    if found_styles:
        updates["travel_style"] = found_styles
    
    return updates
```

---

### 2.2 Flight Searcher

**역할**: 항공권 검색

**Input:**
```python
{
    "destination": "오사카",
    "duration": 3,
    "info_collected": True
}
```

**Output:**
```python
{
    "flight_options": [
        {"type": "budget", "price": 250000, ...},
        {"type": "standard", "price": 350000, ...},
        {"type": "premium", "price": 500000, ...}
    ],
    "flights_searched": True
}
```

**구현:**
```python
from datetime import datetime, timedelta
from src.tools.flight_api import search_flights_naver

def search_flights_node(state: TravelState) -> dict:
    """항공권 검색 Node"""
    
    # 이미 검색했으면 스킵
    if state.get("flight_options"):
        return {}
    
    # 날짜 계산 (오늘 + 30일 출발)
    departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=30 + state["duration"] + 1)).strftime("%Y-%m-%d")
    
    try:
        # 외부 API/크롤링 호출
        flights = search_flights_naver(
            origin="ICN",
            destination=get_airport_code(state["destination"]),
            departure_date=departure_date,
            return_date=return_date
        )
        
        # 3개 옵션으로 필터링 (저가/중가/고가)
        budget = min(flights, key=lambda x: x["price"])
        premium = max(flights, key=lambda x: x["price"])
        standard = sorted(flights, key=lambda x: x["price"])[len(flights)//2]
        
        return {
            "flight_options": [
                {**budget, "type": "budget"},
                {**standard, "type": "standard"},
                {**premium, "type": "premium"}
            ],
            "flights_searched": True
        }
    
    except Exception as e:
        logger.error(f"Flight search failed: {e}")
        return {
            "errors": [f"항공권 검색 실패: {str(e)}"],
            "flight_options": []
        }

def get_airport_code(city: str) -> str:
    """도시 → 공항 코드 매핑"""
    mapping = {
        "오사카": "KIX",
        "도쿄": "NRT",
        "방콕": "BKK",
        "제주": "CJU"
    }
    return mapping.get(city, city)
```

---

### 2.3 Hotel Searcher

**역할**: 숙박 검색

**구현:** (Flight Searcher와 유사)
```python
def search_hotels_node(state: TravelState) -> dict:
    """숙박 검색 Node"""
    
    if state.get("hotel_options"):
        return {}
    
    try:
        hotels = search_hotels_booking(
            destination=state["destination"],
            checkin=calculate_checkin(state),
            checkout=calculate_checkout(state),
            guests=state["num_people"]
        )
        
        # 3개 옵션
        return {
            "hotel_options": [
                {**min(hotels, key=lambda x: x["price"]), "type": "budget"},
                {**sorted(hotels, key=lambda x: x["price"])[len(hotels)//2], "type": "standard"},
                {**max(hotels, key=lambda x: x["price"]), "type": "premium"}
            ],
            "hotels_searched": True
        }
    
    except Exception as e:
        return {
            "errors": [f"숙박 검색 실패: {str(e)}"],
            "hotel_options": []
        }
```

---

### 2.4 Itinerary Planner

**역할**: 일정 생성

**Input:**
```python
{
    "destination": "오사카",
    "duration": 3,
    "travel_style": ["관광", "맛집"]
}
```

**Output:**
```python
{
    "itinerary": {
        "day1": {...},
        "day2": {...},
        "day3": {...}
    }
}
```

**구현:**
```python
ITINERARY_PROMPT = """
다음 정보로 {duration}박 {duration_plus_one}일 여행 일정을 생성하세요.

목적지: {destination}
여행 스타일: {travel_style}

요구사항:
- 첫날은 오후부터 (오전 도착 가정)
- 마지막 날은 오전까지 (오후 출발 가정)
- 하루 4-6개 활동
- 시간대별 상세 일정
- 각 활동의 간단한 설명 포함
- {travel_style}에 맞는 활동 우선

JSON 형식으로 출력:
{{
  "day1": {{
    "date": "2024-12-20",
    "theme": "도착 & 시내 탐방",
    "activities": [
      {{
        "time": "09:00",
        "activity": "인천공항 출발",
        "type": "transport"
      }},
      ...
    ]
  }},
  ...
}}
"""

from langchain_core.output_parsers import JsonOutputParser

def plan_itinerary_node(state: TravelState) -> dict:
    """일정 생성 Node"""
    
    if state.get("itinerary"):
        return {}
    
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.8)
    prompt = ChatPromptTemplate.from_template(ITINERARY_PROMPT)
    parser = JsonOutputParser()
    
    chain = prompt | llm | parser
    
    try:
        itinerary = chain.invoke({
            "destination": state["destination"],
            "duration": state["duration"],
            "duration_plus_one": state["duration"] + 1,
            "travel_style": ", ".join(state["travel_style"])
        })
        
        return {
            "itinerary": itinerary,
            "itinerary_planned": True,
            "current_step": "done"
        }
    
    except Exception as e:
        return {
            "errors": [f"일정 생성 실패: {str(e)}"],
            "itinerary": {}
        }
```

---

## 3. Phase 2: Multi Agent 구조

### 3.1 Travel Consultant (메인 진행자)

**역할**: 전체 프로세스 오케스트레이션

**구현:**
```python
def travel_consultant_node(state: MultiAgentTravelState) -> dict:
    """메인 상담사 - 다음 단계 결정"""
    
    # 정보 수집 단계
    if not state.get("info_collected"):
        return {"next_agent": "needs_collector"}
    
    # 검색 단계 - Router에게 위임
    if not state.get("plans_generated"):
        return {"next_agent": "router"}
    
    # 완료
    return {"next_agent": "END"}
```

---

### 3.2 Router (라우터)

**역할**: Conditional routing - 다음 Agent 결정

**구현:**
```python
def router_node(state: MultiAgentTravelState) -> dict:
    """라우터 - 다음 실행할 Agent 결정"""
    
    # 병렬 실행 가능한 Agent들
    pending = []
    
    if not state.get("flights_searched"):
        pending.append("flight_expert")
    
    if not state.get("hotels_searched"):
        pending.append("hotel_expert")
    
    # 병렬 실행
    if pending:
        return {
            "next_agent": pending  # 리스트로 반환 → 병렬 실행
        }
    
    # 순차 실행
    if not state.get("itinerary_planned"):
        return {"next_agent": "itinerary_planner"}
    
    if not state.get("budget_analyzed"):
        return {"next_agent": "budget_manager"}
    
    # 최종 조율
    if not state.get("plans_generated"):
        return {"next_agent": "coordinator"}
    
    # 완료
    return {"next_agent": "consultant"}
```

---

### 3.3 Flight Expert (항공 전문가)

**역할**: 항공권 검색 + 분석 + 추천

**Phase 1과 차이점:**
- 단순 검색 → 분석 + 추천
- 추천 이유 제공
- 팁 제공

**구현:**
```python
FLIGHT_EXPERT_PROMPT = """
당신은 항공권 전문가입니다.

검색 결과:
{flight_options}

사용자 정보:
- 예산: {budget}원
- 선호 항공사: {preferred_airline}
- 예산 유연성: {budget_flexibility}

다음을 수행하세요:
1. 가성비 최고 옵션 선택
2. 선택 이유 설명
3. 다른 옵션과 비교
4. 예약 팁 제공

JSON 형식:
{{
  "recommendation": "standard",
  "reasoning": "...",
  "alternatives": [...],
  "tips": [...]
}}
"""

def flight_expert_node(state: MultiAgentTravelState) -> dict:
    """Flight Expert"""
    
    # 검색 (Phase 1과 동일)
    flights = search_flights(...)
    
    # 분석 (추가)
    llm = ChatOpenAI(model="gpt-4-turbo")
    prompt = ChatPromptTemplate.from_template(FLIGHT_EXPERT_PROMPT)
    parser = JsonOutputParser()
    
    chain = prompt | llm | parser
    
    analysis = chain.invoke({
        "flight_options": flights,
        "budget": state["budget"],
        "preferred_airline": state.get("preferred_airline", "없음"),
        "budget_flexibility": state.get("budget_flexibility", "flexible")
    })
    
    return {
        "flight_options": flights,
        "flights_searched": True,
        
        # Agent별 결과 저장
        "agent_results": {
            **state.get("agent_results", {}),
            "flight_expert": {
                "options": flights,
                **analysis
            }
        }
    }
```

---

### 3.4 Hotel Expert (숙박 전문가)

**구현:** (Flight Expert와 유사 구조)
```python
def hotel_expert_node(state: MultiAgentTravelState) -> dict:
    """Hotel Expert"""
    
    hotels = search_hotels(...)
    
    # 위치 분석 추가
    location_analysis = analyze_locations(
        hotels=hotels,
        travel_style=state["travel_style"]
    )
    
    analysis = llm_analyze_hotels(hotels, location_analysis)
    
    return {
        "hotel_options": hotels,
        "hotels_searched": True,
        "agent_results": {
            **state.get("agent_results", {}),
            "hotel_expert": {
                "options": hotels,
                "location_analysis": location_analysis,
                **analysis
            }
        }
    }
```

---

### 3.5 Budget Manager (예산 관리자)

**역할**: 예산 분배 + 절약 팁

**구현:**
```python
def budget_manager_node(state: MultiAgentTravelState) -> dict:
    """Budget Manager"""
    
    # 다른 Agent 결과 참조
    flight_expert = state["agent_results"]["flight_expert"]
    hotel_expert = state["agent_results"]["hotel_expert"]
    
    selected_flight = flight_expert["recommendation"]
    selected_hotel = hotel_expert["recommendation"]
    
    # 예산 분배
    breakdown = {
        "flights": selected_flight["price"] * state["num_people"],
        "accommodation": selected_hotel["total_price"],
        "food": estimate_food_cost(state),
        "transport": estimate_transport_cost(state),
        "attractions": estimate_attraction_cost(state),
        "shopping": state["budget"] * 0.1  # 예산의 10%
    }
    
    total = sum(breakdown.values())
    remaining = (state["budget"] * state["num_people"]) - total
    
    # 절약 팁 생성
    tips = generate_savings_tips(state, breakdown)
    
    return {
        "budget_breakdown": breakdown,
        "budget_analyzed": True,
        "agent_results": {
            **state.get("agent_results", {}),
            "budget_manager": {
                "breakdown": breakdown,
                "total": total,
                "remaining": remaining,
                "tips": tips
            }
        }
    }
```

---

### 3.6 Final Coordinator (최종 조율자)

**역할**: 3가지 플랜 생성

**구현:**
```python
def final_coordinator_node(state: MultiAgentTravelState) -> dict:
    """Final Coordinator - 3가지 플랜 생성"""
    
    # 모든 Agent 결과 수집
    flight_expert = state["agent_results"]["flight_expert"]
    hotel_expert = state["agent_results"]["hotel_expert"]
    itinerary = state["itinerary"]
    budget = state["agent_results"]["budget_manager"]
    
    # 플랜 A: 럭셔리
    plan_luxury = create_plan(
        flight=flight_expert["options"][2],  # premium
        hotel=hotel_expert["options"][2],
        itinerary=enhance_itinerary(itinerary, "luxury"),
        budget_multiplier=1.5
    )
    
    # 플랜 B: 균형 (추천)
    plan_balanced = create_plan(
        flight=flight_expert["options"][1],  # standard
        hotel=hotel_expert["options"][1],
        itinerary=itinerary,
        budget_multiplier=1.0
    )
    
    # 플랜 C: 가성비
    plan_budget = create_plan(
        flight=flight_expert["options"][0],  # budget
        hotel=hotel_expert["options"][0],
        itinerary=optimize_itinerary(itinerary, "budget"),
        budget_multiplier=0.7
    )
    
    # 추천 로직
    recommendation = determine_recommendation(
        plans=[plan_luxury, plan_balanced, plan_budget],
        user_budget=state["budget"],
        user_preference=state.get("budget_flexibility")
    )
    
    return {
        "final_plans": [plan_luxury, plan_balanced, plan_budget],
        "recommendation": recommendation,
        "plans_generated": True
    }

def create_plan(flight, hotel, itinerary, budget_multiplier):
    """플랜 생성"""
    return {
        "flight": flight,
        "hotel": hotel,
        "itinerary": itinerary,
        "total_budget": calculate_total(flight, hotel, itinerary, budget_multiplier)
    }
```

---

## 4. Agent 테스트

### 4.1 Unit Test
```python
# tests/test_agents.py
import pytest

def test_info_collector_extracts_destination():
    state = {
        "destination": None,
        "messages": [
            {"role": "user", "content": "오사카 가고 싶어요"}
        ]
    }
    
    result = info_collector_node(state)
    
    assert result["destination"] == "오사카"
    assert len(result["messages"]) > 0

def test_flight_searcher_returns_3_options():
    state = {
        "destination": "오사카",
        "duration": 3,
        "flight_options": None
    }
    
    result = search_flights_node(state)
    
    assert len(result["flight_options"]) == 3
    assert result["flight_options"][0]["type"] == "budget"
```

### 4.2 Integration Test
```python
def test_full_workflow():
    """전체 워크플로우 테스트"""
    
    # 초기 State
    state = create_initial_state()
    
    # 정보 수집 시뮬레이션
    state = simulate_conversation(state, [
        "오사카",
        "3박 4일",
        "100만원",
        "2명",
        "관광 맛집"
    ])
    
    # Graph 실행
    app = create_graph()
    final_state = app.invoke(state)
    
    # 검증
    assert final_state["info_collected"]
    assert len(final_state["flight_options"]) == 3
    assert len(final_state["hotel_options"]) == 3
    assert final_state["itinerary"]
```

---

**문서 버전**: 1.0  
**작성일**: 2024-11-30  
**관련 코드**: backend/src/agents/