from __future__ import annotations

from pathlib import Path

from services.stt import STTService
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
