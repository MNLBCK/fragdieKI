from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import yaml
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from services.agent import AgentService
from services.ocr import OCRService
from services.safety import SafetyService
from services.schemas import TurnRecord, TurnResponse
from services.storage import StorageService
from services.stt import STTService
from services.tts import TTSService

BASE_DIR = Path(__file__).resolve().parent
_config_path = Path(os.environ.get("APP_CONFIG_PATH", BASE_DIR / "config.yaml"))
CONFIG = yaml.safe_load(_config_path.read_text(encoding="utf-8"))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("fragdieki")

DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
UPLOAD_DIR = DATA_DIR / "uploads"
IMAGE_DIR = DATA_DIR / "images"

# Max upload size in bytes (default 20 MB); can be set in config as stt.max_upload_bytes
MAX_UPLOAD_BYTES: int = int(CONFIG["stt"].get("max_upload_bytes", 20 * 1024 * 1024))
MAX_IMAGE_BYTES: int = int(CONFIG.get("ocr", {}).get("max_image_bytes", 10 * 1024 * 1024))
MAX_TURNS_PER_MINUTE: int = int(CONFIG.get("api", {}).get("max_turns_per_minute", 30))

stt_service = STTService(model=CONFIG["stt"]["model"], language=CONFIG["stt"]["language"], command=CONFIG["stt"].get("command", ""))
safety_service = SafetyService()
agent_service = AgentService(prompt_dir=BASE_DIR / "prompts", endpoint=CONFIG.get("agent", {}).get("endpoint", ""), api_key=CONFIG.get("agent", {}).get("api_key", ""), timeout_seconds=float(CONFIG.get("agent", {}).get("timeout_seconds", 20)))
tts_service = TTSService(audio_dir=AUDIO_DIR, command=CONFIG["tts"].get("command", ""))
ocr_service = OCRService(language=CONFIG.get("ocr", {}).get("language", "deu"))
storage_service = StorageService(
    data_dir=DATA_DIR,
    retention_days=int(CONFIG["storage"].get("text_retention_days", 30)),
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="openClaw Maxi Voice API", version="0.1.0", lifespan=lifespan)


_rate_lock = threading.Lock()
_rate_bucket: dict[str, list[float]] = {}


def _enforce_turn_rate_limit(device_id: str) -> None:
    if MAX_TURNS_PER_MINUTE <= 0:
        return
    now = time.time()
    cutoff = now - 60
    key = device_id or "unknown"
    with _rate_lock:
        entries = [ts for ts in _rate_bucket.get(key, []) if ts >= cutoff]
        if len(entries) >= MAX_TURNS_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Too many requests")
        entries.append(now)
        _rate_bucket[key] = entries

def _require_api_key(x_api_key: str, key_name: str) -> None:
    """Enforce API key for protected endpoints when configured."""
    required_key: str = CONFIG.get("api", {}).get(key_name, "")
    if required_key and x_api_key != required_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "stt": stt_service.ready(), "tts": tts_service.ready(), "agent": agent_service.ready(), "ocr": ocr_service.ready()}


@app.post("/api/v1/maxi/turn", response_model=TurnResponse)
async def create_turn(
    request: Request,
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    device_id: str = Form(...),
    mode: str = Form("explain"),
    client_version: str = Form("unknown"),
) -> TurnResponse:
    _ = client_version
    _require_api_key(request.headers.get("x-api-key", ""), "turn_api_key")
    _enforce_turn_rate_limit(device_id)
    if audio.content_type not in {"audio/m4a", "audio/mp4", "audio/wav", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Unsupported audio type")

    turn_id = str(uuid.uuid4())
    # Use only the basename to prevent path traversal via a crafted filename
    safe_filename = Path(audio.filename or "input.m4a").name
    upload_path = UPLOAD_DIR / f"{turn_id}_{safe_filename}"

    # Stream to disk in chunks, enforcing upload size limit
    total_bytes = 0
    try:
        with upload_path.open("wb") as fp:
            while True:
                chunk = await audio.read(8192)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Audio file too large")
                fp.write(chunk)

        started = time.perf_counter()
        stt_started = time.perf_counter()
        transcript = stt_service.transcribe(upload_path)
        stt_ms = int((time.perf_counter() - stt_started) * 1000)
        input_class = safety_service.classify_input(transcript)

        agent_ms = 0
        if input_class == "ok":
            agent_started = time.perf_counter()
            answer = agent_service.ask(user_text=transcript, session_id=session_id, mode=mode)
            agent_ms = int((time.perf_counter() - agent_started) * 1000)
        else:
            answer = safety_service.safe_response(input_class)

        answer = safety_service.check_output(answer)
        tts_started = time.perf_counter()
        audio_path = tts_service.synthesize(turn_id=turn_id, text=answer)
        tts_ms = int((time.perf_counter() - tts_started) * 1000)
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info("turn_complete turn_id=%s session_id=%s mode=%s safety=%s stt_ms=%s agent_ms=%s tts_ms=%s total_ms=%s", turn_id, session_id, mode, input_class, stt_ms, agent_ms, tts_ms, duration_ms)

        storage_service.store_turn(
            TurnRecord(
                turn_id=turn_id,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                device_id=device_id,
                mode=mode,
                transcript=transcript,
                answer=answer,
                safety_state=input_class,
                duration_ms=duration_ms,
            )
        )

        if CONFIG["storage"].get("delete_audio_after_turn", False):
            audio_path.unlink(missing_ok=True)

    finally:
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


@app.post("/api/v1/ocr")
async def extract_text_from_image(
    request: Request,
    image: UploadFile = File(...),
    device_id: str = Form(...),
) -> dict[str, str]:
    """
    Extract text from an uploaded image using local OCR (Tesseract).
    No external API calls are made - all processing happens on the family backend.
    """
    _require_api_key(request.headers.get("x-api-key", ""), "turn_api_key")
    _enforce_turn_rate_limit(device_id)

    if image.content_type not in {"image/jpeg", "image/jpg", "image/png", "image/heic", "image/heif", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    ocr_id = str(uuid.uuid4())
    safe_filename = Path(image.filename or "image.jpg").name
    image_path = IMAGE_DIR / f"{ocr_id}_{safe_filename}"

    # Stream to disk in chunks, enforcing image size limit
    total_bytes = 0
    try:
        with image_path.open("wb") as fp:
            while True:
                chunk = await image.read(8192)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_IMAGE_BYTES:
                    raise HTTPException(status_code=413, detail="Image file too large")
                fp.write(chunk)

        started = time.perf_counter()
        text = ocr_service.extract_text(image_path)
        duration_ms = int((time.perf_counter() - started) * 1000)

        logger.info("ocr_complete ocr_id=%s device_id=%s chars=%d duration_ms=%d", ocr_id, device_id, len(text), duration_ms)

        return {
            "ocr_id": ocr_id,
            "text": text,
        }

    except ValueError as e:
        logger.warning("OCR failed for %s: %s", ocr_id, e)
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        logger.error("OCR processing error for %s: %s", ocr_id, e)
        if str(e) == "OCR service unavailable":
            raise HTTPException(status_code=503, detail="OCR service unavailable") from e
        raise HTTPException(status_code=500, detail="OCR processing failed") from e
    finally:
        # Clean up uploaded image immediately after processing
        image_path.unlink(missing_ok=True)


@app.get("/api/v1/parent/history")
async def parent_history(request: Request) -> list[dict[str, str]]:
    _require_api_key(request.headers.get("x-api-key", ""), "parent_history_api_key")
    return storage_service.parent_history()
