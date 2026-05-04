from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from services.agent import AgentService
from services.safety import SafetyService
from services.schemas import TurnRecord, TurnResponse
from services.storage import StorageService
from services.stt import STTService
from services.tts import TTSService

BASE_DIR = Path(__file__).resolve().parent
CONFIG = yaml.safe_load((BASE_DIR / "config.yaml").read_text(encoding="utf-8"))
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
UPLOAD_DIR = DATA_DIR / "uploads"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

stt_service = STTService(model=CONFIG["stt"]["model"], language=CONFIG["stt"]["language"])
safety_service = SafetyService()
agent_service = AgentService(prompt_dir=BASE_DIR / "prompts")
tts_service = TTSService(audio_dir=AUDIO_DIR)
storage_service = StorageService(data_dir=DATA_DIR)

app = FastAPI(title="openClaw Maxi Voice API", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "stt": stt_service.ready(), "tts": tts_service.ready(), "agent": agent_service.ready()}


@app.post("/api/v1/maxi/turn", response_model=TurnResponse)
async def create_turn(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    device_id: str = Form(...),
    mode: str = Form("explain"),
    client_version: str = Form("unknown"),
) -> TurnResponse:
    _ = client_version
    if audio.content_type not in {"audio/m4a", "audio/mp4", "audio/wav", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Unsupported audio type")

    turn_id = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / f"{turn_id}_{audio.filename or 'input.m4a'}"
    content = await audio.read()
    upload_path.write_bytes(content)

    started = time.perf_counter()
    transcript = stt_service.transcribe(upload_path)
    input_class = safety_service.classify_input(transcript)

    if input_class == "ok":
        answer = agent_service.ask(user_text=transcript, session_id=session_id, mode=mode)
    else:
        answer = safety_service.safe_response(input_class)

    answer = safety_service.check_output(answer)
    tts_service.synthesize(turn_id=turn_id, text=answer)
    duration_ms = int((time.perf_counter() - started) * 1000)

    storage_service.store_turn(
        TurnRecord(
            turn_id=turn_id,
            timestamp=datetime.now(UTC),
            session_id=session_id,
            device_id=device_id,
            mode=mode,
            transcript=transcript,
            answer=answer,
            safety_state=input_class,
            duration_ms=duration_ms,
        )
    )

    upload_path.unlink(missing_ok=True)

    return TurnResponse(
        turn_id=turn_id,
        transcript=transcript,
        answer_text=answer,
        audio_url=f"/api/v1/audio/{turn_id}.m4a",
        safety_state=input_class,
    )


@app.get("/api/v1/audio/{turn_id}.m4a")
async def get_audio(turn_id: str) -> FileResponse:
    path = AUDIO_DIR / f"{turn_id}.m4a"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(path, media_type="audio/mp4", filename=path.name)


@app.get("/api/v1/parent/history")
async def parent_history() -> list[dict[str, str]]:
    return storage_service.parent_history()
