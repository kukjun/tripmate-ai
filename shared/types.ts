/**
 * TripMate AI - Shared Type Definitions
 *
 * 이 파일은 Backend(Python)와 Frontend(TypeScript)에서 공통으로 사용되는
 * 타입 정의를 포함합니다. 양쪽 코드베이스에서 일관성을 유지하기 위해 사용됩니다.
 *
 * Python에서는 src/models/state.py를 참조하세요.
 * TypeScript에서는 frontend/src/types/index.ts를 참조하세요.
 */

// ===========================
// Common Enums/Literals
// ===========================

/**
 * 현재 여행 계획 단계
 */
export type TravelStep =
  | 'collecting' // 정보 수집 중
  | 'searching_flights' // 항공권 검색 중
  | 'searching_hotels' // 숙박 검색 중
  | 'planning' // 일정 생성 중
  | 'done'; // 완료

/**
 * 옵션 타입 (항공권, 숙박)
 */
export type OptionType = 'budget' | 'standard' | 'premium';

/**
 * 활동 타입
 */
export type ActivityType =
  | 'transport' // 이동
  | 'sightseeing' // 관광
  | 'food' // 식사
  | 'shopping' // 쇼핑
  | 'rest'; // 휴식

/**
 * 메시지 역할
 */
export type MessageRole = 'user' | 'assistant' | 'system';

// ===========================
// Flight Types
// ===========================

export interface FlightTime {
  departure_time: string; // "HH:MM"
  arrival_time: string; // "HH:MM"
  flight_time: string; // "Xh XXm"
}

export interface FlightOption {
  type: OptionType;
  price: number; // 왕복 가격 (원)
  airline: string;
  outbound: FlightTime; // 가는 편
  inbound: FlightTime; // 오는 편
}

// ===========================
// Hotel Types
// ===========================

export interface HotelOption {
  type: OptionType;
  name: string;
  price_per_night: number; // 1박 가격 (원)
  total_price: number; // 총 가격 (원)
  location: string;
  rating: number; // 0.0 ~ 5.0
  amenities: string[];
  distance_from_center: string; // "X.Xkm"
}

// ===========================
// Itinerary Types
// ===========================

export interface Activity {
  time: string; // "HH:MM"
  activity: string;
  type: ActivityType;
  location?: string;
  duration?: string;
  description?: string;
}

export interface DayPlan {
  date: string; // "YYYY-MM-DD"
  theme: string;
  activities: Activity[];
}

export interface Itinerary {
  [key: string]: DayPlan; // day1, day2, ...
}

// ===========================
// Chat Types
// ===========================

export interface Message {
  role: MessageRole;
  content: string;
  timestamp?: string;
}

// ===========================
// Travel State
// ===========================

export interface TravelState {
  // User Input
  destination: string;
  duration: number; // 박 수
  budget: number; // 원 (1인)
  num_people: number;
  travel_style: string[];

  // Progress
  info_collected: boolean;
  current_step: TravelStep;

  // Search Results
  flight_options: FlightOption[];
  hotel_options: HotelOption[];
  itinerary: Itinerary;

  // Chat History
  messages: Message[];

  // Metadata
  session_id: string;
  created_at: string; // ISO format
  updated_at: string; // ISO format
  error?: string | null;
}

// ===========================
// API Request/Response
// ===========================

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  state?: TravelState;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  version: string;
  environment?: string;
}
