# API 명세서

## 개요
- **Base URL**: `http://localhost:8000/api`
- **프로토콜**: REST API
- **인증**: 없음 (MVP)
- **응답 형식**: JSON

---

## 1. 채팅 API

### POST /api/chat

사용자 메시지를 받아 AI Agent 응답 반환

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "message": "오사카 여행 가고 싶어요",
  "session_id": "uuid-string"  // optional, 없으면 자동 생성
}
```

**Parameters:**
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| message | string | O | 사용자 메시지 |
| session_id | string | X | 세션 ID (대화 연속성) |

#### Response

**Success (200):**
```json
{
  "reply": "오사카 좋네요! 몇 박 며칠 계획이신가요?",
  "session_id": "uuid-string",
  "state": {
    "destination": "오사카",
    "duration": null,
    "budget": null,
    "num_people": null,
    "travel_style": [],
    "info_collected": false,
    "current_step": "collecting"
  },
  "next_question": "duration",
  "progress": {
    "current": 1,
    "total": 5,
    "percentage": 20
  }
}
```

**Error (400):**
```json
{
  "error": "Invalid message format",
  "details": "Message cannot be empty"
}
```

**Error (500):**
```json
{
  "error": "Internal server error",
  "details": "LLM API timeout"
}
```

---

## 2. 여행 계획 조회 API

### GET /api/plan/{session_id}

완성된 여행 계획 조회

#### Request

**Path Parameters:**
| 필드 | 타입 | 설명 |
|------|------|------|
| session_id | string | 세션 ID |

#### Response

**Success (200):**
```json
{
  "session_id": "uuid-string",
  "status": "completed",
  "user_info": {
    "destination": "오사카",
    "duration": 3,
    "budget": 1000000,
    "num_people": 2,
    "travel_style": ["관광", "맛집"]
  },
  "plan": {
    "flights": [
      {
        "type": "budget",
        "price": 250000,
        "airline": "티웨이항공",
        "outbound": {
          "departure_time": "06:00",
          "arrival_time": "08:30",
          "flight_time": "2h 30m"
        },
        "inbound": {
          "departure_time": "09:00",
          "arrival_time": "11:30",
          "flight_time": "2h 30m"
        }
      }
      // ... 3개
    ],
    "hotels": [
      {
        "type": "budget",
        "name": "게스트하우스 난바",
        "price_per_night": 40000,
        "total_price": 120000,
        "location": "난바",
        "rating": 4.2
      }
      // ... 3개
    ],
    "itinerary": {
      "day1": {
        "date": "2024-12-20",
        "theme": "도착 & 시내 탐방",
        "activities": [
          {
            "time": "09:00",
            "activity": "인천공항 출발",
            "type": "transport"
          }
          // ...
        ]
      }
      // ... N일
    },
    "budget_breakdown": {
      "flights": 500000,
      "accommodation": 240000,
      "food": 400000,
      "transport": 100000,
      "attractions": 200000,
      "total": 1440000
    }
  },
  "created_at": "2024-12-01T10:00:00Z",
  "updated_at": "2024-12-01T10:05:00Z"
}
```

**Error (404):**
```json
{
  "error": "Plan not found",
  "details": "Session ID does not exist"
}
```

---

## 3. Phase 2 전용 API

### GET /api/plan/{session_id}/multi

Multi Agent 결과 조회 (3가지 플랜)

#### Response

**Success (200):**
```json
{
  "session_id": "uuid-string",
  "plans": [
    {
      "plan_id": "luxury",
      "name": "프리미엄 여행",
      "total_budget": 2500000,
      "description": "완벽한 휴식과 럭셔리",
      "flights": {...},
      "hotels": {...},
      "itinerary": {...},
      "highlights": [
        "대한항공 직항",
        "5성급 호텔",
        "미슐랭 맛집"
      ]
    },
    {
      "plan_id": "balanced",
      "name": "밸런스 여행",
      "total_budget": 2000000,
      "recommended": true,  // 추천 플랜
      "description": "가성비와 품질의 균형",
      // ...
    },
    {
      "plan_id": "budget",
      "name": "가성비 여행",
      "total_budget": 1400000,
      // ...
    }
  ],
  "recommendation": {
    "plan_id": "balanced",
    "reasoning": "예산에 딱 맞고 품질도 우수합니다",
    "comparison": {
      "vs_luxury": "50만원 절약, 만족도 차이 적음",
      "vs_budget": "60만원 추가, 편의성 크게 향상"
    }
  },
  "agent_insights": {
    "flight_expert": "오전 출발편 추천",
    "hotel_expert": "난바 지역 최적",
    "itinerary_planner": "동선 효율 95%",
    "budget_manager": "예산 여유 36만원"
  }
}
```

---

## 4. 세션 관리 API

### GET /api/sessions

사용자의 세션 목록 조회

#### Response
```json
{
  "sessions": [
    {
      "session_id": "uuid-1",
      "destination": "오사카",
      "status": "completed",
      "created_at": "2024-12-01T10:00:00Z"
    },
    {
      "session_id": "uuid-2",
      "destination": "방콕",
      "status": "in_progress",
      "created_at": "2024-12-02T14:00:00Z"
    }
  ]
}
```

### DELETE /api/session/{session_id}

세션 삭제

#### Response
```json
{
  "message": "Session deleted successfully",
  "session_id": "uuid-string"
}
```

---

## 5. 헬스체크 API

### GET /api/health

서버 상태 확인

#### Response
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-12-01T10:00:00Z",
  "dependencies": {
    "openai_api": "connected",
    "database": "connected"
  }
}
```

---

## 6. 데이터 모델

### TravelState
```typescript
interface TravelState {
  // 사용자 정보
  destination: string;
  duration: number;          // 박
  budget: number;            // 원
  num_people: number;
  travel_style: string[];
  
  // 진행 상태
  info_collected: boolean;
  current_step: "collecting" | "searching" | "planning" | "done";
  
  // 검색 결과
  flight_options: FlightOption[];
  hotel_options: HotelOption[];
  itinerary: Itinerary;
  
  // 메타
  session_id: string;
  created_at: string;
  updated_at: string;
}
```

### FlightOption
```typescript
interface FlightOption {
  type: "budget" | "standard" | "premium";
  price: number;
  airline: string;
  outbound: {
    departure_time: string;  // "HH:MM"
    arrival_time: string;
    flight_time: string;     // "Xh Ym"
  };
  inbound: {
    departure_time: string;
    arrival_time: string;
    flight_time: string;
  };
}
```

### HotelOption
```typescript
interface HotelOption {
  type: "budget" | "standard" | "premium";
  name: string;
  price_per_night: number;
  total_price: number;
  location: string;
  rating: number;
  amenities: string[];
  distance_from_center: string;
}
```

### Itinerary
```typescript
interface Itinerary {
  [key: string]: {  // "day1", "day2", ...
    date: string;   // "YYYY-MM-DD"
    theme: string;
    activities: Activity[];
  };
}

interface Activity {
  time: string;       // "HH:MM"
  activity: string;
  location?: string;
  duration?: string;
  type: "transport" | "sightseeing" | "food" | "shopping" | "rest";
  description?: string;
}
```

---

## 7. 오류 코드

| 코드 | 설명 | 해결 방법 |
|------|------|----------|
| 400 | 잘못된 요청 | 요청 형식 확인 |
| 404 | 리소스 없음 | session_id 확인 |
| 429 | 요청 제한 초과 | 잠시 후 재시도 |
| 500 | 서버 오류 | 관리자 문의 |
| 503 | 서비스 불가 | LLM API 장애 |

---

## 8. Rate Limiting

- **제한**: 100 requests / hour / IP
- **초과 시**: 429 응답
- **헤더**:
```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 50
  X-RateLimit-Reset: 1638360000
```

---

## 9. WebSocket API (선택, Phase 3)

### WS /api/ws/chat

실시간 채팅 (스트리밍)

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/chat?session_id=uuid');
```

#### Send Message
```json
{
  "type": "user_message",
  "message": "오사카"
}
```

#### Receive Message (streaming)
```json
{
  "type": "agent_response",
  "chunk": "오사카 좋",
  "done": false
}
```
```json
{
  "type": "agent_response",
  "chunk": "네요!",
  "done": true,
  "state": {...}
}
```

---

**문서 버전**: 1.0  
**작성일**: 2024-11-30  
**Base URL**: http://localhost:8000/api