import SwiftUI

struct MainView: View {
    @StateObject private var viewModel = AppStateViewModel()
    @State private var showParentalGate = false

    var body: some View {
        VStack(spacing: 24) {
            Text("🦒")
                .font(.system(size: 72))

            statusIcon
                .font(.system(size: 48))
                .foregroundStyle(statusColor)

            Circle()
                .fill(buttonColor)
                .frame(width: 220, height: 220)
                .overlay(Image(systemName: buttonSymbol).font(.system(size: 56)).foregroundStyle(.white))
                .scaleEffect(viewModel.state == .recording ? 1.08 : 1.0)
                .animation(.easeInOut(duration: 0.7).repeatForever(autoreverses: true), value: viewModel.state == .recording)
                .simultaneousGesture(
                    DragGesture(minimumDistance: 0)
                        .onChanged { _ in viewModel.pressAndHoldStart() }
                        .onEnded { _ in viewModel.releaseAndSend() }
                )

            Text("Halten und sprechen")
                .font(.title3)

            Image(systemName: "gear")
                .onLongPressGesture(minimumDuration: 1.5) {
                    showParentalGate = true
                }
        }
        .padding()
        .sheet(isPresented: $showParentalGate) {
            ParentalGateView(viewModel: viewModel)
        }
    }

    private var statusIcon: Image {
        switch viewModel.state {
        case .idle: return Image(systemName: "mic.fill")
        case .recording: return Image(systemName: "waveform")
        case .uploading, .thinking: return Image(systemName: "ellipsis.bubble")
        case .speaking: return Image(systemName: "speaker.wave.3.fill")
        case .error: return Image(systemName: "icloud.slash")
        }
    }

    private var statusColor: Color {
        if case .error = viewModel.state { return .red }
        if viewModel.state == .recording { return .red }
        return .primary
    }

    private var buttonColor: Color {
        viewModel.state == .recording ? .red : .blue
    }

    private var buttonSymbol: String {
        if viewModel.state == .speaking { return "stop.fill" }
        return "mic.fill"
    }
}
