import Foundation

struct TurnHistoryEntry: Codable, Identifiable {
    let id: UUID
    let createdAt: Date
    let mode: ConversationMode
    let transcript: String
    let safetyState: String
    let estimatedDurationSeconds: Int
}
