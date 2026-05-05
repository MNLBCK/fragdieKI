import Foundation

struct TurnResponse: Codable {
    let turnId: String
    let transcript: String
    let answerText: String
    let audioURL: String
    let safetyState: String

    enum CodingKeys: String, CodingKey {
        case turnId = "turn_id"
        case transcript
        case answerText = "answer_text"
        case audioURL = "audio_url"
        case safetyState = "safety_state"
    }
}
