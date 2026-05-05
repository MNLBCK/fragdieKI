# Frag die KI iOS Frontend (IST-Stand)

Diese Struktur bildet eine einfache Push-to-Talk-App in SwiftUI für iOS 15 ab.

## Enthaltene Komponenten

- **Push-to-Talk Hauptscreen** mit Zustands-Icons und großem Button.
- **Branding** mit App-Name „Frag die KI“ und einfachem Emoji-Logo direkt im Hauptscreen.
- **Audioaufnahme** via `AVAudioRecorder` (M4A, 16 kHz, mono, max. 20 s).
- **Backend-Anbindung** an `POST /api/v1/maxi/turn` mit multipart/form-data.
- **Audioausgabe** via `AVAudioPlayer` auf Backend-TTS-Datei.
- **Elternmodus** mit PIN-Gate und Einstellungen.
- **Lokale Settings-Persistenz** via `UserDefaults`.
- **Persistente Device-ID** via `UserDefaults`.
- **Verlauf** (letzte Turns) im Elternmodus inkl. Löschfunktion.

## App-Zustände

`AppState`: idle, recording, uploading, thinking, speaking, error(String)

## Offene Punkte (für produktiven Betrieb)

- Tageslimit aktuell nur konfigurierbar, noch nicht hart erzwungen.
- Offline-Fallback-Audiodatei ist noch nicht eingebunden.
- Kein fertiges Xcode-Projekt (`.xcodeproj`) enthalten; der Code ist als modulare Basisstruktur angelegt.
