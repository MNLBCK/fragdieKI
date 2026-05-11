import Foundation
import UIKit

@MainActor
final class AppStateViewModel: ObservableObject {
    @Published private(set) var state: AppState = .idle
    @Published private(set) var micLevel: Float = 0
    @Published var currentMode: ConversationMode = .question
    @Published var isImagePickerPresented = false
    @Published var settings: ParentalSettings
    @Published private(set) var history: [TurnHistoryEntry]

    let sessionId: UUID
    let deviceId: UUID

    private let recorder = AudioRecorderService()
    private let backend = BackendClient()
    private let playback = AudioPlaybackService()
    private let readingPlayback = ReadingPlaybackService()
    private let minRecordingDurationSeconds = 0
    private let maxRecordingDurationSeconds = 20
    private var recordingStartedAt: Date?

    init(sessionId: UUID = UUID(), deviceId: UUID = SettingsStore.loadOrCreateDeviceID()) {
        self.sessionId = sessionId
        self.deviceId = deviceId
        self.settings = SettingsStore.load()
        self.history = HistoryStore.load()

        playback.onPlaybackFinished = { [weak self] in
            Task { @MainActor in
                self?.state = .idle
            }
        }
        readingPlayback.onFinished = { [weak self] in
            Task { @MainActor in
                self?.state = .idle
            }
        }
    }

    // Wire up after init so `self` is available.
    func configure() {
        recorder.onRecordingFinishedBySystem = { [weak self] audioURL in
            Task { @MainActor [weak self] in
                guard let self, case .recording = self.state else { return }
                self.handleAudioReady(audioURL)
            }
        }
        recorder.onLevelUpdate = { [weak self] level in
            Task { @MainActor [weak self] in
                self?.micLevel = level
            }
        }
    }

    func pressAndHoldStart() {
        guard case .idle = state else {
            if case .speaking = state {
                stopPlayback()
            }
            return
        }
        guard settings.enabledModes.contains(currentMode) else {
            state = .error("Modus deaktiviert")
            return
        }
        guard remainingDailySeconds > 0 else {
            state = .error("Tageslimit erreicht")
            return
        }

        Task {
            do {
                try await recorder.startRecording()
                recordingStartedAt = Date()
                state = .recording
            } catch RecorderError.permissionDenied {
                state = .error("Mikrofon-Zugriff verweigert")
            } catch {
                state = .error(settings.debugEnabled ? error.localizedDescription : "Aufnahme nicht möglich")
            }
        }
    }

    func releaseAndSend() {
        guard case .recording = state else { return }

        let audioURL: URL
        do {
            audioURL = try recorder.stopRecording()
        } catch {
            state = .error(settings.debugEnabled ? error.localizedDescription : "Aufnahme fehlerhaft")
            return
        }

        handleAudioReady(audioURL)
    }

    func stopPlayback() {
        playback.stop()
        readingPlayback.stop()
        micLevel = 0
        state = .idle
    }

    func saveSettings(_ newSettings: ParentalSettings) {
        settings = newSettings
        SettingsStore.save(newSettings)
    }

    func clearHistory() {
        history = []
        HistoryStore.clear()
    }

    var remainingDailySeconds: Int {
        max(0, settings.dailyLimitSeconds - usedTodaySeconds)
    }

    func startPhotoReading() {
        guard settings.photoReadingEnabled else {
            state = .error("Foto-Vorlesen ist deaktiviert")
            return
        }
        guard case .idle = state else { return }
        isImagePickerPresented = true
    }

    func processPickedImage(_ image: UIImage?) {
        guard let image else { return }
        guard let baseURL = URL(string: settings.serverBaseURL) else {
            state = .error("Server-URL ungültig")
            return
        }

        state = .uploading

        let deviceId = self.deviceId
        let backend = self.backend
        let readingPlayback = self.readingPlayback
        let debugEnabled = self.settings.debugEnabled

        Task.detached { [weak self] in
            do {
                // Save image to temporary file
                let imageURL = try Self.saveImageToTempFile(image)
                defer { try? FileManager.default.removeItem(at: imageURL) }

                // Upload to backend for OCR
                await MainActor.run { self?.state = .thinking }
                let text = try await backend.extractTextFromImage(
                    imageURL: imageURL,
                    deviceId: deviceId,
                    serverBaseURL: baseURL
                )

                // Speak the extracted text
                await MainActor.run {
                    self?.state = .speaking
                    try? readingPlayback.speak(text)
                }
            } catch BackendError.noTextFound {
                await MainActor.run {
                    self?.state = .error("Ich konnte keinen lesbaren Text erkennen")
                }
            } catch let urlError as URLError {
                await MainActor.run {
                    self?.playOfflineFallbackSpeech(debugText: urlError.localizedDescription, debugEnabled: debugEnabled)
                }
            } catch {
                await MainActor.run {
                    self?.state = .error(debugEnabled ? error.localizedDescription : "Foto konnte nicht verarbeitet werden")
                }
            }
        }
    }

    private static func saveImageToTempFile(_ image: UIImage) throws -> URL {
        guard let jpegData = image.jpegData(compressionQuality: 0.8) else {
            throw NSError(domain: "AppStateViewModel", code: 1, userInfo: [NSLocalizedDescriptionKey: "Could not convert image to JPEG"])
        }
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent("photo-\(UUID().uuidString).jpg")
        try jpegData.write(to: tempURL)
        return tempURL
    }

    // MARK: - Private

    /// Shared upload + playback flow triggered either by an explicit button release or
    /// by the recorder reaching its maximum duration.
    private func handleAudioReady(_ audioURL: URL) {
        guard let baseURL = URL(string: settings.serverBaseURL) else {
            state = .error("Server-URL ungültig")
            return
        }

        micLevel = 0
        state = .uploading
        let recordingDurationSeconds = measuredRecordingDurationSeconds()

        // Capture value-typed state needed off the MainActor.
        let sessionId = self.sessionId
        let deviceId = self.deviceId
        let mode = self.currentMode
        let debugEnabled = self.settings.debugEnabled
        let backend = self.backend
        let playback = self.playback

        Task.detached { [weak self] in
            do {
                let response = try await backend.sendTurn(
                    audioURL: audioURL,
                    sessionId: sessionId,
                    deviceId: deviceId,
                    mode: mode,
                    serverBaseURL: baseURL
                )
                await MainActor.run { self?.state = .thinking }
                let ttsURL = try await backend.downloadAudio(audioPath: response.audioURL, serverBaseURL: baseURL)
                await MainActor.run {
                    self?.appendHistory(response, recordingDurationSeconds: recordingDurationSeconds)
                    self?.state = .speaking
                    try? playback.play(url: ttsURL)
                }
            } catch let urlError as URLError {
                await MainActor.run {
                    self?.playOfflineFallbackSpeech(debugText: urlError.localizedDescription, debugEnabled: debugEnabled)
                }
            } catch {
                await MainActor.run {
                    self?.playOfflineFallbackSpeech(debugText: error.localizedDescription, debugEnabled: debugEnabled)
                }
            }
        }
    }

    private func playOfflineFallbackSpeech(debugText: String, debugEnabled: Bool) {
        let fallbackText = "Ich habe gerade keine Verbindung. Bitte versuch es gleich noch einmal."
        state = .speaking
        do {
            try readingPlayback.speak(fallbackText)
        } catch {
            state = .error(debugEnabled ? debugText : "Keine Verbindung")
        }
    }

    private func appendHistory(_ response: TurnResponse, recordingDurationSeconds: Int) {
        let entry = TurnHistoryEntry(
            id: UUID(),
            createdAt: Date(),
            mode: currentMode,
            transcript: response.transcript,
            safetyState: response.safetyState,
            estimatedDurationSeconds: recordingDurationSeconds
        )
        history.insert(entry, at: 0)
        HistoryStore.save(history)
    }

    private func measuredRecordingDurationSeconds() -> Int {
        guard let startedAt = recordingStartedAt else {
            NSLog("AppStateViewModel: missing recordingStartedAt while measuring duration")
            return 0
        }
        let elapsed = Date().timeIntervalSince(startedAt)
        let clampedDurationSeconds = min(maxRecordingDurationSeconds, max(minRecordingDurationSeconds, Int(elapsed.rounded())))
        recordingStartedAt = nil
        return clampedDurationSeconds
    }

    private var usedTodaySeconds: Int {
        let calendar = Calendar.current
        return history
            .filter { calendar.isDateInToday($0.createdAt) }
            .map(\.estimatedDurationSeconds)
            .reduce(0, +)
    }
}
