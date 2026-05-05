import Foundation

enum AppState: Equatable {
    case idle
    case recording
    case uploading
    case thinking
    case speaking
    case error(String)
}

enum ConversationMode: String, Codable, CaseIterable, Identifiable {
    case question
    case story
    case explain
    case football
    case dino

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .question: return "questionmark.bubble"
        case .story: return "book"
        case .explain: return "lightbulb"
        case .football: return "sportscourt"
        case .dino: return "tortoise"
        }
    }
}
