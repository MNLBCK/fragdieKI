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
        let endpoint = url(for: "/api/v1/maxi/turn", relativeTo: serverBaseURL)
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        // Write multipart body to a temp file so URLSession can stream it from disk.
        let bodyFileURL = try createBodyFile(
            audioURL: audioURL,
            boundary: boundary,
            sessionId: sessionId,
            deviceId: deviceId,
            mode: mode
        )
        defer { try? FileManager.default.removeItem(at: bodyFileURL) }

        let (data, response) = try await session.upload(for: request, fromFile: bodyFileURL)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw BackendError.invalidResponse
        }

        return try JSONDecoder().decode(TurnResponse.self, from: data)
    }

    func downloadAudio(audioPath: String, serverBaseURL: URL) async throws -> URL {
        let remoteURL = url(for: audioPath, relativeTo: serverBaseURL)
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

    // MARK: - Helpers

    /// Constructs a URL by replacing the path component of `base` with `path`.
    /// Compatible with iOS 15 (avoids `URL.appending(path:)` which requires iOS 16).
    /// Query parameters in `base` are intentionally stripped; API endpoints don't
    /// carry pass-through query strings from the server base URL.
    private func url(for path: String, relativeTo base: URL) -> URL {
        var components = URLComponents(url: base, resolvingAgainstBaseURL: false) ?? URLComponents()
        components.path = path.hasPrefix("/") ? path : "/" + path
        components.query = nil
        return components.url ?? base.appendingPathComponent(path)
    }

    private func createBodyFile(
        audioURL: URL,
        boundary: String,
        sessionId: UUID,
        deviceId: UUID,
        mode: ConversationMode
    ) throws -> URL {
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

        let fileURL = FileManager.default.temporaryDirectory.appendingPathComponent("multipart-\(UUID().uuidString).bin")
        try body.write(to: fileURL)
        return fileURL
    }
}

enum BackendError: Error {
    case invalidResponse
}

