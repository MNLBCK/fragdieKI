from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class STTService:
    model: str = "small"
    language: str = "de"

    def transcribe(self, audio_path: Path) -> str:
        # Platzhalter für faster-whisper Integration.
        # MVP: Rückfalltranskript, falls kein STT-Backend verdrahtet ist.
        return "Ich bin ein Platzhalter-Transkript. Bitte STT-Engine verbinden."

    def ready(self) -> str:
        return "ready"
