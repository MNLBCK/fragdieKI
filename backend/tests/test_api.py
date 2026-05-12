from __future__ import annotations

import io
import logging

import pytest
from fastapi.testclient import TestClient

from app import AGENT_FAILURE_ANSWER, STT_FAILURE_ANSWER, agent_service, app, stt_service
from services.stt import STTServiceError

SILENT_WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00\x80>\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["stt"] in {"configured", "fallback"}
    assert data["tts"] in {"configured", "fallback"}
    assert data["agent"] in {"configured", "fallback"}
    assert data["ocr"] in {"ready", "unavailable"}


def test_parent_history_returns_list(client: TestClient) -> None:
    response = client.get("/api/v1/parent/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_turn_returns_response(client: TestClient) -> None:
    dummy_audio = io.BytesIO(SILENT_WAV_BYTES)
    response = client.post(
        "/api/v1/maxi/turn",
        data={"session_id": "test-session", "device_id": "test-device", "mode": "explain"},
        files={"audio": ("test.wav", dummy_audio, "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "turn_id" in data
    assert "transcript" in data
    assert "answer_text" in data
    assert "audio_url" in data
    assert data["audio_url"].endswith(".m4a")


def test_get_audio_after_turn(client: TestClient) -> None:
    # Only run if delete_audio_after_turn is False (stub may delete immediately).
    # Perform a turn and check if the audio endpoint responds meaningfully.
    dummy_audio = io.BytesIO(SILENT_WAV_BYTES)
    turn_response = client.post(
        "/api/v1/maxi/turn",
        data={"session_id": "test-session", "device_id": "test-device", "mode": "explain"},
        files={"audio": ("test.wav", dummy_audio, "audio/wav")},
    )
    assert turn_response.status_code == 200
    audio_url = turn_response.json()["audio_url"]
    audio_response = client.get(audio_url)
    # Either 200 (audio present) or 404 (deleted by delete_audio_after_turn flag)
    assert audio_response.status_code in {200, 404}


def test_audio_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/audio/nonexistent-turn-id.m4a")
    assert response.status_code == 404


def test_ocr_endpoint_with_invalid_image(client: TestClient) -> None:
    """Test OCR endpoint with invalid image data."""
    dummy_data = io.BytesIO(b"not an image")
    response = client.post(
        "/api/v1/ocr",
        data={"device_id": "test-device"},
        files={"image": ("test.jpg", dummy_data, "image/jpeg")},
    )
    # 503 if OCR binary is unavailable in runtime environment, otherwise 422/500 for bad image data.
    assert response.status_code in {422, 500, 503}


def test_create_turn_returns_safe_answer_when_stt_bridge_fails(client: TestClient, monkeypatch, caplog) -> None:
    dummy_audio = io.BytesIO(SILENT_WAV_BYTES)

    def fail_transcribe(_path):
        raise STTServiceError("no model")

    monkeypatch.setattr(stt_service, "transcribe", fail_transcribe)

    with caplog.at_level(logging.INFO, logger="fragdieki"):
        response = client.post(
            "/api/v1/maxi/turn",
            data={"session_id": "test-session", "device_id": "test-device", "mode": "explain"},
            files={"audio": ("test.wav", dummy_audio, "audio/wav")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == ""
    assert data["answer_text"] == STT_FAILURE_ANSWER
    assert any("stt_ms=" in record.message and "total_ms=" in record.message for record in caplog.records)


def test_create_turn_returns_safe_answer_when_agent_bridge_raises(client: TestClient, monkeypatch) -> None:
    dummy_audio = io.BytesIO(SILENT_WAV_BYTES)

    monkeypatch.setattr(stt_service, "transcribe", lambda _path: "Warum ist der Himmel blau?")

    def fail_agent(*args, **kwargs):
        raise RuntimeError("bridge down")

    monkeypatch.setattr(agent_service, "ask", fail_agent)

    response = client.post(
        "/api/v1/maxi/turn",
        data={"session_id": "test-session", "device_id": "test-device", "mode": "explain"},
        files={"audio": ("test.wav", dummy_audio, "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json()["answer_text"] == AGENT_FAILURE_ANSWER
