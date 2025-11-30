# 개발 환경 설정 가이드

## 1. 필수 요구사항

### 시스템 요구사항
- **OS**: macOS, Linux, Windows (WSL2 권장)
- **RAM**: 8GB 이상 (16GB 권장)
- **Disk**: 10GB 이상 여유 공간

### 소프트웨어 버전
- **Python**: 3.11 이상
- **Node.js**: 18 이상
- **Git**: 2.30 이상

---

## 2. 프로젝트 클론
```bash
# GitHub에서 클론
git clone https://github.com/your-username/tripmate-ai.git
cd tripmate-ai
```

---

## 3. Backend 환경 설정

### 3.1 Python 가상환경 생성
```bash
cd backend

# venv 생성
python -m venv venv

# 활성화
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3.2 의존성 설치
```bash
# 기본 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt:**
```txt
# LLM & LangChain
langchain==0.1.0
langgraph==0.0.20
langchain-openai==0.0.5
openai==1.0.0

# Web Framework
fastapi==0.104.0
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Data & Validation
pydantic==2.5.0
pydantic-settings==2.1.0

# Utils
python-dotenv==1.0.0
httpx==0.25.0

# Web Scraping (필요시)
playwright==1.40.0

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
```

### 3.3 Playwright 설치 (크롤링 필요시)
```bash
# Playwright 브라우저 다운로드
playwright install chromium
```

### 3.4 환경변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**.env 내용:**
```bash
# OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Optional: 외부 API
SKYSCANNER_API_KEY=your-key-here
BOOKING_API_KEY=your-key-here
GOOGLE_PLACES_API_KEY=your-key-here

# Environment
ENVIRONMENT=development  # development, production

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# CORS (Frontend URL)
FRONTEND_URL=http://localhost:3000
```

**.env.example (Git에 커밋용):**
```bash
# OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Optional APIs
SKYSCANNER_API_KEY=
BOOKING_API_KEY=
GOOGLE_PLACES_API_KEY=

# Environment
ENVIRONMENT=development

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# CORS
FRONTEND_URL=http://localhost:3000
```

### 3.5 OpenAI API Key 발급

1. https://platform.openai.com/ 접속
2. 로그인 후 "API Keys" 메뉴
3. "Create new secret key" 클릭
4. 생성된 키를 `.env`의 `OPENAI_API_KEY`에 입력

**중요:** API 키는 절대 Git에 커밋하지 말 것!

### 3.6 Backend 실행 확인
```bash
# FastAPI 서버 실행
python app.py

# 또는
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**브라우저에서 확인:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

**정상 응답:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 4. Frontend 환경 설정

### 4.1 Node.js 의존성 설치
```bash
cd ../frontend

# npm 사용
npm install

# 또는 yarn 사용
yarn install
```

**package.json 주요 의존성:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.3.0",
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0",
    "vite": "^5.0.0"
  }
}
```

### 4.2 환경변수 설정
```bash
# .env.local 파일 생성
cp .env.example .env.local

# 편집
nano .env.local
```

**.env.local:**
```bash
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/ws
```

### 4.3 Frontend 실행 확인
```bash
# 개발 서버 실행
npm run dev

# 또는
yarn dev
```

**브라우저에서 확인:**
- http://localhost:3000

---

## 5. 전체 실행 (Backend + Frontend)

### 5.1 터미널 2개 사용

**터미널 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python app.py
```

**터미널 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5.2 또는 tmux 사용 (권장)
```bash
# tmux 설치 (macOS)
brew install tmux

# 세션 시작
tmux new -s tripmate

# 화면 분할 (수평)
Ctrl+b, "

# 위쪽 창: Backend
cd backend && source venv/bin/activate && python app.py

# 아래쪽 창으로 이동
Ctrl+b, ↓

# 아래쪽 창: Frontend
cd frontend && npm run dev

# tmux 종료
Ctrl+b, d
```

---

## 6. Phase 1 전용: Streamlit 실행

Phase 1에서는 Streamlit으로 빠른 프로토타입 가능:
```bash
cd backend
source venv/bin/activate

# Streamlit 설치
pip install streamlit

# 실행
streamlit run streamlit_app.py
```

**브라우저에서 자동 열림:**
- http://localhost:8501

---

## 7. 테스트 실행

### 7.1 Backend 테스트
```bash
cd backend
source venv/bin/activate

# 전체 테스트
pytest

# 특정 파일
pytest tests/test_agents.py

# Coverage 포함
pytest --cov=src tests/
```

### 7.2 Frontend 테스트
```bash
cd frontend

# Jest 테스트
npm run test

# E2E 테스트 (Playwright)
npm run test:e2e
```

---

## 8. 개발 도구 설정

### 8.1 VSCode 추천 확장

**.vscode/extensions.json:**
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "ms-playwright.playwright"
  ]
}
```

### 8.2 VSCode 설정

**.vscode/settings.json:**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### 8.3 Black (Python 포맷터)
```bash
cd backend

# 설치
pip install black

# 사용
black src/

# 설정 파일 (pyproject.toml)
```

**pyproject.toml:**
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
```

### 8.4 Prettier (TS/React 포맷터)
```bash
cd frontend

# 설치
npm install --save-dev prettier

# 설정 파일
```

**.prettierrc:**
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

---

## 9. 일반적인 문제 해결

### 9.1 "ModuleNotFoundError: No module named 'langchain'"

**원인:** 가상환경 활성화 안 됨

**해결:**
```bash
cd backend
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows
```

### 9.2 "OPENAI_API_KEY not found"

**원인:** 환경변수 미설정

**해결:**
```bash
# .env 파일 확인
cat backend/.env

# OPENAI_API_KEY가 있는지 확인
# 없으면 추가
echo "OPENAI_API_KEY=sk-your-key" >> backend/.env
```

### 9.3 "Port 8000 already in use"

**원인:** 포트 충돌

**해결:**
```bash
# 프로세스 찾기 (macOS/Linux)
lsof -i :8000

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
uvicorn app:app --port 8001
```

### 9.4 "playwright: command not found"

**원인:** Playwright 브라우저 미설치

**해결:**
```bash
cd backend
source venv/bin/activate
playwright install chromium
```

### 9.5 CORS 오류 (Frontend → Backend)

**원인:** CORS 설정 문제

**해결:**

**backend/app.py:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 9.6 "Module not found: Can't resolve 'axios'"

**원인:** npm install 안 됨

**해결:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 10. 디렉토리 구조 확인

프로젝트가 제대로 설정되었는지 확인:
```bash
tripmate-ai/
├── backend/
│   ├── venv/              ✅ 가상환경
│   ├── .env               ✅ 환경변수
│   ├── requirements.txt   ✅ 의존성
│   ├── app.py            ✅ FastAPI 앱
│   └── src/              ✅ 소스코드
│
├── frontend/
│   ├── node_modules/     ✅ 의존성
│   ├── .env.local        ✅ 환경변수
│   ├── package.json      ✅ 설정
│   └── src/              ✅ 소스코드
│
└── docs/                 ✅ 문서
```

**확인 명령:**
```bash
# Backend
cd backend && ls -la

# 있어야 할 것:
# venv/, .env, requirements.txt, app.py, src/

# Frontend
cd frontend && ls -la

# 있어야 할 것:
# node_modules/, .env.local, package.json, src/
```

---

## 11. 다음 단계

환경 설정이 완료되었다면:

1. ✅ Backend 실행: http://localhost:8000/docs
2. ✅ Frontend 실행: http://localhost:3000
3. ✅ 테스트 실행: `pytest`

**이제 개발 시작!**

👉 다음: [대화 플로우 예시](../examples/conversation-flow.md)

---

## 12. 참고 자료

- **LangChain 문서**: https://python.langchain.com/docs/
- **LangGraph 문서**: https://langchain-ai.github.io/langgraph/
- **FastAPI 문서**: https://fastapi.tiangolo.com/
- **React 문서**: https://react.dev/

---

**문서 버전**: 1.0  
**작성일**: 2024-11-30  
**최종 업데이트**: 환경 설정 완료 후