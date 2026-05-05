import Foundation

enum HistoryStore {
    private static let key = "fragdieki.turn.history"

    static func load() -> [TurnHistoryEntry] {
        guard
            let data = UserDefaults.standard.data(forKey: key),
            let decoded = try? JSONDecoder().decode([TurnHistoryEntry].self, from: data)
        else {
            return []
        }
        return decoded
    }

    static func save(_ entries: [TurnHistoryEntry]) {
        guard let data = try? JSONEncoder().encode(entries) else { return }
        UserDefaults.standard.set(data, forKey: key)
    }

    static func clear() {
        UserDefaults.standard.removeObject(forKey: key)
    }
}
