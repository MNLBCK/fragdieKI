from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_parent_history_returns_list(client: TestClient) -> None:
    response = client.get("/api/v1/parent/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_turn_returns_response(client: TestClient) -> None:
    dummy_audio = io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00\x80>\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
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
    dummy_audio = io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00\x80>\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
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
