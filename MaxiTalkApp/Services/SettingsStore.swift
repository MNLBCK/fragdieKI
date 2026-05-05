import Foundation

enum SettingsStore {
    private static let key = "fragdieki.parental.settings"
    private static let deviceKey = "fragdieki.device.id"

    static func load() -> ParentalSettings {
        guard
            let data = UserDefaults.standard.data(forKey: key),
            let decoded = try? JSONDecoder().decode(ParentalSettings.self, from: data)
        else {
            return .default
        }
        return decoded
    }

    static func save(_ settings: ParentalSettings) {
        guard let data = try? JSONEncoder().encode(settings) else { return }
        UserDefaults.standard.set(data, forKey: key)
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
