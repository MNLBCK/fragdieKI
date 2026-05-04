import SwiftUI

struct ParentalSettingsView: View {
    @ObservedObject var viewModel: AppStateViewModel
    @State private var draft: ParentalSettings

    init(viewModel: AppStateViewModel) {
        self.viewModel = viewModel
        _draft = State(initialValue: viewModel.settings)
    }

    var body: some View {
        Form {
            Section("Server") {
                TextField("Server-URL", text: $draft.serverBaseURL)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
            }

            Section("Tageslimit") {
                Stepper(value: $draft.dailyLimitSeconds, in: 60...7200, step: 60) {
                    Text("\(draft.dailyLimitSeconds / 60) Minuten")
                }
            }

            Section("Modi") {
                ForEach(ConversationMode.allCases) { mode in
                    Toggle(mode.rawValue.capitalized, isOn: Binding(
                        get: { draft.enabledModes.contains(mode) },
                        set: { enabled in
                            if enabled { draft.enabledModes.insert(mode) }
                            else { draft.enabledModes.remove(mode) }
                        }
                    ))
                }
            }

            Toggle("Debug-Anzeige", isOn: $draft.debugEnabled)

            Button("Speichern") { viewModel.saveSettings(draft) }
        }
    }
}
