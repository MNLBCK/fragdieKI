from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .schemas import TurnRecord


@dataclass
class StorageService:
    data_dir: Path
    retention_days: int = 30
    history_file: Path = field(init=False)
    _lock: threading.Lock = field(init=False, default_factory=threading.Lock)

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "turn_history.jsonl"

    def store_turn(self, record: TurnRecord) -> None:
        line = record.model_dump_json() + "\n"
        with self._lock:
            with self.history_file.open("a", encoding="utf-8") as fp:
                fp.write(line)

    def parent_history(self) -> list[dict[str, Any]]:
        if not self.history_file.exists():
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        rows: list[dict[str, Any]] = []
        with self._lock:
            lines = self.history_file.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                ts = datetime.fromisoformat(item["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
            except (KeyError, ValueError):
                pass
            rows.append(
                {
                    "timestamp": item.get("timestamp", ""),
                    "transcript": item.get("transcript", ""),
                    "answer": item.get("answer", ""),
                    "mode": item.get("mode", ""),
                    "safety_state": item.get("safety_state", ""),
                }
            )
        return rows
