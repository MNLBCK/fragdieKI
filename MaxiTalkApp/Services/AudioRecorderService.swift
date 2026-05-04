import AVFoundation
import Foundation

final class AudioRecorderService: NSObject {
    private var recorder: AVAudioRecorder?
    private let maxDuration: TimeInterval = 20

    func startRecording() throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord, mode: .spokenAudio, options: [.defaultToSpeaker])
        try session.setActive(true)

        let outputURL = temporaryOutputURL()
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatMPEG4AAC,
            AVSampleRateKey: 16_000,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        recorder = try AVAudioRecorder(url: outputURL, settings: settings)
        recorder?.prepareToRecord()
        recorder?.record(forDuration: maxDuration)
    }

    func stopRecording() throws -> URL {
        guard let recorder else {
            throw RecorderError.noActiveRecording
        }

        recorder.stop()
        let outputURL = recorder.url
        self.recorder = nil
        return outputURL
    }

    private func temporaryOutputURL() -> URL {
        let fileName = "maxi-\(UUID().uuidString).m4a"
        return FileManager.default.temporaryDirectory.appendingPathComponent(fileName)
    }
}

enum RecorderError: Error {
    case noActiveRecording
}
