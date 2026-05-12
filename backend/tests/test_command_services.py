from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from services.agent import AgentService
from services.stt import STTService, STTServiceError
from services.tts import TTSService


def test_stt_command_uses_argv_without_shell(tmp_path, monkeypatch) -> None:
    audio_path = tmp_path / "input file.wav"
    audio_path.write_bytes(b"audio")
    calls: list[list[str]] = []

    def fake_run(cmd, check, capture_output, text):
        assert check is True
        assert capture_output is True
        assert text is True
        assert isinstance(cmd, list)
        calls.append(cmd)

        out_dir = Path(cmd[cmd.index("--out") + 1])
        (out_dir / "result.txt").write_text(" erkannt ", encoding="utf-8")

    monkeypatch.setattr("services.stt.subprocess.run", fake_run)

    service = STTService(command='dummy-stt --in {input} --out {output_dir} --model {model} --lang {language}')
    transcript = service.transcribe(audio_path)

    assert transcript == "erkannt"
    assert calls
    assert any("input file.wav" in part for part in calls[0])


def test_stt_command_failure_raises_service_error(tmp_path, monkeypatch) -> None:
    audio_path = tmp_path / "input.wav"
    audio_path.write_bytes(b"audio")

    def fake_run(cmd, check, capture_output, text):
        raise FileNotFoundError(cmd[0])

    monkeypatch.setattr("services.stt.subprocess.run", fake_run)

    service = STTService(command="missing-stt --in {input} --out {output_dir}")

    with pytest.raises(STTServiceError):
        service.transcribe(audio_path)


def test_tts_command_passes_text_as_single_arg(tmp_path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, check, capture_output, text):
        assert check is True
        assert capture_output is True
        assert text is True
        assert isinstance(cmd, list)
        calls.append(cmd)

        out_file = Path(cmd[cmd.index("--output") + 1])
        out_file.write_bytes(b"audio")

    monkeypatch.setattr("services.tts.subprocess.run", fake_run)

    service = TTSService(audio_dir=tmp_path, command='dummy-tts --output {output} --text {text}')
    spoken_text = 'Hallo "Kind" && rm -rf /'
    audio_file = service.synthesize("turn-1", spoken_text)

    assert audio_file.exists()
    assert calls
    assert calls[0][calls[0].index("--text") + 1] == spoken_text


def test_tts_command_failure_falls_back_to_silent_audio(tmp_path, monkeypatch) -> None:
    def fake_run(cmd, check, capture_output, text):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr("services.tts.subprocess.run", fake_run)

    service = TTSService(audio_dir=tmp_path, command="dummy-tts --output {output} --text {text}")
    audio_file = service.synthesize("turn-2", "Hallo")

    assert audio_file.exists()
    assert audio_file.read_bytes().startswith(b"RIFF")


def test_agent_endpoint_failure_returns_safe_fallback(monkeypatch, tmp_path) -> None:
    class FailingClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr("services.agent.httpx.Client", FailingClient)

    service = AgentService(prompt_dir=tmp_path, endpoint="https://agent.example.test")

    assert service.ask("Warum regnet es?", session_id="s1", mode="explain") == "Ich habe gerade keine Verbindung zum Antwortdienst. Bitte versuch es gleich noch einmal."


def test_agent_endpoint_extracts_nested_response_text(monkeypatch, tmp_path) -> None:
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "Eine Wolke ist voller Wasser."}}]}

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr("services.agent.httpx.Client", Client)

    service = AgentService(prompt_dir=tmp_path, endpoint="https://agent.example.test")

    assert service.ask("Was ist eine Wolke?", session_id="s1", mode="explain") == "Eine Wolke ist voller Wasser."
