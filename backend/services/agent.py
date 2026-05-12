from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("fragdieki.agent")


@dataclass
class AgentService:
    prompt_dir: Path
    endpoint: str = ""
    api_key: str = ""
    timeout_seconds: float = 20.0

    def ask(self, user_text: str, session_id: str, mode: str) -> str:
        mode_hint = self._load_mode_hint(mode)
        if self.endpoint:
            payload = {
                "session_id": session_id,
                "mode": mode,
                "message": user_text,
                "mode_hint": mode_hint,
            }
            headers = {"content-type": "application/json"}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    resp = client.post(self.endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    text = self._extract_text(resp.json())
                    if text:
                        return text
                    logger.warning("agent_bridge_empty_response endpoint=%s", self.endpoint)
            except Exception as exc:
                logger.warning("agent_bridge_failed endpoint=%s error=%s", self.endpoint, exc)
            return "Ich habe gerade keine Verbindung zum Antwortdienst. Bitte versuch es gleich noch einmal."

        base = "Ich erkläre es dir ganz einfach"
        if mode_hint:
            base = f"{base} ({mode_hint})"
        return f"{base}: {user_text[:140]}."

    def _extract_text(self, payload: Any) -> str:
        if isinstance(payload, str):
            return payload.strip()
        if isinstance(payload, dict):
            for key in ("answer", "text", "message", "content"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            for key in ("response", "output"):
                value = payload.get(key)
                text = self._extract_text(value)
                if text:
                    return text
            choices = payload.get("choices")
            if isinstance(choices, list):
                for item in choices:
                    text = self._extract_text(item)
                    if text:
                        return text
            for value in payload.values():
                text = self._extract_text(value)
                if text:
                    return text
        if isinstance(payload, list):
            for item in payload:
                text = self._extract_text(item)
                if text:
                    return text
        return ""

    def _load_mode_hint(self, mode: str) -> str:
        mode_file = self.prompt_dir / f"modes.{mode}.md"
        if mode_file.exists():
            return mode_file.read_text(encoding="utf-8").strip()
        return ""

    def ready(self) -> str:
        return "configured" if self.endpoint else "fallback"
