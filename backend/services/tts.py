from __future__ import annotations

import struct
import subprocess
import shlex
from dataclasses import dataclass
from pathlib import Path


# Minimal silent WAV header (44 bytes, 0 samples, 8000 Hz, mono, 16-bit PCM)
def _silent_wav() -> bytes:
    sample_rate = 8000
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = 0
    riff_size = 36 + data_size
    return (
        b"RIFF"
        + struct.pack("<I", riff_size)
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
        + b"data"
        + struct.pack("<I", data_size)
    )


@dataclass
class TTSService:
    audio_dir: Path
    command: str = ""

    def synthesize(self, turn_id: str, text: str) -> Path:
        target = self.audio_dir / f"{turn_id}.m4a"
        if self.command:
            argv_template = shlex.split(self.command)
            argv = [token.format(output=str(target), text=text) for token in argv_template]
            subprocess.run(argv, check=True, capture_output=True, text=True)
            if target.exists() and target.stat().st_size > 0:
                return target

        # Fallback stub
        target.write_bytes(_silent_wav())
        return target

    def ready(self) -> str:
        return "ready"
