from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TTSService:
    audio_dir: Path

    def synthesize(self, turn_id: str, text: str) -> Path:
        target = self.audio_dir / f"{turn_id}.m4a"
        # Platzhalter: schreibt Textdatei mit .m4a-Endung für API-Fluss.
        target.write_text(f"TTS_PLACEHOLDER\n{text}\n", encoding="utf-8")
        return target

    def ready(self) -> str:
        return "ready"
