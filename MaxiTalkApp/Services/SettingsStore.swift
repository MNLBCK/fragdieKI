import Foundation

enum SettingsStore {
    private static let key = "maxi.parental.settings"

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
}
