from __future__ import annotations

import logging
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("fragdieki.stt")


class STTServiceError(RuntimeError):
    pass


@dataclass
class STTService:
    engine: str = "faster-whisper"
    model: str = "small"
    language: str = "de"
    vad: bool = True
    command: str = ""
    fallback_transcript: str = "Ich bin ein Platzhalter-Transkript. Bitte STT-Engine verbinden."

    def transcribe(self, audio_path: Path) -> str:
        if not self.command:
            return self.fallback_transcript

        try:
            with tempfile.TemporaryDirectory() as td:
                out_dir = Path(td)
                argv_template = shlex.split(self.command)
                argv = [
                    token.format(
                        input=str(audio_path),
                        output_dir=str(out_dir),
                        engine=self.engine,
                        model=self.model,
                        language=self.language,
                        vad=str(self.vad).lower(),
                    )
                    for token in argv_template
                ]
                subprocess.run(argv, check=True, capture_output=True, text=True)
                txt_files = sorted(out_dir.glob("*.txt"))
                if txt_files:
                    text = txt_files[0].read_text(encoding="utf-8").strip()
                    if text:
                        return text
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            logger.warning("stt_bridge_failed input=%s error=%s", audio_path, exc)
            raise STTServiceError("Spracherkennung gerade nicht verfügbar") from exc

        logger.warning("stt_bridge_empty_result input=%s", audio_path)
        raise STTServiceError("Spracherkennung lieferte kein Transkript")

    def ready(self) -> str:
        return "configured" if self.command else "fallback"
