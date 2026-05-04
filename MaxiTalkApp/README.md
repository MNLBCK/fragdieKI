# MaxiTalk iOS Frontend (IST-Stand)

Diese Struktur bildet eine einfache Push-to-Talk-App in SwiftUI für iOS 15 ab.

## Enthaltene Komponenten

- **Push-to-Talk Hauptscreen** mit Zustands-Icons und großem Button.
- **Audioaufnahme** via `AVAudioRecorder` (M4A, 16 kHz, mono, max. 20 s).
- **Backend-Anbindung** an `POST /api/v1/maxi/turn` mit multipart/form-data.
- **Audioausgabe** via `AVAudioPlayer` auf Backend-TTS-Datei.
- **Elternmodus** mit PIN-Gate und Einstellungen.
- **Lokale Settings-Persistenz** via `UserDefaults`.

## App-Zustände

`AppState`: idle, recording, uploading, thinking, speaking, error(String)

## Offene Punkte (für produktiven Betrieb)

- Tageslimit aktuell nur konfigurierbar, noch nicht hart erzwungen.
- Verlaufsliste/Verlauf löschen sind noch nicht implementiert.
- Offline-Fallback-Audiodatei ist noch nicht eingebunden.
- Device-ID wird pro App-Lauf erzeugt und sollte dauerhaft im Keychain/UserDefaults gespeichert werden.
- Kein fertiges Xcode-Projekt (`.xcodeproj`) enthalten; der Code ist als modulare Basisstruktur angelegt.
