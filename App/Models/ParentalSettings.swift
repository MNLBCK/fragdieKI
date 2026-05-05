import Foundation

struct ParentalSettings: Codable {
    var serverBaseURL: String
    var dailyLimitSeconds: Int
    var enabledModes: Set<ConversationMode>
    var debugEnabled: Bool
    var pinCode: String

    static let `default` = ParentalSettings(
        serverBaseURL: "http://openclaw.local:8080",
        dailyLimitSeconds: 15 * 60,
        enabledModes: Set(ConversationMode.allCases),
        debugEnabled: false,
        pinCode: "1234"
    )
}
