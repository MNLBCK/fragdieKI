from __future__ import annotations

import subprocess
import tempfile
import shlex
from dataclasses import dataclass
from pathlib import Path


@dataclass
class STTService:
    model: str = "small"
    language: str = "de"
    command: str = ""

    def transcribe(self, audio_path: Path) -> str:
        if self.command:
            with tempfile.TemporaryDirectory() as td:
                out_dir = Path(td)
                argv_template = shlex.split(self.command)
                argv = [
                    token.format(
                        input=str(audio_path),
                        output_dir=str(out_dir),
                        model=self.model,
                        language=self.language,
                    )
                    for token in argv_template
                ]
                subprocess.run(argv, check=True, capture_output=True, text=True)
                txt_files = sorted(out_dir.glob('*.txt'))
                if txt_files:
                    text = txt_files[0].read_text(encoding='utf-8').strip()
                    if text:
                        return text
        return "Ich bin ein Platzhalter-Transkript. Bitte STT-Engine verbinden."

    def ready(self) -> str:
        return "ready"
