# TripMate AI - Backend

LangGraph 기반 AI 여행 플래너 백엔드

## 기술 스택

- **Python**: 3.11+
- **Web Framework**: FastAPI
- **AI Orchestration**: LangGraph, LangChain
- **LLM**: OpenAI GPT-4
- **Validation**: Pydantic v2
- **Crawling**: Playwright (선택)

## 설치 및 실행

### 1. 가상환경 생성

```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어서 OPENAI_API_KEY 설정
```

### 4. 서버 실행

```bash
# FastAPI 서버
python app.py

# 또는
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 5. Streamlit UI (Phase 1 전용)

```bash
pip install streamlit
streamlit run streamlit_app.py
```

## 디렉토리 구조

```
backend/
├── app.py                 # FastAPI 메인 앱
├── streamlit_app.py       # Streamlit UI (Phase 1)
├── requirements.txt       # Python 의존성
├── pyproject.toml         # Python 프로젝트 설정
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
│   │
│   ├── tools/             # External API 연동
│   │   ├── __init__.py
│   │   ├── flight_api.py
│   │   └── hotel_api.py
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
│       └── chat.py
│
└── tests/                 # 테스트
    ├── __init__.py
    └── test_agents.py
```

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/health` | 헬스 체크 |
| POST | `/api/chat` | 채팅 메시지 전송 |
| GET | `/api/sessions/{id}` | 세션 조회 |

## 개발 가이드

### 코드 포맷팅

```bash
# Black 포맷터 실행
black src/

# Import 정렬
isort src/
```

### 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 파일
pytest tests/test_agents.py

# Coverage
pytest --cov=src tests/
```

## 라이선스

MIT License
