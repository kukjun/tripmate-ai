# TripMate AI - Backend

LangGraph 기반 AI 여행 플래너 백엔드

## 기술 스택

- **Python**: 3.11+
- **Package Manager**: uv
- **Web Framework**: FastAPI
- **AI Orchestration**: LangGraph, LangChain
- **LLM**: OpenAI GPT-4
- **Validation**: Pydantic v2
- **UI**: Streamlit (Phase 1)
- **Crawling**: Playwright (선택)

## 설치 및 실행

### 1. uv 설치 (처음 한 번만)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 의존성 설치

```bash
cd backend
uv sync
```

### 3. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어서 OPENAI_API_KEY 설정
```

### 4. 서버 실행

```bash
# FastAPI 서버
uv run python app.py

# 또는
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 5. Streamlit UI (Phase 1 전용)

```bash
uv run streamlit run streamlit_app.py
```

## 디렉토리 구조

```
backend/
├── app.py                 # FastAPI 메인 앱
├── streamlit_app.py       # Streamlit UI (Phase 1)
├── pyproject.toml         # Python 프로젝트 설정 (uv)
├── uv.lock                # 의존성 잠금 파일
├── .env.example           # 환경변수 예시
│
├── src/
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   │
│   ├── models/            # 데이터 모델
│   │   ├── __init__.py
│   │   └── state.py       # TravelState 정의
│   │
│   ├── agents/            # AI Agents
│   │   ├── __init__.py
│   │   └── phase1/        # Phase 1 Single Agent
│   │       ├── info_collector.py
│   │       ├── flight_searcher.py
│   │       ├── hotel_searcher.py
│   │       └── itinerary_planner.py
│   │
│   ├── tools/             # External API 연동
│   │   └── __init__.py
│   │
│   ├── graph/             # LangGraph Workflows
│   │   ├── __init__.py
│   │   └── phase1_graph.py
│   │
│   ├── utils/             # 유틸리티
│   │   ├── __init__.py
│   │   └── prompts.py
│   │
│   └── api/               # FastAPI 라우터
│       ├── __init__.py
│       ├── chat.py
│       ├── plan.py
│       └── sessions.py
│
└── tests/                 # 테스트
    ├── __init__.py
    ├── conftest.py
    ├── test_agents.py
    └── test_api.py
```

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/health` | 헬스 체크 |
| POST | `/api/chat` | 채팅 메시지 전송 |
| GET | `/api/chat/{session_id}/history` | 대화 히스토리 조회 |
| GET | `/api/plan/{session_id}` | 여행 계획 조회 |
| GET | `/api/plan/{session_id}/flights` | 항공권 옵션 조회 |
| GET | `/api/plan/{session_id}/hotels` | 숙박 옵션 조회 |
| GET | `/api/plan/{session_id}/itinerary` | 일정 조회 |
| GET | `/api/plan/{session_id}/summary` | 마크다운 요약 조회 |
| GET | `/api/sessions` | 세션 목록 조회 |
| DELETE | `/api/sessions/{session_id}` | 세션 삭제 |

## 개발 가이드

### 코드 포맷팅

```bash
# Ruff (린터 + 포맷터)
uv run ruff check src/
uv run ruff format src/

# Black 포맷터 실행
uv run black src/

# Import 정렬
uv run isort src/
```

### 테스트 실행

```bash
# 전체 테스트
uv run pytest

# 특정 파일
uv run pytest tests/test_agents.py

# Coverage
uv run pytest --cov=src tests/
```

### 개발 의존성 추가

```bash
# 일반 의존성 추가
uv add <package-name>

# 개발 의존성 추가
uv add --dev <package-name>

# 선택적 의존성 추가
uv add --optional scraping playwright
```

## 라이선스

MIT License
