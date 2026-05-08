from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class AgentService:
    prompt_dir: Path
    endpoint: str = ""
    api_key: str = ""
    timeout_seconds: float = 20.0

    def ask(self, user_text: str, session_id: str, mode: str) -> str:
        if self.endpoint:
            payload = {
                "session_id": session_id,
                "mode": mode,
                "message": user_text,
            }
            headers = {"content-type": "application/json"}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    resp = client.post(self.endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    text = (data.get("answer") or data.get("text") or "").strip()
                    if text:
                        return text
            except Exception:
                pass

        mode_hint = self._load_mode_hint(mode)
        base = "Ich erkläre es dir ganz einfach"
        if mode_hint:
            base = f"{base} ({mode_hint})"
        return f"{base}: {user_text[:140]}."

    def _load_mode_hint(self, mode: str) -> str:
        mode_file = self.prompt_dir / f"modes.{mode}.md"
        if mode_file.exists():
            return mode_file.read_text(encoding="utf-8").strip()
        return ""

    def ready(self) -> str:
        return "ready"
