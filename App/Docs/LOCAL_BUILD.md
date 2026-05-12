# Lokales Bauen – Frag die KI (iOS)

## Voraussetzungen

| Tool | Mindestversion | Bezug |
|------|----------------|-------|
| macOS | 13 Ventura | – |
| Xcode | 15.0 | Mac App Store / [developer.apple.com](https://developer.apple.com/xcode/) |
| iOS Simulator | wird mit Xcode installiert | – |

> **Hinweis:** Das Projekt benötigt **keinen** Apple-Entwickler-Account für reine Simulator-Builds.

---

## Projekt öffnen

```bash
open App/FragDieKI.xcodeproj
```

Alternativ in Xcode über **File → Open** navigieren und `App/FragDieKI.xcodeproj` auswählen.

---

## Debug-Build (Kommandozeile)

```bash
xcodebuild build \
  -project App/FragDieKI.xcodeproj \
  -scheme FragDieKI \
  -configuration Debug \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' \
  CODE_SIGN_IDENTITY="" \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGNING_ALLOWED=NO
```

---

## Unit-Tests ausführen

```bash
xcodebuild test \
  -project App/FragDieKI.xcodeproj \
  -scheme FragDieKI \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' \
  CODE_SIGN_IDENTITY="" \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGNING_ALLOWED=NO
```

In Xcode reicht ⌘U (Scheme: **FragDieKI**).

---

## Auf echtem Gerät bauen

1. Ein Apple-Entwickler-Account in Xcode-Einstellungen hinzufügen (**Xcode → Settings → Accounts**).
2. Ziel auf das verbundene iPhone umstellen.
3. Signierungsteam unter **Signing & Capabilities** auswählen.
4. ▶ drücken.

---

## Projektstruktur

```
App/
├── FragDieKI.xcodeproj/   ← Xcode-Projekt
├── App/                   ← @main App-Einstiegspunkt
├── Components/            ← wiederverwendbare UI-Komponenten
├── Models/                ← Datenmodelle
├── Parental/              ← Elternmodus-Views
├── Services/              ← Audio, Backend, Keychain, …
├── ViewModels/            ← AppStateViewModel
├── Views/                 ← MainView
└── Tests/                 ← Unit-Tests (XCTest)
```

---

## CI

Der Workflow `.github/workflows/ios-ci.yml` läuft automatisch bei jedem Push/PR auf `main` und führt folgende Schritte aus:

1. **Build** – Debug-Build gegen den iOS Simulator
2. **Test** – Unit-Tests (`FragDieKITests`)

Ergebnis wird als ✅ / ❌ direkt am Commit / PR angezeigt.
