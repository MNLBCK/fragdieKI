import AVFoundation
import Foundation

final class ReadingPlaybackService: NSObject, AVSpeechSynthesizerDelegate {
    private let synthesizer = AVSpeechSynthesizer()
    var onFinished: (() -> Void)?

    override init() {
        super.init()
        synthesizer.delegate = self
    }

    func speak(_ text: String) throws {
        try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio)
        try AVAudioSession.sharedInstance().setActive(true)

        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "de-DE")
        utterance.rate = 0.48
        utterance.pitchMultiplier = 1.02
        synthesizer.speak(utterance)
    }

    func stop() {
        synthesizer.stopSpeaking(at: .immediate)
        onFinished?()
    }

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        onFinished?()
    }
}
