from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AgentService:
    prompt_dir: Path

    def ask(self, user_text: str, session_id: str, mode: str) -> str:
        mode_hint = self._load_mode_hint(mode)
        base = "Ich erkläre es dir ganz einfach"
        if mode_hint:
            base = f"{base} im Modus {mode}"
        return f"{base}: {user_text[:140]}."

    def _load_mode_hint(self, mode: str) -> str:
        mode_file = self.prompt_dir / f"modes.{mode}.md"
        if mode_file.exists():
            return mode_file.read_text(encoding="utf-8").strip()
        return ""

    def ready(self) -> str:
        return "ready"
