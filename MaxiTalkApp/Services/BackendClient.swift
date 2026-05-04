import Foundation

final class BackendClient {
    private let session: URLSession
    private let clientVersion: String

    init(session: URLSession = .shared, clientVersion: String = "1.0.0") {
        self.session = session
        self.clientVersion = clientVersion
    }

    func sendTurn(
        audioURL: URL,
        sessionId: UUID,
        deviceId: UUID,
        mode: ConversationMode,
        serverBaseURL: URL
    ) async throws -> TurnResponse {
        let endpoint = serverBaseURL.appending(path: "/api/v1/maxi/turn")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = try createBody(
            audioURL: audioURL,
            boundary: boundary,
            sessionId: sessionId,
            deviceId: deviceId,
            mode: mode
        )

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw BackendError.invalidResponse
        }

        return try JSONDecoder().decode(TurnResponse.self, from: data)
    }

    func downloadAudio(audioPath: String, serverBaseURL: URL) async throws -> URL {
        let remoteURL = serverBaseURL.appending(path: audioPath)
        let (tempURL, response) = try await session.download(from: remoteURL)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw BackendError.invalidResponse
        }

        let localURL = FileManager.default.temporaryDirectory.appendingPathComponent("tts-\(UUID().uuidString).m4a")
        try? FileManager.default.removeItem(at: localURL)
        try FileManager.default.moveItem(at: tempURL, to: localURL)
        return localURL
    }

    private func createBody(
        audioURL: URL,
        boundary: String,
        sessionId: UUID,
        deviceId: UUID,
        mode: ConversationMode
    ) throws -> Data {
        var body = Data()

        func appendField(_ name: String, value: String) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }

        appendField("session_id", value: sessionId.uuidString)
        appendField("device_id", value: deviceId.uuidString)
        appendField("mode", value: mode.rawValue)
        appendField("client_version", value: clientVersion)

        let audioData = try Data(contentsOf: audioURL)
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"audio\"; filename=\"recording.m4a\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/m4a\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        return body
    }
}

enum BackendError: Error {
    case invalidResponse
}
