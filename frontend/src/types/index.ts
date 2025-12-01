/**
 * TripMate AI Frontend Type Definitions
 */

// ===========================
// API Response Types
// ===========================

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

// ===========================
// Chat Types
// ===========================

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  role: MessageRole;
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  state?: TravelState;
}

// ===========================
// Travel State Types
// ===========================

export type TravelStep =
  | 'collecting'
  | 'searching_flights'
  | 'searching_hotels'
  | 'planning'
  | 'done';

export type OptionType = 'budget' | 'standard' | 'premium';

export interface FlightTime {
  departure_time: string;
  arrival_time: string;
  flight_time: string;
}

export interface FlightOption {
  type: OptionType;
  price: number;
  airline: string;
  outbound: FlightTime;
  inbound: FlightTime;
}

export interface HotelOption {
  type: OptionType;
  name: string;
  price_per_night: number;
  total_price: number;
  location: string;
  rating: number;
  amenities: string[];
  distance_from_center: string;
}

export type ActivityType =
  | 'transport'
  | 'sightseeing'
  | 'food'
  | 'shopping'
  | 'rest';

export interface Activity {
  time: string;
  activity: string;
  type: ActivityType;
  location?: string;
  duration?: string;
  description?: string;
}

export interface DayPlan {
  date: string;
  theme: string;
  activities: Activity[];
}

export interface Itinerary {
  [key: string]: DayPlan; // day1, day2, ...
}

export interface TravelState {
  // User input
  destination: string;
  duration: number;
  budget: number;
  num_people: number;
  travel_style: string[];

  // Progress
  info_collected: boolean;
  current_step: TravelStep;

  // Search results
  flight_options: FlightOption[];
  hotel_options: HotelOption[];
  itinerary: Itinerary;

  // Chat history
  messages: Message[];

  // Meta
  session_id: string;
  created_at: string;
  updated_at: string;
  error?: string;
}

// ===========================
// Component Props Types
// ===========================

export interface ChatInterfaceProps {
  sessionId?: string;
  onComplete?: (state: TravelState) => void;
}

export interface PlanDisplayProps {
  state: TravelState;
}

export interface LoadingSpinnerProps {
  message?: string;
}
