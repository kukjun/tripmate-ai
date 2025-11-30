# State 관리 설계

## 1. 개요

여행 플래너의 핵심은 대화를 통해 점진적으로 정보를 수집하고, 
여러 Agent가 협업하며 상태를 업데이트하는 것입니다.

LangGraph의 State는 모든 Agent가 공유하는 **단일 진실 공급원(Single Source of Truth)**입니다.

---

## 2. State 구조

### 2.1 Phase 1: Single Agent State
```python
from typing import TypedDict, Literal, Optional

class TravelState(TypedDict):
    """Phase 1 - Single Agent용 상태"""
    
    # === 사용자 입력 정보 ===
    destination: Optional[str]              # 목적지
    duration: Optional[int]                 # 기간 (박)
    budget: Optional[int]                   # 예산 (원)
    num_people: Optional[int]              # 인원
    travel_style: list[str]                # 여행 스타일
    
    # === 진행 상태 ===
    info_collected: bool                   # 정보 수집 완료 여부
    current_step: Literal[
        "collecting",      # 정보 수집 중
        "searching",       # 검색 중
        "planning",        # 일정 생성 중
        "done"            # 완료
    ]
    
    # === 검색 결과 ===
    flight_options: list[dict]             # 항공권 옵션 (3개)
    hotel_options: list[dict]              # 숙박 옵션 (3개)
    itinerary: dict                        # 일정
    
    # === 대화 히스토리 ===
    messages: list[dict]                   # 대화 기록
    
    # === 메타 정보 ===
    session_id: str
    created_at: str
    updated_at: str
    
    # === 오류 처리 ===
    errors: list[str]                      # 발생한 오류들
```

### 2.2 Phase 2: Multi Agent State
```python
class MultiAgentTravelState(TypedDict):
    """Phase 2 - Multi Agent용 상태 (Phase 1 확장)"""
    
    # === Phase 1 필드 모두 포함 ===
    # (위의 모든 필드)
    
    # === Agent 협업 관리 ===
    current_agent: str                     # 현재 실행 중인 Agent
    next_agent: str | list[str]           # 다음 Agent (단일 또는 병렬)
    agent_history: list[str]              # Agent 실행 이력
    
    # === 진행 상태 (세분화) ===
    info_collected: bool
    flights_searched: bool
    hotels_searched: bool
    itinerary_planned: bool
    budget_analyzed: bool
    plans_generated: bool
    
    # === Agent별 결과 ===
    agent_results: dict[str, dict]        # Agent별 상세 결과
    # {
    #   "flight_expert": {...},
    #   "hotel_expert": {...},
    #   ...
    # }
    
    # === Phase 2 전용 결과 ===
    flight_analysis: Optional[dict]        # Flight Expert 분석
    hotel_analysis: Optional[dict]         # Hotel Expert 분석
    itinerary_optimization: Optional[dict] # Itinerary Planner 최적화
    budget_breakdown: Optional[dict]       # Budget Manager 분석
    final_plans: list[dict]               # 3가지 플랜
    recommendation: Optional[dict]         # 추천 플랜
    
    # === 추가 사용자 정보 (Phase 2) ===
    budget_flexibility: Optional[Literal["strict", "flexible"]]
    preferred_airline: Optional[str]
    accommodation_preference: Optional[Literal["hotel", "guesthouse", "airbnb"]]
    must_visit_places: list[str]
```

---

## 3. State 업데이트 패턴

### 3.1 부분 업데이트 (Partial Update)

각 Node는 State 전체를 반환하지 않고, 변경된 부분만 반환합니다.
```python
def info_collector_node(state: TravelState) -> dict:
    """정보 수집 Node"""
    
    # 사용자 메시지에서 정보 추출
    user_message = state["messages"][-1]["content"]
    
    # 목적지 추출 예시
    if "오사카" in user_message:
        return {
            "destination": "오사카",
            "messages": state["messages"] + [
                {"role": "assistant", "content": "몇 박 며칠 계획이신가요?"}
            ]
        }
    
    # duration 추출 예시
    if "3박" in user_message:
        return {
            "duration": 3,
            "messages": state["messages"] + [
                {"role": "assistant", "content": "예산은 얼마 정도 생각하세요?"}
            ]
        }
```

**LangGraph의 자동 병합:**
```python
# 이전 State
{
    "destination": "오사카",
    "duration": None,
    "messages": [...]
}

# Node 반환값
{
    "duration": 3,
    "messages": [... 새 메시지 추가]
}

# 자동 병합 후
{
    "destination": "오사카",      # 유지
    "duration": 3,                # 업데이트
    "messages": [... 업데이트]
}
```

---

### 3.2 Reducer 패턴 (리스트 병합)

메시지나 오류 같은 리스트는 **추가(append)** 방식으로 병합:
```python
from typing import Annotated
from operator import add

class TravelState(TypedDict):
    messages: Annotated[list[dict], add]  # append로 병합
    errors: Annotated[list[str], add]
```

**동작 방식:**
```python
# 이전 State
{
    "messages": [
        {"role": "user", "content": "오사카"},
    ]
}

# Node 반환
{
    "messages": [
        {"role": "assistant", "content": "몇 박 며칠?"}
    ]
}

# 병합 결과 (add 적용)
{
    "messages": [
        {"role": "user", "content": "오사카"},
        {"role": "assistant", "content": "몇 박 며칠?"}  # 추가됨
    ]
}
```

---

### 3.3 Conditional Update (조건부 업데이트)
```python
def search_flights_node(state: TravelState) -> dict:
    """항공권 검색"""
    
    # 이미 검색했으면 스킵
    if state.get("flight_options"):
        return {}  # 변경사항 없음
    
    try:
        flights = search_flights_api(
            destination=state["destination"],
            duration=state["duration"]
        )
        
        return {
            "flight_options": flights,
            "flights_searched": True,
            "current_step": "searching"
        }
    
    except APIError as e:
        return {
            "errors": [f"항공권 검색 실패: {str(e)}"],
            "flight_options": []  # 빈 리스트로라도 설정
        }
```

---

## 4. State 검증

### 4.1 Pydantic을 이용한 검증
```python
from pydantic import BaseModel, Field, validator

class TravelStateModel(BaseModel):
    """검증 가능한 State 모델"""
    
    destination: str | None = None
    duration: int | None = Field(None, ge=1, le=14)  # 1~14박
    budget: int | None = Field(None, ge=100000, le=10000000)
    num_people: int | None = Field(None, ge=1, le=10)
    travel_style: list[str] = []
    
    @validator('duration')
    def validate_duration(cls, v):
        if v is not None and (v < 1 or v > 14):
            raise ValueError('기간은 1박~14박이어야 합니다')
        return v
    
    @validator('budget')
    def validate_budget(cls, v):
        if v is not None and v < 100000:
            raise ValueError('예산은 최소 10만원 이상이어야 합니다')
        return v
    
    def is_complete(self) -> bool:
        """정보 수집 완료 여부"""
        return all([
            self.destination,
            self.duration,
            self.budget,
            self.num_people,
            len(self.travel_style) > 0
        ])
```

### 4.2 검증 사용 예시
```python
def info_collector_node(state: TravelState) -> dict:
    """정보 수집 with 검증"""
    
    # Pydantic 모델로 변환하여 검증
    try:
        validated = TravelStateModel(**state)
    except ValidationError as e:
        return {
            "errors": [str(e)]
        }
    
    # 정보 수집 완료 체크
    if validated.is_complete():
        return {
            "info_collected": True,
            "current_step": "searching"
        }
    
    # 다음 질문 생성
    next_question = generate_next_question(validated)
    return {
        "messages": [
            {"role": "assistant", "content": next_question}
        ]
    }
```

---

## 5. State 초기화

### 5.1 새 세션 시작
```python
import uuid
from datetime import datetime

def create_initial_state(session_id: str | None = None) -> TravelState:
    """초기 State 생성"""
    
    return {
        # 사용자 정보 (모두 None/빈값)
        "destination": None,
        "duration": None,
        "budget": None,
        "num_people": None,
        "travel_style": [],
        
        # 진행 상태
        "info_collected": False,
        "current_step": "collecting",
        
        # 결과
        "flight_options": [],
        "hotel_options": [],
        "itinerary": {},
        
        # 대화
        "messages": [
            {
                "role": "assistant",
                "content": "안녕하세요! 여행 계획을 도와드리겠습니다. 어디로 여행 가고 싶으세요?"
            }
        ],
        
        # 메타
        "session_id": session_id or str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        
        # 오류
        "errors": []
    }
```

### 5.2 State 로드 (세션 복원)
```python
import json

def load_state(session_id: str) -> TravelState | None:
    """저장된 State 로드"""
    
    # JSON 파일에서 로드 (Phase 1)
    try:
        with open(f"sessions/{session_id}.json", "r") as f:
            state = json.load(f)
        return state
    except FileNotFoundError:
        return None

def save_state(state: TravelState):
    """State 저장"""
    
    session_id = state["session_id"]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    with open(f"sessions/{session_id}.json", "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
```

---

## 6. State 디버깅

### 6.1 로깅
```python
import logging

logger = logging.getLogger(__name__)

def log_state_change(node_name: str, before: dict, after: dict):
    """State 변경 로깅"""
    
    changes = {}
    for key in after:
        if before.get(key) != after.get(key):
            changes[key] = {
                "before": before.get(key),
                "after": after.get(key)
            }
    
    if changes:
        logger.info(f"[{node_name}] State changes: {changes}")
```

### 6.2 State Inspector (개발 중)
```python
class StateInspector:
    """State 변화 추적"""
    
    def __init__(self):
        self.history = []
    
    def track(self, node_name: str, state: dict):
        """State 스냅샷 저장"""
        self.history.append({
            "node": node_name,
            "timestamp": datetime.utcnow().isoformat(),
            "state": state.copy()
        })
    
    def get_field_history(self, field: str) -> list:
        """특정 필드의 변화 추적"""
        return [
            {
                "node": h["node"],
                "value": h["state"].get(field)
            }
            for h in self.history
        ]
    
    def visualize(self):
        """State 변화 시각화 (Streamlit용)"""
        import streamlit as st
        
        st.write("### State 변화 추적")
        for h in self.history:
            with st.expander(f"{h['node']} - {h['timestamp']}"):
                st.json(h['state'])
```

---

## 7. State 최적화

### 7.1 불필요한 데이터 제거
```python
def cleanup_state(state: TravelState) -> TravelState:
    """완료 후 불필요한 데이터 제거"""
    
    if state["current_step"] == "done":
        # 중간 결과 제거
        state.pop("agent_history", None)
        state.pop("errors", None)  # 오류는 로그에만
    
    return state
```

### 7.2 State 압축 (대화 히스토리)
```python
def compress_messages(messages: list[dict], max_length: int = 20) -> list[dict]:
    """대화 히스토리 압축"""
    
    if len(messages) <= max_length:
        return messages
    
    # 최근 N개만 유지
    return [
        messages[0],  # 첫 인사는 유지
        *messages[-max_length+1:]
    ]
```

---

## 8. Multi Agent State 관리

### 8.1 Agent 간 데이터 전달
```python
def flight_expert_node(state: MultiAgentTravelState) -> dict:
    """Flight Expert의 결과를 agent_results에 저장"""
    
    analysis = analyze_flights(state)
    
    return {
        "flight_options": analysis["options"],
        "flights_searched": True,
        
        # Agent별 상세 결과 저장
        "agent_results": {
            **state.get("agent_results", {}),
            "flight_expert": {
                "options": analysis["options"],
                "recommendation": analysis["best_option"],
                "reasoning": analysis["reasoning"],
                "tips": analysis["tips"]
            }
        }
    }
```

### 8.2 다른 Agent의 결과 참조
```python
def budget_manager_node(state: MultiAgentTravelState) -> dict:
    """다른 Agent 결과를 참조하여 예산 분석"""
    
    # Flight Expert 결과 가져오기
    flight_result = state["agent_results"].get("flight_expert", {})
    selected_flight = flight_result.get("recommendation", {})
    
    # Hotel Expert 결과 가져오기
    hotel_result = state["agent_results"].get("hotel_expert", {})
    selected_hotel = hotel_result.get("recommendation", {})
    
    # 예산 계산
    budget_breakdown = calculate_budget(
        flight_price=selected_flight.get("price", 0),
        hotel_price=selected_hotel.get("total_price", 0),
        duration=state["duration"],
        num_people=state["num_people"]
    )
    
    return {
        "budget_breakdown": budget_breakdown,
        "budget_analyzed": True
    }
```

---

## 9. State 버전 관리

### 9.1 State Schema 버전
```python
class TravelState(TypedDict):
    # ...
    schema_version: str  # "1.0", "2.0"

def migrate_state_v1_to_v2(state_v1: dict) -> dict:
    """State v1 → v2 마이그레이션"""
    
    state_v2 = state_v1.copy()
    
    # v2에 추가된 필드
    state_v2["budget_flexibility"] = "flexible"  # 기본값
    state_v2["schema_version"] = "2.0"
    
    return state_v2
```

---

## 10. 예시: 전체 State 변화 과정

### 초기 State
```json
{
  "destination": null,
  "duration": null,
  "budget": null,
  "info_collected": false,
  "current_step": "collecting",
  "messages": [
    {"role": "assistant", "content": "어디로 여행 가고 싶으세요?"}
  ]
}
```

### Step 1: 목적지 입력
```json
{
  "destination": "오사카",
  "messages": [
    {"role": "assistant", "content": "어디로 여행 가고 싶으세요?"},
    {"role": "user", "content": "오사카"},
    {"role": "assistant", "content": "몇 박 며칠 계획이신가요?"}
  ]
}
```

### Step 2: 기간 입력
```json
{
  "destination": "오사카",
  "duration": 3,
  "messages": [
    ...,
    {"role": "user", "content": "3박 4일"},
    {"role": "assistant", "content": "예산은 얼마 정도?"}
  ]
}
```

### Step 3: 정보 수집 완료
```json
{
  "destination": "오사카",
  "duration": 3,
  "budget": 1000000,
  "num_people": 2,
  "travel_style": ["관광", "맛집"],
  "info_collected": true,
  "current_step": "searching"
}
```

### Step 4: 항공권 검색 완료
```json
{
  ...,
  "flight_options": [
    {"type": "budget", "price": 250000, ...},
    {"type": "standard", "price": 350000, ...},
    {"type": "premium", "price": 500000, ...}
  ],
  "flights_searched": true
}
```

### Step 5: 최종 완료
```json
{
  ...,
  "flight_options": [...],
  "hotel_options": [...],
  "itinerary": {...},
  "current_step": "done"
}
```

---

**문서 버전**: 1.0  
**작성일**: 2024-11-30  
**관련 문서**: system-design.md, agent-design.md