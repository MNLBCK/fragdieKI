# Frag die KI iOS Frontend (IST-Stand)

Diese Struktur bildet eine einfache Push-to-Talk-App in SwiftUI für iOS 15 ab.

## Enthaltene Komponenten

- **Push-to-Talk Hauptscreen** mit Zustands-Icons und großem Button.
- **Branding** mit App-Name „Frag die KI“ und einfachem Emoji-Logo direkt im Hauptscreen.
- **Audioaufnahme** via `AVAudioRecorder` (M4A, 16 kHz, mono, max. 20 s) mit Mikrofon-Permission-Handling.
- **Backend-Anbindung** an `POST /api/v1/maxi/turn` mit multipart/form-data; der Request-Body wird als Datei-Upload gestreamt (kein komplettes In-Memory-Buffering).
- **Audioausgabe** via `AVAudioPlayer` auf Backend-TTS-Datei.
- **Foto-Vorlesen (OCR) ausschließlich lokal** über Apple Vision; Bilder werden dafür nicht an das Backend hochgeladen.
- **Elternmodus** mit PIN-Gate und Einstellungen.
- **Sicherer PIN-Speicher** via iOS Keychain; alle anderen Einstellungen in `UserDefaults`.
- **Persistente Device-ID** via `UserDefaults`.
- **Verlauf** (letzte Turns) im Elternmodus inkl. Löschfunktion.
- **Tageslimit-Prüfung** beim Start der Aufnahme (basierend auf lokalem Verlauf und geschätzter Turn-Dauer).
- **Modus-Prüfung**: deaktivierte Modi werden vor Aufnahme blockiert.
- **Differenzierte Fehlermeldungen**: Netzwerk-/URLErrors werden von anderen Fehlern unterschieden; im Debug-Modus werden `localizedDescription`-Details angezeigt.
- **iOS 15+ kompatibel**: keine iOS-16-only APIs (`NavigationStack`, `URL.appending(path:)` etc.).

## App-Zustände

`AppState`: idle, recording, uploading, thinking, speaking, error(String)

## Offene Punkte (für produktiven Betrieb)

- Offline-Fallback-Audiodatei ist noch nicht eingebunden.
- Die Dauer pro Turn wird aktuell als Schätzwert gespeichert (bis zu 20s), nicht als exakte Messung.
- Kein fertiges Xcode-Projekt (`.xcodeproj`) enthalten; der Code ist als modulare Basisstruktur angelegt.
