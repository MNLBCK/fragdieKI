import Foundation

enum SettingsStore {
    private static let key = "fragdieki.parental.settings"
    private static let deviceKey = "fragdieki.device.id"
    private static let pinKeychainAccount = "parental-pin"

    static func load() -> ParentalSettings {
        var settings: ParentalSettings
        if let data = UserDefaults.standard.data(forKey: key),
           let decoded = try? JSONDecoder().decode(ParentalSettings.self, from: data) {
            settings = decoded
        } else {
            settings = .default
        }
        // Load PIN from Keychain (falls back to default "1234" on first run).
        settings.pinCode = KeychainHelper.load(account: pinKeychainAccount) ?? "1234"
        return settings
    }

    static func save(_ settings: ParentalSettings) {
        // Persist all fields except pinCode to UserDefaults.
        if let data = try? JSONEncoder().encode(settings) {
            UserDefaults.standard.set(data, forKey: key)
        }
        // Persist PIN separately in Keychain.
        KeychainHelper.save(settings.pinCode, account: pinKeychainAccount)
    }

    static func loadOrCreateDeviceID() -> UUID {
        if let raw = UserDefaults.standard.string(forKey: deviceKey), let id = UUID(uuidString: raw) {
            return id
        }
        let id = UUID()
        UserDefaults.standard.set(id.uuidString, forKey: deviceKey)
        return id
    }
}

