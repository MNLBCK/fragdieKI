import AVFoundation
import Foundation

final class AudioRecorderService: NSObject, AVAudioRecorderDelegate {
    /// Called when recording ends due to the max-duration limit (not an explicit `stopRecording` call).
    var onRecordingFinishedBySystem: ((URL) -> Void)?

    private var recorder: AVAudioRecorder?
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
        newRecorder.prepareToRecord()
        newRecorder.record(forDuration: maxDuration)
        recorder = newRecorder
    }

    func stopRecording() throws -> URL {
        guard let recorder else {
            throw RecorderError.noActiveRecording
        }
        // Clear delegate so `audioRecorderDidFinishRecording` is not triggered for this explicit stop.
        recorder.delegate = nil
        recorder.stop()
        let outputURL = recorder.url
        self.recorder = nil
        return outputURL
    }

    // MARK: - AVAudioRecorderDelegate

    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        // Triggered automatically when `maxDuration` is reached.
        let outputURL = recorder.url
        self.recorder = nil
        if flag {
            onRecordingFinishedBySystem?(outputURL)
        }
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

