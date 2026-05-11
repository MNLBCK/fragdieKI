# openClaw Voice Agent Backend (IST-Stand)

Dieses Backend implementiert die spezifizierte Voice-Pipeline als MVP-Referenz mit FastAPI.

## Architektur (aktuell)

- **API**: FastAPI (`backend/app.py`)
- **STT-Service**: `STTService` (Platzhalter für `faster-whisper`)
- **Safety-Service**: regelbasierte Klassifikation + sichere Antworten
- **Agent-Service**: Prompt-basierter Stub mit Mode-Hinweisen
- **TTS-Service**: Platzhalterausgabe als `.m4a`-Artefakt
- **Storage-Service**: JSONL-Verlauf für Eltern-History

## Implementierte Endpunkte

- `POST /api/v1/maxi/turn`
- `GET /api/v1/audio/{turn_id}.m4a`
- `GET /api/v1/parent/history`
- `POST /api/v1/ocr` — Foto-zu-Text (lokales Tesseract OCR, keine Cloud-Calls)
- `GET /health`

## Datenschutz im IST-Stand

- Upload-Audio wird nur temporär in `backend/data/uploads` abgelegt und nach dem Turn gelöscht.
- Roh-Audio wird nicht dauerhaft im Verlauf gespeichert.
- Verlauf speichert Zeitstempel, Transkript, Antwort, Modus, Safety-Status und Dauer.
- **Foto-OCR**: Hochgeladene Fotos werden lokal mit Tesseract OCR verarbeitet (keine Cloud-Calls zu OpenAI/Google). Bilder werden sofort nach der Verarbeitung gelöscht.

## Start lokal (macOS / Apple Silicon)

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Tesseract OCR installieren (für Foto-zu-Text Feature)
# macOS:
brew install tesseract tesseract-lang
# Linux:
# sudo apt-get install tesseract-ocr tesseract-ocr-deu

uvicorn app:app --host 127.0.0.1 --port 8787 --reload
```


> **Hinweis Netzwerk-Exposition**: Der Standard-Host `127.0.0.1` beschränkt den Zugriff auf
> das lokale Gerät. `--host 0.0.0.0` nur setzen, wenn der Zugriff über das lokale Netz
> bewusst gewünscht ist – `/api/v1/parent/history` enthält dann sensitive Gesprächsdaten.
> In dem Fall empfiehlt sich die `api.parent_history_api_key`-Option in `config.yaml`.

## Tests

```bash
cd backend
pytest -q
```

## Nächste Integrationen

- `STTService.transcribe`: echte `faster-whisper`-Pipeline
- `TTSService.synthesize`: echte Piper-CLI/Library
- `AgentService.ask`: openClaw-Bridge statt Stub


## Produktionsnahe Bridges (neu)

In `config.yaml` können echte Integrationen zugeschaltet werden:

- `stt.command`: CLI-Template für Transkription (`{input}`, `{output_dir}`, `{model}`, `{language}`)
- `tts.command`: CLI-Template für Audio-Erzeugung (`{output}`, `{text}`)
- `agent.endpoint`: HTTP-Endpoint für LLM/Agent-Antworten (+ optional `agent.api_key`)

Hinweis: `stt.command` und `tts.command` werden als Argumentliste ohne Shell ausgeführt
(`shell=False`). Shell-Operatoren wie Pipes/Redirects werden dabei absichtlich nicht unterstützt.

Wenn diese Felder leer sind, bleiben die sicheren Fallbacks aktiv.

## Observability (neu)

Pro Turn wird ein strukturierter Log-Eintrag mit Latenzen geschrieben:
- `stt_ms`, `agent_ms`, `tts_ms`, `total_ms`

## Load-Smoke-Test (neu)

```bash
cd backend
python scripts/load_smoke.py --base http://127.0.0.1:8787 --requests 20 --concurrency 4
```
