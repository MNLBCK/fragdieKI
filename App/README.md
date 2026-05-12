# Frag die KI iOS Frontend (IST-Stand)

Diese Struktur bildet eine einfache Push-to-Talk-App in SwiftUI für iOS 15 ab.

## Enthaltene Komponenten

- **Push-to-Talk Hauptscreen** mit Zustands-Icons und großem Button.
- **Branding** mit App-Name „Frag die KI“ und einfachem Emoji-Logo direkt im Hauptscreen.
- **Audioaufnahme** via `AVAudioRecorder` (M4A, 16 kHz, mono, max. 20 s) mit Mikrofon-Permission-Handling.
- **Backend-Anbindung** an `POST /api/v1/maxi/turn` mit multipart/form-data; der Request-Body wird als Datei-Upload gestreamt (kein komplettes In-Memory-Buffering).
- **Audioausgabe** via `AVAudioPlayer` auf Backend-TTS-Datei.
- **Foto-Vorlesen (OCR)** über Backend-Tesseract; Bilder werden ans Familien-Backend hochgeladen und dort lokal verarbeitet (keine Cloud-Calls zu OpenAI/Google).
- **Elternmodus** mit PIN-Gate und Einstellungen.
- **Sicherer PIN-Speicher** via iOS Keychain; alle anderen Einstellungen in `UserDefaults`.
- **Persistente Device-ID** via `UserDefaults`.
- **Verlauf** (letzte Turns) im Elternmodus inkl. Löschfunktion.
- **Tageslimit-Prüfung** beim Start der Aufnahme (basierend auf lokalem Verlauf und geschätzter Turn-Dauer).
- **Modus-Prüfung**: deaktivierte Modi werden vor Aufnahme blockiert.
- **Differenzierte Fehlermeldungen**: Netzwerk-/URLErrors werden von anderen Fehlern unterschieden; im Debug-Modus werden `localizedDescription`-Details angezeigt.
- **Offline-Fallback-Sprache**: Bei Netzwerk-/Backend-Fehlern wird eine lokale Retry-Ansage per `AVSpeechSynthesizer` abgespielt.
- **Exakte Turn-Dauer lokal**: Die tatsächliche Aufnahmedauer pro Turn wird im Verlauf gespeichert (statt pauschaler Schätzung).
- **iOS 15+ kompatibel**: keine iOS-16-only APIs (`NavigationStack`, `URL.appending(path:)` etc.).

## App-Zustände

`AppState`: idle, recording, uploading, thinking, speaking, error(String)

## Lokales Bauen

Siehe [`Docs/LOCAL_BUILD.md`](Docs/LOCAL_BUILD.md) für vollständige Anleitung.

Schnellstart (Simulator):
```bash
open App/FragDieKI.xcodeproj
# oder per Kommandozeile:
xcodebuild build -project App/FragDieKI.xcodeproj -scheme FragDieKI \
  -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' \
  CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO
```

## CI

GitHub Actions Workflow: `.github/workflows/ios-ci.yml`  
Läuft bei jedem Push/PR auf `main` → Debug-Build + Unit-Tests.
