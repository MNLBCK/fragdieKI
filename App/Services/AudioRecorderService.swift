import AVFoundation
import Foundation

final class AudioRecorderService: NSObject, AVAudioRecorderDelegate {
    /// Called when recording ends due to the max-duration limit (not an explicit `stopRecording` call).
    var onRecordingFinishedBySystem: ((URL) -> Void)?
    /// Live normalized level 0...1 while recording.
    var onLevelUpdate: ((Float) -> Void)?

    private var recorder: AVAudioRecorder?
    private var meterTimer: Timer?
    private let maxDuration: TimeInterval = 20

    func startRecording() async throws {
        let avSession = AVAudioSession.sharedInstance()

        // Request microphone permission if not yet determined.
        let permission = avSession.recordPermission
        if permission == .undetermined {
            let granted = await withCheckedContinuation { continuation in
                avSession.requestRecordPermission { continuation.resume(returning: $0) }
            }
            guard granted else { throw RecorderError.permissionDenied }
        } else if permission == .denied {
            throw RecorderError.permissionDenied
        }

        try avSession.setCategory(.playAndRecord, mode: .spokenAudio, options: [.defaultToSpeaker])
        try avSession.setActive(true)

        let outputURL = temporaryOutputURL()
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatMPEG4AAC,
            AVSampleRateKey: 16_000,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        let newRecorder = try AVAudioRecorder(url: outputURL, settings: settings)
        newRecorder.delegate = self
        newRecorder.isMeteringEnabled = true
        newRecorder.prepareToRecord()
        newRecorder.record(forDuration: maxDuration)
        recorder = newRecorder
        startMetering()
    }

    func stopRecording() throws -> URL {
        guard let recorder else {
            throw RecorderError.noActiveRecording
        }
        // Clear delegate so `audioRecorderDidFinishRecording` is not triggered for this explicit stop.
        recorder.delegate = nil
        recorder.stop()
        stopMetering()
        let outputURL = recorder.url
        self.recorder = nil
        return outputURL
    }

    // MARK: - AVAudioRecorderDelegate

    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        // Triggered automatically when `maxDuration` is reached.
        stopMetering()
        let outputURL = recorder.url
        self.recorder = nil
        if flag {
            onRecordingFinishedBySystem?(outputURL)
        }
    }


    private func startMetering() {
        stopMetering()
        let timer = Timer(timeInterval: 0.08, repeats: true) { [weak self] _ in
            guard let self, let recorder = self.recorder else { return }
            recorder.updateMeters()
            let averagePower = recorder.averagePower(forChannel: 0)
            // averagePower is typically in -160...0 dB. Normalize and floor for stable UI.
            let normalized = max(0.0, min(1.0, (averagePower + 60.0) / 60.0))
            self.onLevelUpdate?(normalized)
        }
        RunLoop.main.add(timer, forMode: .common)
        meterTimer = timer
    }

    private func stopMetering() {
        meterTimer?.invalidate()
        meterTimer = nil
        onLevelUpdate?(0)
    }

    private func temporaryOutputURL() -> URL {
        let fileName = "fragdieki-\(UUID().uuidString).m4a"
        return FileManager.default.temporaryDirectory.appendingPathComponent(fileName)
    }
}

enum RecorderError: Error {
    case noActiveRecording
    case permissionDenied
}
