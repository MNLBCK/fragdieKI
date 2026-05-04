import Foundation

@MainActor
final class AppStateViewModel: ObservableObject {
    @Published private(set) var state: AppState = .idle
    @Published var currentMode: ConversationMode = .question
    @Published var settings: ParentalSettings

    let sessionId: UUID
    let deviceId: UUID

    private let recorder = AudioRecorderService()
    private let backend = BackendClient()
    private let playback = AudioPlaybackService()

    init(sessionId: UUID = UUID(), deviceId: UUID = UUID()) {
        self.sessionId = sessionId
        self.deviceId = deviceId
        self.settings = SettingsStore.load()

        playback.onPlaybackFinished = { [weak self] in
            Task { @MainActor in
                self?.state = .idle
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

        do {
            try recorder.startRecording()
            state = .recording
        } catch {
            state = .error("Aufnahme nicht möglich")
        }
    }

    func releaseAndSend() {
        guard case .recording = state else { return }

        Task {
            do {
                state = .uploading
                let audioURL = try recorder.stopRecording()
                state = .thinking
                let baseURL = try validatedServerURL()
                let response = try await backend.sendTurn(
                    audioURL: audioURL,
                    sessionId: sessionId,
                    deviceId: deviceId,
                    mode: currentMode,
                    serverBaseURL: baseURL
                )
                let ttsURL = try await backend.downloadAudio(audioPath: response.audioURL, serverBaseURL: baseURL)
                state = .speaking
                try playback.play(url: ttsURL)
            } catch {
                state = .error("Keine Verbindung")
            }
        }
    }

    func stopPlayback() {
        playback.stop()
        state = .idle
    }

    func saveSettings(_ newSettings: ParentalSettings) {
        settings = newSettings
        SettingsStore.save(newSettings)
    }

    private func validatedServerURL() throws -> URL {
        guard let url = URL(string: settings.serverBaseURL) else {
            throw URLError(.badURL)
        }
        return url
    }
}
