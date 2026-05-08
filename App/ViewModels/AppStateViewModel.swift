import Foundation

@MainActor
final class AppStateViewModel: ObservableObject {
    @Published private(set) var state: AppState = .idle
    @Published private(set) var micLevel: Float = 0
    @Published var currentMode: ConversationMode = .question
    @Published var settings: ParentalSettings
    @Published private(set) var history: [TurnHistoryEntry]

    let sessionId: UUID
    let deviceId: UUID

    private let recorder = AudioRecorderService()
    private let backend = BackendClient()
    private let playback = AudioPlaybackService()

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
                    self?.appendHistory(response)
                    self?.state = .speaking
                    try? playback.play(url: ttsURL)
                }
            } catch let urlError as URLError {
                await MainActor.run {
                    self?.state = .error(debugEnabled ? urlError.localizedDescription : "Keine Verbindung")
                }
            } catch {
                await MainActor.run {
                    self?.state = .error(debugEnabled ? error.localizedDescription : "Fehler aufgetreten")
                }
            }
        }
    }

    private func appendHistory(_ response: TurnResponse) {
        let estimatedDurationSeconds = min(20, remainingDailySeconds == 0 ? 20 : remainingDailySeconds)
        let entry = TurnHistoryEntry(
            id: UUID(),
            createdAt: Date(),
            mode: currentMode,
            transcript: response.transcript,
            safetyState: response.safetyState,
            estimatedDurationSeconds: estimatedDurationSeconds
        )
        history.insert(entry, at: 0)
        HistoryStore.save(history)
    }

    private var usedTodaySeconds: Int {
        let calendar = Calendar.current
        return history
            .filter { calendar.isDateInToday($0.createdAt) }
            .map(\.estimatedDurationSeconds)
            .reduce(0, +)
    }
}

