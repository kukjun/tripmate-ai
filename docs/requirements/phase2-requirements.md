# Phase 2 요구사항 명세서 - Multi AI Agent

## 1. 개요
- **목표**: Single Agent를 Multi Agent 구조로 리팩토링
- **기간**: Week 3-4 (2024.12.15 - 2024.12.28)
- **핵심**: 역할별 전문가 Agent 분리 + 협업 구조

---

## 2. Multi Agent 아키텍처

### 2.1 Agent 구성
```
사용자 입력
    ↓
[Travel Consultant] - 메인 진행자
    ↓
[Needs Collector] - 정보 수집 전문
    ↓
[Router] - 다음 Agent 결정
    ↓
┌─────────────────────────────┐
│ [Flight Expert]             │ → 항공권 전문가
│ [Hotel Expert]              │ → 숙박 전문가
│ [Itinerary Planner]         │ → 일정 기획자
│ [Budget Manager]            │ → 예산 관리자
└─────────────────────────────┘
    ↓
[Final Coordinator] - 결과 통합 및 3가지 플랜 생성
    ↓
최종 응답
```

### 2.2 Agent별 역할

| Agent | 역할 | 입력 | 출력 |
|-------|------|------|------|
| Travel Consultant | 전체 진행 관리 | 사용자 메시지 | 다음 단계 지시 |
| Needs Collector | 정보 수집 | 대화 히스토리 | TravelState (완성) |
| Router | 라우팅 결정 | State | 다음 Agent 이름 |
| Flight Expert | 항공권 분석 | State | 항공권 옵션 + 추천 |
| Hotel Expert | 숙박 분석 | State | 숙박 옵션 + 추천 |
| Itinerary Planner | 일정 기획 | State | 일정 + 동선 최적화 |
| Budget Manager | 예산 분배 | State + 검색 결과 | 예산 breakdown |
| Final Coordinator | 결과 통합 | 모든 Agent 결과 | 3가지 플랜 |

---

## 3. 기능 요구사항

### 3.1 Travel Consultant (FR-201)

**역할**: 전체 프로세스 관리 및 사용자 대응

**책임:**
- 사용자 메시지 수신
- 현재 상태 파악
- 다음 Agent 호출
- 최종 응답 전달

**구현:**
```python
def travel_consultant_node(state: MultiAgentTravelState):
    if not state["info_collected"]:
        return {"next_agent": "needs_collector"}
    elif not state["flights_searched"]:
        return {"next_agent": "flight_expert"}
    # ...
```

---

### 3.2 Needs Collector (FR-202)

**역할**: 정보 수집 전문화

**Phase 1과 차이점:**
- 더 자연스러운 대화
- 추가 질문 (예산 유연성, 선호 항공사 등)
- 검증 강화

**추가 수집 정보:**
```python
class EnhancedTravelInfo:
    # 기본 정보 (Phase 1과 동일)
    destination: str
    duration: int
    budget: int
    num_people: int
    travel_style: list[str]
    
    # 추가 정보
    budget_flexibility: Literal["strict", "flexible"]  # 예산 유연성
    preferred_airline: str | None                      # 선호 항공사
    accommodation_preference: Literal["hotel", "guesthouse", "airbnb"]
    must_visit_places: list[str]                       # 꼭 가고 싶은 곳
```

---

### 3.3 Router (FR-203)

**역할**: Conditional routing 결정

**라우팅 로직:**
```python
def router_node(state: MultiAgentTravelState):
    # 병렬 실행 가능한 Agent들
    parallel_agents = []
    
    if not state.get("flights_searched"):
        parallel_agents.append("flight_expert")
    
    if not state.get("hotels_searched"):
        parallel_agents.append("hotel_expert")
    
    # 병렬 실행
    if parallel_agents:
        return {"next_agents": parallel_agents}
    
    # 순차 실행
    if not state.get("itinerary_planned"):
        return {"next_agent": "itinerary_planner"}
    
    if not state.get("budget_analyzed"):
        return {"next_agent": "budget_manager"}
    
    # 완료
    return {"next_agent": "coordinator"}
```

---

### 3.4 Flight Expert (FR-204)

**역할**: 항공권 전문 분석 및 추천

**Phase 1과 차이점:**
- 단순 검색 → 분석 + 추천
- 사용자 선호도 반영
- 여러 옵션 비교 설명

**Output 예시:**
```python
{
    "flight_options": [...],  # 기존과 동일
    "recommendation": {
        "best_value": "standard",  # 가성비 최고
        "reasoning": "35만원으로 오전 출발, 직항입니다.",
        "alternatives": [
            {
                "option": "budget",
                "trade_off": "15만원 저렴하지만 새벽 출발"
            }
        ]
    },
    "tips": [
        "출발 2주 전 예약 시 10% 추가 할인 가능",
        "직항이 경유보다 피로도 낮음"
    ]
}
```

---

### 3.5 Hotel Expert (FR-205)

**역할**: 숙박 전문 분석 및 추천

**추가 기능:**
- 위치별 분석 (관광지 접근성)
- 숙소 타입별 장단점
- 예약 팁

**Output 예시:**
```python
{
    "hotel_options": [...],
    "location_analysis": {
        "난바": "관광/쇼핑 최적, 교통 편리",
        "우메다": "비즈니스 지역, 조용함",
        "신사이바시": "쇼핑 천국, 젊은 분위기"
    },
    "recommendation": {
        "best_for_sightseeing": "난바 지역 호텔",
        "reasoning": "오사카성, 도톤보리 도보 가능"
    }
}
```

---

### 3.6 Itinerary Planner (FR-206)

**역할**: 일정 기획 전문가

**추가 기능:**
- 동선 최적화 (가까운 곳끼리 묶기)
- 시간대별 혼잡도 고려
- 대안 일정 제시

**Output 예시:**
```python
{
    "itinerary": {...},  # 기존과 동일
    "optimization": {
        "route_efficiency": "95%",  # 동선 효율성
        "estimated_walking": "5km/일",
        "tips": [
            "Day 2는 하루 종일 유니버셜이므로 체력 안배 필요",
            "Day 3 교토 방문 시 JR패스 추천"
        ]
    },
    "alternative_plan": {
        "description": "비 오는 날 대비",
        "changes": [...]
    }
}
```

---

### 3.7 Budget Manager (FR-207)

**역할**: 예산 분석 및 관리

**기능:**
- 항목별 예산 분배
- 절약 팁
- 추가 비용 예측

**Output 예시:**
```python
{
    "budget_breakdown": {
        "flights": {
            "amount": 700000,
            "percentage": 35,
            "selected": "standard"
        },
        "accommodation": {
            "amount": 240000,
            "percentage": 12,
            "selected": "standard"
        },
        "food": {
            "amount": 600000,
            "percentage": 30,
            "estimate": "20000원/끼 × 3끼 × 4일 × 2인"
        },
        "transport": {
            "amount": 200000,
            "percentage": 10,
            "estimate": "교통카드 + JR패스"
        },
        "attractions": {
            "amount": 200000,
            "percentage": 10,
            "estimate": "유니버셜 티켓 + 입장료"
        },
        "shopping": {
            "amount": 60000,
            "percentage": 3,
            "estimate": "여유 자금"
        }
    },
    "total": 2000000,
    "user_budget": 2000000,
    "remaining": 0,
    "savings_tips": [
        "점심은 편의점 도시락(1000엔)으로 30% 절약",
        "오사카 주유패스 구매 시 교통비 50% 절감"
    ]
}
```

---

### 3.8 Final Coordinator (FR-208)

**역할**: 모든 결과 통합 및 3가지 플랜 생성

**3가지 플랜:**

#### 플랜 A: 럭셔리 🌟
- 항공: Premium
- 숙박: Premium
- 일정: 여유롭게
- 예산: +50%

#### 플랜 B: 균형 (추천) ⭐
- 항공: Standard
- 숙박: Standard
- 일정: 알차게
- 예산: 딱 맞춤

#### 플랜 C: 가성비 💰
- 항공: Budget
- 숙박: Budget
- 일정: 꽉 차게
- 예산: -30%

**Output 형식:**
```markdown
# 🎉 오사카 3박4일 완벽 가이드

당신의 예산: 200만원 (2인)
여행 스타일: 관광 + 맛집

---

## 📊 3가지 추천 플랜

### 🌟 플랜 A: 프리미엄 여행 (250만원)
완벽한 휴식과 럭셔리를 원한다면

**항공**: 대한항공 직항 (50만원)
**숙박**: 힐튼 오사카 (15만원/박)
**특징**: 
- 여유로운 일정
- 미슐랭 맛집 포함
- 프라이빗 투어

[상세 보기]

---

### ⭐ 플랜 B: 밸런스 여행 (200만원) 👈 추천!
가성비와 품질의 완벽한 균형

**항공**: 제주항공 (35만원)
**숙박**: 호텔 난바 (8만원/박)
**특징**:
- 알찬 일정
- 유명 맛집 위주
- 대중교통 이용

[상세 보기]

---

### 💰 플랜 C: 가성비 여행 (140만원)
저예산으로 똑똑하게

**항공**: 티웨이항공 새벽편 (25만원)
**숙박**: 게스트하우스 (4만원/박)
**특징**:
- 빽빽한 일정
- 로컬 맛집
- 도보 + 대중교통

[상세 보기]

---

## 💡 전문가 추천

예산 200만원이시면 **플랜 B**를 강력 추천합니다!

이유:
1. 항공편이 오전 출발로 첫날 활용도 높음
2. 난바 호텔은 관광지 접근성 최고
3. 예산 딱 맞춤으로 여유자금 발생

플랜 C는 60만원 절약되지만:
- 새벽 비행으로 피로도 ↑
- 게스트하우스는 프라이버시 ↓

플랜 A는 50만원 추가지만:
- 체감 만족도는 30% 정도만 ↑
- 가성비 측면에서 비추천
```

---

## 4. LangGraph Multi-Agent Workflow

### 4.1 State 확장
```python
class MultiAgentTravelState(TypedDict):
    # Phase 1 State 모두 포함
    # ... (기존 필드들)
    
    # Agent 통신용
    current_agent: str
    next_agent: str | list[str]  # 단일 또는 병렬
    agent_results: dict[str, Any]
    
    # 진행 상태
    info_collected: bool
    flights_searched: bool
    hotels_searched: bool
    itinerary_planned: bool
    budget_analyzed: bool
    
    # Agent별 결과
    flight_analysis: dict
    hotel_analysis: dict
    itinerary_with_optimization: dict
    budget_breakdown: dict
    final_plans: list[dict]  # 3가지 플랜
```

### 4.2 Graph 구성
```python
from langgraph.graph import StateGraph, END

graph = StateGraph(MultiAgentTravelState)

# Agents
graph.add_node("consultant", travel_consultant_node)
graph.add_node("needs_collector", needs_collector_node)
graph.add_node("router", router_node)
graph.add_node("flight_expert", flight_expert_node)
graph.add_node("hotel_expert", hotel_expert_node)
graph.add_node("itinerary_planner", itinerary_planner_node)
graph.add_node("budget_manager", budget_manager_node)
graph.add_node("coordinator", final_coordinator_node)

# Edges
graph.set_entry_point("consultant")

graph.add_conditional_edges(
    "consultant",
    lambda x: x["next_agent"],
    {
        "needs_collector": "needs_collector",
        "router": "router",
        "coordinator": "coordinator"
    }
)

graph.add_edge("needs_collector", "router")

graph.add_conditional_edges(
    "router",
    lambda x: x["next_agent"],
    {
        "flight_expert": "flight_expert",
        "hotel_expert": "hotel_expert",
        "itinerary_planner": "itinerary_planner",
        "budget_manager": "budget_manager",
        "coordinator": "coordinator"
    }
)

# 각 전문가 → router로 돌아가기
graph.add_edge("flight_expert", "router")
graph.add_edge("hotel_expert", "router")
graph.add_edge("itinerary_planner", "router")
graph.add_edge("budget_manager", "router")

graph.add_edge("coordinator", END)

app = graph.compile()
```

---

## 5. 완료 기준

### Must Have ✅
- [ ] 7개 Agent 구현 및 동작
- [ ] Conditional routing 작동
- [ ] 3가지 플랜 생성
- [ ] Phase 1 대비 품질 향상
- [ ] 3개 여행지 테스트 (오사카/방콕/제주)

### Should Have ⭐
- [ ] Agent별 전문성 명확히 드러남
- [ ] 병렬 실행 (항공+숙박 동시)
- [ ] Single vs Multi 성능 비교 문서
- [ ] 개선된 UI (Agent 진행 상태 표시)

### Could Have 💡
- [ ] Agent 간 의견 충돌 시뮬레이션
- [ ] 사용자 선택에 따른 재계획
- [ ] Agent별 신뢰도 점수

---

## 6. 테스트 케이스

### TC-201: Multi-Agent 협업
```yaml
Input: "오사카 3박4일 200만원 2명"

Expected:
  - Needs Collector: 정보 수집
  - Flight + Hotel Expert: 병렬 검색
  - Itinerary Planner: 일정 생성
  - Budget Manager: 예산 분석
  - Coordinator: 3가지 플랜

Verify:
  - 각 Agent 실행 순서 로그
  - Agent 간 State 전달 확인
```

### TC-202: 예산 초과 시나리오
```yaml
Input: 예산 150만원 (부족)

Expected:
  - Budget Manager가 경고
  - Coordinator가 플랜 C만 제시
  - 또는 예산 증액 제안
```

---

## 7. Single vs Multi 비교 분석

### 비교 항목
| 항목 | Single Agent | Multi Agent | 개선율 |
|------|-------------|-------------|--------|
| 응답 품질 | 3.5/5 | 4.5/5 | +28% |
| 전문성 | 보통 | 높음 | - |
| 응답 시간 | 45초 | 60초 | -33% |
| 코드 복잡도 | 낮음 | 높음 | - |
| 유지보수성 | 보통 | 높음 | - |
| 확장성 | 낮음 | 높음 | - |

### 품질 평가 기준
- 항공권 추천 적절성
- 일정 최적화 정도
- 예산 분배 합리성
- 전반적 만족도

---

**문서 버전**: 1.0  
**작성일**: 2024-11-30  
**의존성**: Phase 1 완료 필수