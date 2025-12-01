"""Sessions API Router for TripMate AI.

세션 관리 API 엔드포인트입니다.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])

# 세션 파일 저장 경로
SESSIONS_DIR = "sessions"


def ensure_sessions_dir():
    """세션 저장 디렉토리 확인/생성."""
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)


class SessionSummary(BaseModel):
    """세션 요약 모델."""

    session_id: str
    destination: str | None
    duration: int | None
    status: str
    created_at: str
    updated_at: str


class SessionsListResponse(BaseModel):
    """세션 목록 응답 모델."""

    sessions: list[SessionSummary]
    total: int


@router.get("", response_model=SessionsListResponse)
async def list_sessions():
    """모든 세션 목록 조회."""
    ensure_sessions_dir()

    sessions = []
    session_files = [
        f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")
    ]

    for filename in session_files:
        filepath = os.path.join(SESSIONS_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state = json.load(f)

            session_id = filename.replace(".json", "")
            current_step = state.get("current_step", "collecting")

            status = "completed" if current_step == "done" else "in_progress"

            sessions.append(
                SessionSummary(
                    session_id=session_id,
                    destination=state.get("destination") or None,
                    duration=state.get("duration") if state.get("duration") else None,
                    status=status,
                    created_at=state.get("created_at", ""),
                    updated_at=state.get("updated_at", ""),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to load session {filename}: {e}")
            continue

    # 최신순 정렬
    sessions.sort(key=lambda x: x.updated_at, reverse=True)

    return SessionsListResponse(sessions=sessions, total=len(sessions))


@router.get("/{session_id}")
async def get_session(session_id: str):
    """특정 세션 상세 조회."""
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    with open(filepath, "r", encoding="utf-8") as f:
        state = json.load(f)

    return {
        "session_id": session_id,
        "state": state,
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제."""
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    os.remove(filepath)

    return {
        "message": "세션이 삭제되었습니다",
        "session_id": session_id,
    }


@router.delete("")
async def delete_all_sessions():
    """모든 세션 삭제."""
    ensure_sessions_dir()

    deleted_count = 0
    session_files = [
        f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")
    ]

    for filename in session_files:
        filepath = os.path.join(SESSIONS_DIR, filename)
        try:
            os.remove(filepath)
            deleted_count += 1
        except Exception as e:
            logger.warning(f"Failed to delete session {filename}: {e}")

    return {
        "message": f"{deleted_count}개 세션이 삭제되었습니다",
        "deleted_count": deleted_count,
    }
