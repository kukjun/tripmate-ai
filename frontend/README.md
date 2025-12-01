# TripMate AI - Frontend

React + TypeScript 기반 AI 여행 플래너 프론트엔드

## 기술 스택

- **React**: 18.x
- **TypeScript**: 5.x
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **State Management**: TanStack Query (React Query)
- **HTTP Client**: Axios

## 설치 및 실행

### 1. 의존성 설치

```bash
npm install
# 또는
yarn install
```

### 2. 환경변수 설정

```bash
cp .env.example .env.local
# .env.local 파일 편집
```

### 3. 개발 서버 실행

```bash
npm run dev
# 또는
yarn dev
```

브라우저에서 http://localhost:3000 접속

### 4. 빌드

```bash
npm run build
# 또는
yarn build
```

## 디렉토리 구조

```
frontend/
├── public/
│   └── index.html
│
├── src/
│   ├── App.tsx              # 메인 앱 컴포넌트
│   ├── index.tsx            # 엔트리 포인트
│   ├── index.css            # 글로벌 스타일
│   │
│   ├── components/          # UI 컴포넌트
│   │   ├── ChatInterface.tsx
│   │   ├── PlanDisplay.tsx
│   │   └── LoadingSpinner.tsx
│   │
│   ├── hooks/               # Custom Hooks
│   │   ├── useChat.ts
│   │   └── usePlan.ts
│   │
│   ├── api/                 # API 클라이언트
│   │   └── client.ts
│   │
│   ├── types/               # TypeScript 타입
│   │   └── index.ts
│   │
│   └── utils/               # 유틸리티 함수
│       └── formatters.ts
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## 스크립트

| 명령어 | 설명 |
|--------|------|
| `npm run dev` | 개발 서버 실행 |
| `npm run build` | 프로덕션 빌드 |
| `npm run preview` | 빌드 결과 미리보기 |
| `npm run lint` | ESLint 검사 |
| `npm run format` | Prettier 포맷팅 |

## 환경변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000/api` |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000/api/ws` |

## 라이선스

MIT License
