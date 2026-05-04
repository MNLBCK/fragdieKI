from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class TurnRecord(BaseModel):
    turn_id: str
    timestamp: datetime
    session_id: str
    device_id: str
    mode: str
    transcript: str
    answer: str
    safety_state: str
    duration_ms: int


class TurnResponse(BaseModel):
    turn_id: str
    transcript: str
    answer_text: str
    audio_url: str
    safety_state: str
