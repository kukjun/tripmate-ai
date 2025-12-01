"""Tests for API endpoints."""

import pytest


class TestHealthCheck:
    """Health Check API 테스트."""

    def test_health_check(self, client):
        """헬스체크 엔드포인트 테스트."""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestChatAPI:
    """Chat API 테스트."""

    def test_chat_new_session(self, client):
        """새 세션으로 채팅 테스트."""
        response = client.post(
            "/api/chat",
            json={"message": "안녕하세요"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "reply" in data
        assert "session_id" in data
        assert "state" in data
        assert "progress" in data

    def test_chat_with_destination(self, client):
        """목적지 입력 채팅 테스트."""
        # 첫 메시지
        response1 = client.post(
            "/api/chat",
            json={"message": "오사카"},
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # 상태 확인
        state = response1.json()["state"]
        assert state["destination"] == "오사카"

    def test_chat_extracts_multiple_info(self, client):
        """복합 정보 추출 테스트."""
        response = client.post(
            "/api/chat",
            json={"message": "오사카 3박4일 100만원 2명이서 관광이랑 맛집"},
        )
        assert response.status_code == 200

        state = response.json()["state"]
        assert state["destination"] == "오사카"
        assert state["duration"] == 3
        assert state["budget"] == 1000000
        assert state["num_people"] == 2
        assert "관광" in state["travel_style"]
        assert "맛집" in state["travel_style"]

    def test_chat_continues_session(self, client):
        """세션 연속성 테스트."""
        # 첫 메시지
        response1 = client.post(
            "/api/chat",
            json={"message": "오사카"},
        )
        session_id = response1.json()["session_id"]

        # 두 번째 메시지 (같은 세션)
        response2 = client.post(
            "/api/chat",
            json={
                "message": "3박4일",
                "session_id": session_id,
            },
        )
        assert response2.status_code == 200

        state = response2.json()["state"]
        assert state["destination"] == "오사카"
        assert state["duration"] == 3

    def test_chat_progress(self, client):
        """진행 상태 테스트."""
        response = client.post(
            "/api/chat",
            json={"message": "오사카"},
        )

        progress = response.json()["progress"]
        assert "current" in progress
        assert "total" in progress
        assert "percentage" in progress
        assert progress["current"] >= 1

    def test_chat_empty_message_fails(self, client):
        """빈 메시지 실패 테스트."""
        response = client.post(
            "/api/chat",
            json={"message": ""},
        )
        assert response.status_code == 422  # Validation error


class TestPlanAPI:
    """Plan API 테스트."""

    def test_get_plan_not_found(self, client):
        """존재하지 않는 플랜 조회 테스트."""
        response = client.get("/api/plan/nonexistent-session")
        assert response.status_code == 404

    def test_get_flights_not_found(self, client):
        """존재하지 않는 항공권 조회 테스트."""
        response = client.get("/api/plan/nonexistent-session/flights")
        assert response.status_code == 404

    def test_get_hotels_not_found(self, client):
        """존재하지 않는 숙박 조회 테스트."""
        response = client.get("/api/plan/nonexistent-session/hotels")
        assert response.status_code == 404

    def test_get_itinerary_not_found(self, client):
        """존재하지 않는 일정 조회 테스트."""
        response = client.get("/api/plan/nonexistent-session/itinerary")
        assert response.status_code == 404


class TestSessionsAPI:
    """Sessions API 테스트."""

    def test_list_sessions(self, client):
        """세션 목록 조회 테스트."""
        response = client.get("/api/sessions")
        assert response.status_code == 200

        data = response.json()
        assert "sessions" in data
        assert "total" in data
        assert isinstance(data["sessions"], list)

    def test_delete_session_not_found(self, client):
        """존재하지 않는 세션 삭제 테스트."""
        response = client.delete("/api/sessions/nonexistent-session")
        assert response.status_code == 404


class TestFullFlow:
    """전체 플로우 통합 테스트."""

    def test_complete_flow(self, client):
        """완전한 여행 계획 플로우 테스트."""
        # 1. 모든 정보를 한번에 입력
        response = client.post(
            "/api/chat",
            json={"message": "오사카 3박4일 100만원 2명이서 관광이랑 맛집 여행 가고 싶어"},
        )
        assert response.status_code == 200

        data = response.json()
        session_id = data["session_id"]

        # 정보 수집 완료 확인
        assert data["state"]["info_collected"] is True

        # 여행 계획 완료 확인 (자동으로 검색 및 계획 수행)
        assert data["is_complete"] is True

        # 2. 플랜 조회
        plan_response = client.get(f"/api/plan/{session_id}")
        assert plan_response.status_code == 200

        plan_data = plan_response.json()
        assert plan_data["status"] == "completed"
        assert "flights" in plan_data["plan"]
        assert "hotels" in plan_data["plan"]
        assert "itinerary" in plan_data["plan"]

        # 3. 항공권 옵션 확인
        assert len(plan_data["plan"]["flights"]) == 3

        # 4. 숙박 옵션 확인
        assert len(plan_data["plan"]["hotels"]) == 3

        # 5. 일정 확인
        assert len(plan_data["plan"]["itinerary"]) == 4  # 3박 4일

        # 6. 예산 계산 확인
        assert "budget_breakdown" in plan_data["plan"]
        assert plan_data["plan"]["budget_breakdown"]["total"] > 0
