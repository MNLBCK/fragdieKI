import SwiftUI

struct ParentalGateView: View {
    @ObservedObject var viewModel: AppStateViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var pinInput = ""
    @State private var unlocked = false

    var body: some View {
        NavigationView {
            Group {
                if unlocked {
                    ParentalSettingsView(viewModel: viewModel)
                } else {
                    VStack(spacing: 16) {
                        SecureField("PIN", text: $pinInput)
                            .keyboardType(.numberPad)
                            .textFieldStyle(.roundedBorder)
                        Button("Öffnen") {
                            unlocked = pinInput == viewModel.settings.pinCode
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("Elternmodus")
            .toolbar { ToolbarItem(placement: .navigationBarTrailing) { Button("Schließen") { dismiss() } } }
        }
    }
}
