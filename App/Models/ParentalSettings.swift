import Foundation

struct ParentalSettings: Codable {
    var serverBaseURL: String
    var dailyLimitSeconds: Int
    var enabledModes: Set<ConversationMode>
    var debugEnabled: Bool
    /// Not persisted to UserDefaults; managed via Keychain by `SettingsStore`.
    var pinCode: String

    static let `default` = ParentalSettings(
        serverBaseURL: "http://openclaw.local:8080",
        dailyLimitSeconds: 15 * 60,
        enabledModes: Set(ConversationMode.allCases),
        debugEnabled: false,
        pinCode: "1234"
    )

    // Explicit memberwise init so external callers can create instances normally.
    init(serverBaseURL: String, dailyLimitSeconds: Int, enabledModes: Set<ConversationMode>, debugEnabled: Bool, pinCode: String) {
        self.serverBaseURL = serverBaseURL
        self.dailyLimitSeconds = dailyLimitSeconds
        self.enabledModes = enabledModes
        self.debugEnabled = debugEnabled
        self.pinCode = pinCode
    }

    // Custom CodingKeys that intentionally exclude `pinCode`.
    enum CodingKeys: String, CodingKey {
        case serverBaseURL, dailyLimitSeconds, enabledModes, debugEnabled
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        serverBaseURL = try container.decode(String.self, forKey: .serverBaseURL)
        dailyLimitSeconds = try container.decode(Int.self, forKey: .dailyLimitSeconds)
        enabledModes = try container.decode(Set<ConversationMode>.self, forKey: .enabledModes)
        debugEnabled = try container.decode(Bool.self, forKey: .debugEnabled)
        // pinCode is populated from Keychain by SettingsStore, not from encoded data.
        pinCode = ""
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(serverBaseURL, forKey: .serverBaseURL)
        try container.encode(dailyLimitSeconds, forKey: .dailyLimitSeconds)
        try container.encode(enabledModes, forKey: .enabledModes)
        try container.encode(debugEnabled, forKey: .debugEnabled)
        // pinCode is intentionally NOT encoded here; it is stored in Keychain.
    }
}

