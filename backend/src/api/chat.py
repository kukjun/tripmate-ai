"""Chat API Router for TripMate AI.

대화형 여행 플래너 API 엔드포인트입니다.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.graph.phase1_graph import get_phase1_graph
from src.models.state import TravelState, create_initial_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# 세션 저장소 (Phase 1: 메모리, 추후 Redis로 교체)
sessions: dict[str, TravelState] = {}

# 세션 파일 저장 경로
SESSIONS_DIR = "sessions"


def ensure_sessions_dir():
    """세션 저장 디렉토리 확인/생성."""
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)


def save_session(session_id: str, state: TravelState):
    """세션을 파일로 저장."""
    ensure_sessions_dir()
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(dict(state), f, ensure_ascii=False, indent=2)
    # 메모리에도 저장
    sessions[session_id] = state


def load_session(session_id: str) -> TravelState | None:
    """세션을 파일에서 로드."""
    # 메모리에서 먼저 확인
    if session_id in sessions:
        return sessions[session_id]

    # 파일에서 로드
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            state = json.load(f)
            sessions[session_id] = state
            return state

    return None


class ChatRequest(BaseModel):
    """채팅 요청 모델."""

    message: str = Field(..., min_length=1, description="사용자 메시지")
    session_id: str | None = Field(None, description="세션 ID (없으면 자동 생성)")


class ChatResponse(BaseModel):
    """채팅 응답 모델."""

    reply: str = Field(..., description="AI 응답 메시지")
    session_id: str = Field(..., description="세션 ID")
    state: dict = Field(..., description="현재 상태")
    progress: dict = Field(..., description="진행 상태")
    is_complete: bool = Field(False, description="여행 계획 완료 여부")


def get_progress(state: TravelState) -> dict:
    """진행 상태 계산."""
    total_fields = 5  # destination, duration, budget, num_people, travel_style
    collected = 0

    if state.get("destination"):
        collected += 1
    if state.get("duration") and state.get("duration", 0) > 0:
        collected += 1
    if state.get("budget") and state.get("budget", 0) > 0:
        collected += 1
    if state.get("num_people") and state.get("num_people", 0) > 0:
        collected += 1
    if state.get("travel_style"):
        collected += 1

    current_step = state.get("current_step", "collecting")

    if current_step == "done":
        return {
            "current": 5,
            "total": 5,
            "percentage": 100,
            "step": "done",
            "step_label": "완료",
        }

    step_labels = {
        "collecting": "정보 수집 중",
        "searching_flights": "항공권 검색 중",
        "searching_hotels": "숙박 검색 중",
        "planning": "일정 생성 중",
        "done": "완료",
    }

    return {
        "current": collected,
        "total": total_fields,
        "percentage": int((collected / total_fields) * 100),
        "step": current_step,
        "step_label": step_labels.get(current_step, current_step),
    }


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """채팅 API 엔드포인트.

    사용자 메시지를 받아 AI Agent 응답을 반환합니다.
    """
    try:
        # 세션 ID 확인 또는 생성
        session_id = request.session_id or str(uuid4())

        # 기존 세션 로드 또는 새 세션 생성
        state = load_session(session_id)
        if state is None:
            state = create_initial_state(session_id)
            logger.info(f"Created new session: {session_id}")
        else:
            logger.info(f"Loaded existing session: {session_id}")

        # 사용자 메시지 추가
        messages = list(state.get("messages", []))
        messages.append({"role": "user", "content": request.message})
        state["messages"] = messages
        state["updated_at"] = datetime.now().isoformat()

        # LangGraph 워크플로우 실행
        graph = get_phase1_graph()
        result = graph.invoke(dict(state))

        # 결과를 TravelState로 변환
        updated_state = TravelState(**{**state, **result})

        # 세션 저장
        save_session(session_id, updated_state)

        # 마지막 Assistant 메시지 가져오기
        all_messages = updated_state.get("messages", [])
        assistant_messages = [m for m in all_messages if m.get("role") == "assistant"]
        last_reply = assistant_messages[-1]["content"] if assistant_messages else ""

        # 진행 상태 계산
        progress = get_progress(updated_state)

        # 응답 반환
        return ChatResponse(
            reply=last_reply,
            session_id=session_id,
            state={
                "destination": updated_state.get("destination", ""),
                "duration": updated_state.get("duration", 0),
                "budget": updated_state.get("budget", 0),
                "num_people": updated_state.get("num_people", 0),
                "travel_style": updated_state.get("travel_style", []),
                "info_collected": updated_state.get("info_collected", False),
                "current_step": updated_state.get("current_step", "collecting"),
            },
            progress=progress,
            is_complete=updated_state.get("current_step") == "done",
        )

    except Exception as e:
        logger.exception(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


@router.get("/{session_id}/history")
async def get_chat_history(session_id: str):
    """대화 히스토리 조회."""
    state = load_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return {
        "session_id": session_id,
        "messages": state.get("messages", []),
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at"),
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제."""
    # 메모리에서 삭제
    if session_id in sessions:
        del sessions[session_id]

    # 파일 삭제
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"message": "세션이 삭제되었습니다", "session_id": session_id}

    raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
