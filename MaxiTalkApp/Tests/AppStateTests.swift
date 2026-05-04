import XCTest
@testable import MaxiTalkApp

final class AppStateTests: XCTestCase {
    func testConversationModeRawValues() {
        XCTAssertEqual(ConversationMode.question.rawValue, "question")
        XCTAssertTrue(ConversationMode.allCases.contains(.dino))
    }
}
