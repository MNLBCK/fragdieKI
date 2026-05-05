# fragdieKI

Voice-Agent-Backend für kindgerechte Gespräche mit Safety-Layer und Eltern-History.

## Repository-Struktur

- `backend/` — FastAPI-Backend gemäß openClaw-Voice-Spec

## Schnellstart

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8787 --reload
```
