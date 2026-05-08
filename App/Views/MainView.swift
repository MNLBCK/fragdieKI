import SwiftUI
import UIKit

struct MainView: View {
    @StateObject private var viewModel = AppStateViewModel()
    @State private var showParentalGate = false
    @State private var pickedImage: UIImage?

    var body: some View {
        VStack(spacing: 24) {
            VStack(spacing: 8) {
                Text("🧠✨")
                    .font(.system(size: 56))
                Text("Frag die KI")
                    .font(.title2.bold())
            }

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

            if viewModel.state == .recording {
                VStack(spacing: 8) {
                    HStack(spacing: 6) {
                        ForEach(0..<12, id: \.self) { index in
                            Capsule()
                                .fill(.red)
                                .frame(width: 6, height: barHeight(for: index))
                        }
                    }
                    .frame(height: 40)

                    Text("Ich höre zu …")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.red)
                }
            }

            Text("Halten und sprechen")
                .font(.title3)


            Button {
                viewModel.startPhotoReading()
            } label: {
                Label("Foto vorlesen", systemImage: "text.viewfinder")
                    .font(.headline)
                    .padding(.horizontal, 18)
                    .padding(.vertical, 10)
                    .background(viewModel.settings.photoReadingEnabled ? Color.orange.opacity(0.2) : Color.gray.opacity(0.2))
                    .clipShape(Capsule())
            }
            .disabled(!viewModel.settings.photoReadingEnabled || viewModel.state != .idle)

            Image(systemName: "gear")
                .accessibilityLabel("Elternmodus")
                .accessibilityHint("Gedrückt halten für Elternmodus")
                .accessibilityAddTraits(.isButton)
                .onLongPressGesture(minimumDuration: 1.5) {
                    showParentalGate = true
                }
        }
        .padding()
        .onAppear { viewModel.configure() }
        .sheet(isPresented: $showParentalGate) {
            ParentalGateView(viewModel: viewModel)
        }
        .sheet(isPresented: $viewModel.isImagePickerPresented) {
            ImagePickerView(selectedImage: $pickedImage, isPresented: $viewModel.isImagePickerPresented)
        }
        .onChange(of: pickedImage) { image in
            viewModel.processPickedImage(image)
            pickedImage = nil
        }
    }



    private func barHeight(for index: Int) -> CGFloat {
        let minHeight: CGFloat = 8
        let maxHeight: CGFloat = 40
        let noiseFloor = 0.12
        let level = max(0, CGFloat(viewModel.micLevel) - noiseFloor) / (1 - noiseFloor)
        let phase = Double(index) * 0.55
        let wave = (sin(Date().timeIntervalSinceReferenceDate * 8 + phase) + 1) / 2
        let dynamic = CGFloat(wave) * level
        return minHeight + (maxHeight - minHeight) * dynamic
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
