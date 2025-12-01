/**
 * API Client for TripMate AI Backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type { ChatRequest, ChatResponse, ApiResponse } from '@/types';

// API Base URL from environment
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds (for long AI operations)
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // No response received
      console.error('Network Error:', error.message);
    } else {
      // Request setup error
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ===========================
// API Functions
// ===========================

/**
 * Health check
 */
export async function healthCheck(): Promise<ApiResponse<{ status: string }>> {
  const response = await apiClient.get('/health');
  return response.data;
}

/**
 * Send chat message
 */
export async function sendMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await apiClient.post('/chat', request);
  return response.data;
}

/**
 * Get session by ID
 */
export async function getSession(sessionId: string): Promise<ChatResponse> {
  const response = await apiClient.get(`/sessions/${sessionId}`);
  return response.data;
}

export default apiClient;
