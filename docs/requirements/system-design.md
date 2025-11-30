# 시스템 아키텍처

## 1. 전체 구조
```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Chat UI   │  │  Result View │  │  Plan Compare│       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   API Layer                          │   │
│  │  /api/chat  /api/plan  /api/sessions                │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │              LangGraph Orchestration                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ Phase 1  │  │ Phase 2  │  │ Phase 3  │          │   │
│  │  │  Single  │  │  Multi   │  │  Local   │          │   │
│  │  │  Agent   │  │  Agent   │  │  LLM     │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │                External Services                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ OpenAI   │  │ Flight   │  │  Hotel   │          │   │
│  │  │   API    │  │   API    │  │   API    │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Data Storage                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Sessions   │  │    Cache     │                        │
│  │   (JSON)     │  │   (Redis)    │   (Phase 3)           │
│  └──────────────┘  └──────────────┘                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 모노레포 구조
```
tripmate-ai/
├── README.md
├── .gitignore
├── .env.example
│
├── backend/                    # Python Backend
│   ├── README.md
│   ├── requirements.txt
│   ├── .env
│   ├── pyproject.toml         # (선택) Poetry
│   │
│   ├── app.py                 # FastAPI 메인
│   ├── streamlit_app.py       # Streamlit UI (Phase 1)
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   ├── config.py          # 설정 관리
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── state.py       # TravelState 정의
│   │   │
│   │   ├── agents/            # Phase별 Agent
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── phase1/        # Single Agent
│   │   │   │   ├── __init__.py
│   │   │   │   ├── info_collector.py
│   │   │   │   ├── flight_searcher.py
│   │   │   │   ├── hotel_searcher.py
│   │   │   │   └── itinerary_planner.py
│   │   │   │
│   │   │   └── phase2/        # Multi Agent
│   │   │       ├── __init__.py
│   │   │       ├── consultant.py
│   │   │       ├── needs_collector.py
│   │   │       ├── router.py
│   │   │       ├── flight_expert.py
│   │   │       ├── hotel_expert.py
│   │   │       ├── itinerary_planner.py
│   │   │       ├── budget_manager.py
│   │   │       └── coordinator.py
│   │   │
│   │   ├── tools/             # External API/크롤링
│   │   │   ├── __init__.py
│   │   │   ├── flight_api.py
│   │   │   ├── hotel_api.py
│   │   │   └── places_api.py
│   │   │
│   │   ├── graph/             # LangGraph Workflow
│   │   │   ├── __init__.py
│   │   │   ├── phase1_graph.py
│   │   │   └── phase2_graph.py
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── prompts.py     # 프롬프트 템플릿
│   │   │   ├── validators.py  # 입력 검증
│   │   │   └── helpers.py
│   │   │
│   │   └── api/               # FastAPI 라우터
│   │       ├── __init__.py
│   │       ├── chat.py
│   │       ├── plan.py
│   │       └── sessions.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_agents.py
│       ├── test_tools.py
│       └── test_api.py
│
├── frontend/                   # React Frontend
│   ├── README.md
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   │
│   ├── public/
│   │   └── index.html
│   │
│   └── src/
│       ├── App.tsx
│       ├── index.tsx
│       │
│       ├── components/
│       │   ├── ChatInterface.tsx
│       │   ├── PlanDisplay.tsx
│       │   ├── PlanComparison.tsx  # Phase 2
│       │   └── LoadingSpinner.tsx
│       │
│       ├── hooks/
│       │   ├── useChat.ts
│       │   └── usePlan.ts
│       │
│       ├── api/
│       │   └── client.ts      # Axios 설정
│       │
│       ├── types/
│       │   └── index.ts       # TypeScript 타입
│       │
│       └── utils/
│           └── formatters.ts
│
├── shared/                     # 공통 타입 정의
│   └── types.ts
│
└── docs/                       # 문서
    ├── requirements/
    │   ├── phase1-requirements.md
    │   ├── phase2-requirements.md
    │   └── api-spec.md
    │
    ├── architecture/
    │   ├── system-design.md       # 이 문서
    │   ├── state-management.md
    │   └── agent-design.md
    │
    ├── examples/
    │   ├── conversation-flow.md
    │   ├── api-examples.md
    │   └── test-cases.md
    │
    └── setup/
        ├── environment.md
        └── deployment.md
```

---

## 3. 데이터 플로우

### Phase 1: Single Agent
```
User Message
    ↓
FastAPI /api/chat
    ↓
Single Agent Graph
    ↓
┌─────────────────────┐
│ 1. Info Collector   │ → State.info_collected = True
└─────────────────────┘
    ↓
┌─────────────────────┐
│ 2. Flight Searcher  │ → State.flight_options = [...]
└─────────────────────┘
    ↓
┌─────────────────────┐
│ 3. Hotel Searcher   │ → State.hotel_options = [...]
└─────────────────────┘
    ↓
┌─────────────────────┐
│ 4. Itinerary Plan   │ → State.itinerary = {...}
└─────────────────────┘
    ↓
┌─────────────────────┐
│ 5. Response Gen     │ → Final Response
└─────────────────────┘
    ↓
JSON Response
    ↓
Frontend
```

### Phase 2: Multi Agent
```
User Message
    ↓
FastAPI /api/chat
    ↓
Multi Agent Graph
    ↓
┌─────────────────────┐
│  Consultant         │ → Decides next step
└─────────────────────┘
    ↓
┌─────────────────────┐
│ Needs Collector     │ → Collects info
└─────────────────────┘
    ↓
┌─────────────────────┐
│     Router          │ → Routes to experts
└─────────────────────┘
    ↓
┌──────────────────────────────────┐
│ Parallel Execution               │
│  ┌──────────┐  ┌──────────┐     │
│  │ Flight   │  │  Hotel   │     │
│  │ Expert   │  │  Expert  │     │
│  └──────────┘  └──────────┘     │
└──────────────────────────────────┘
    ↓
┌─────────────────────┐
│ Itinerary Planner   │
└─────────────────────┘
    ↓
┌─────────────────────┐
│  Budget Manager     │
└─────────────────────┘
    ↓
┌─────────────────────┐
│   Coordinator       │ → 3 Plans
└─────────────────────┘
    ↓
JSON Response (3 plans)
    ↓
Frontend (Comparison View)
```

---

## 4. 기술 스택 상세

### Backend

| 레이어 | 기술 | 용도 |
|--------|------|------|
| 웹 프레임워크 | FastAPI | REST API |
| AI 오케스트레이션 | LangGraph | Agent workflow |
| LLM | OpenAI GPT-4 | 대화/생성 |
| 크롤링 | Playwright | 항공/숙박 검색 |
| 검증 | Pydantic | 데이터 모델 |
| 환경변수 | python-dotenv | 설정 관리 |

### Frontend

| 레이어 | 기술 | 용도 |
|--------|------|------|
| UI 프레임워크 | React 18 | 사용자 인터페이스 |
| 언어 | TypeScript | 타입 안정성 |
| 스타일링 | TailwindCSS | 빠른 스타일링 |
| 상태 관리 | React Query | 서버 상태 |
| HTTP | Axios | API 호출 |

### DevOps (Phase 3)

| 용도 | 기술 |
|------|------|
| 컨테이너 | Docker |
| 배포 | Vercel (FE) + Railway (BE) |
| CI/CD | GitHub Actions |
| 모니터링 | Sentry |

---

## 5. 보안 고려사항

### API Key 관리
```python
# backend/.env
OPENAI_API_KEY=sk-...
SKYSCANNER_API_KEY=...

# backend/src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    skyscanner_api_key: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### CORS 설정
```python
# backend/app.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("100/hour")
async def chat(request: Request, ...):
    ...
```

---

## 6. 성능 최적화

### 1. 병렬 API 호출
```python
import asyncio

async def parallel_search(state):
    flights_task = search_flights(state)
    hotels_task = search_hotels(state)
    
    flights, hotels = await asyncio.gather(
        flights_task,
        hotels_task
    )
    
    return {"flights": flights, "hotels": hotels}
```

### 2. 캐싱 (Phase 3)
```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379)

@lru_cache(maxsize=100)
def get_flight_options(origin, dest, date):
    # 같은 검색은 캐시에서
    cached = redis_client.get(f"flights:{origin}:{dest}:{date}")
    if cached:
        return cached
    
    # API 호출
    result = search_api(...)
    redis_client.setex(f"flights:{origin}:{dest}:{date}", 3600, result)
    return result
```

### 3. 응답 스트리밍 (WebSocket)
```python
@app.websocket("/api/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    async for chunk in agent.stream(message):
        await websocket.send_json({
            "chunk": chunk,
            "done": False
        })
    
    await websocket.send_json({"done": True})
```

---

## 7. 확장성 고려

### Horizontal Scaling
```
                  Load Balancer
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    Backend 1      Backend 2      Backend 3
        │              │              │
        └──────────────┴──────────────┘
                       │
                  Redis (Session)
```

### Microservices (미래)
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Chat      │  │   Search    │  │  Planning   │
│  Service    │  │  Service    │  │   Service   │
└─────────────┘  └─────────────┘  └─────────────┘
       │                │                │
       └────────────────┴────────────────┘
                       │
                 Message Queue
                   (RabbitMQ)
```

---

## 8. 모니터링 & 로깅

### 로깅 구조
```python
import logging

# backend/src/utils/logger.py
logger = logging.getLogger("tripmate")
logger.setLevel(logging.INFO)

# 로그 포맷
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 파일 핸들러
file_handler = logging.FileHandler('tripmate.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
```

### 사용 예시
```python
# Agent에서
logger.info(f"Collecting info for session {session_id}")
logger.warning(f"Flight API timeout, retrying... (attempt {retry})")
logger.error(f"Failed to search hotels: {error}")
```

### 메트릭 수집 (Phase 3)
```python
from prometheus_client import Counter, Histogram

chat_requests = Counter('chat_requests_total', 'Total chat requests')
response_time = Histogram('response_time_seconds', 'Response time')

@app.post("/api/chat")
async def chat(...):
    chat_requests.inc()
    with response_time.time():
        # ... 처리
```

---

## 9. 에러 처리 전략

### 계층별 에러 처리
```python
# 1. Tool Level (API/크롤링)
class FlightAPIError(Exception):
    pass

async def search_flights():
    try:
        result = await api_call()
    except Timeout:
        logger.warning("Flight API timeout, retrying...")
        # 재시도
    except APIError as e:
        logger.error(f"Flight API error: {e}")
        raise FlightAPIError("항공권 검색 실패")

# 2. Agent Level
def flight_expert_node(state):
    try:
        flights = search_flights()
    except FlightAPIError:
        # 우아한 실패
        return {
            "flight_options": [],
            "error": "항공권 정보를 가져올 수 없습니다"
        }

# 3. API Level
@app.post("/api/chat")
async def chat(...):
    try:
        result = agent.run(message)
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(
            status_code=500,
            detail="서버 오류가 발생했습니다"
        )
```

---

## 10. 테스트 전략

### 테스트 피라미드
```
        ┌──────┐
        │  E2E │  5% - Playwright
        ├──────┤
        │ Integ│  15% - API 테스트
        ├──────┤
        │ Unit │  80% - pytest
        └──────┘
```

### 테스트 예시
```python
# tests/test_agents.py
def test_info_collector():
    state = TravelState(
        destination="오사카",
        duration=None,
        ...
    )
    
    result = info_collector_node(state)
    
    assert result["next_question"] == "duration"
    assert not result["info_collected"]

# tests/test_api.py
def test_chat_endpoint(client):
    response = client.post("/api/chat", json={
        "message": "오사카"
    })
    
    assert response.status_code == 200
    assert "session_id" in response.json()
```

---

**문서 버전**: 1.0  
**작성일**: 2024-11-30  
**다음 리뷰**: Phase 1 완료 후