import AVFoundation
import Foundation

final class AudioPlaybackService: NSObject, AVAudioPlayerDelegate {
    private var player: AVAudioPlayer?
    var onPlaybackFinished: (() -> Void)?

    func play(url: URL) throws {
        try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio)
        try AVAudioSession.sharedInstance().setActive(true)

        player = try AVAudioPlayer(contentsOf: url)
        player?.delegate = self
        player?.prepareToPlay()
        player?.play()
    }

    func stop() {
        player?.stop()
        player = nil
        onPlaybackFinished?()
    }

    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        self.player = nil
        onPlaybackFinished?()
    }
}
