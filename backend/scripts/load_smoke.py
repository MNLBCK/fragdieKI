#!/usr/bin/env python3
"""Very small load smoke test for /api/v1/maxi/turn.
Usage: python scripts/load_smoke.py --base http://127.0.0.1:8787 --requests 10 --concurrency 2
"""
from __future__ import annotations

import argparse
import asyncio
import io
import time

import httpx

DUMMY_WAV = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00\x80>\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"


async def one(client: httpx.AsyncClient, base: str, i: int) -> float:
    started = time.perf_counter()
    files = {"audio": (f"test-{i}.wav", io.BytesIO(DUMMY_WAV), "audio/wav")}
    data = {"session_id": f"s-{i}", "device_id": f"d-{i%3}", "mode": "explain"}
    r = await client.post(f"{base}/api/v1/maxi/turn", data=data, files=files)
    r.raise_for_status()
    return (time.perf_counter() - started) * 1000


async def run(base: str, requests: int, concurrency: int) -> None:
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(timeout=30) as client:
        async def wrapped(i: int) -> float:
            async with sem:
                return await one(client, base, i)

        latencies = await asyncio.gather(*(wrapped(i) for i in range(requests)))

    latencies = sorted(latencies)
    p50 = latencies[int(len(latencies) * 0.5)]
    p95 = latencies[int(len(latencies) * 0.95) - 1]
    print(f"requests={requests} concurrency={concurrency} p50_ms={p50:.1f} p95_ms={p95:.1f} max_ms={latencies[-1]:.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8787")
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=2)
    args = parser.parse_args()
    asyncio.run(run(args.base, args.requests, args.concurrency))
