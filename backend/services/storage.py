from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .schemas import TurnRecord


@dataclass(slots=True)
class StorageService:
    data_dir: Path
    history_file: Path = field(init=False)

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "turn_history.jsonl"

    def store_turn(self, record: TurnRecord) -> None:
        with self.history_file.open("a", encoding="utf-8") as fp:
            fp.write(record.model_dump_json() + "\n")

    def parent_history(self) -> list[dict[str, Any]]:
        if not self.history_file.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.history_file.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            rows.append(
                {
                    "timestamp": item["timestamp"],
                    "transcript": item["transcript"],
                    "answer": item["answer"],
                    "mode": item["mode"],
                    "safety_state": item["safety_state"],
                }
            )
        return rows
