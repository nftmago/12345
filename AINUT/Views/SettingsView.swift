import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var notificationsEnabled = true
    @State private var hapticFeedbackEnabled = true
    @State private var darkModeEnabled = false
    @State private var showingDeleteAccountAlert = false
    @State private var showingLogoutAlert = false
    
    var body: some View {
        NavigationView {
            List {
                // User Section
                Section {
                    HStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [.green, .green.opacity(0.7)],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 50, height: 50)
                            .overlay(
                                Text(networkManager.currentUser?.username.prefix(1).uppercased() ?? "U")
                                    .font(.title2)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                            )
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text(networkManager.currentUser?.username.capitalized ?? "User")
                                .font(.headline)
                                .foregroundColor(.primary)
                            
                            Text(networkManager.currentUser?.email ?? "")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                    }
                    .padding(.vertical, 8)
                }
                
                // App Settings
                Section("App Settings") {
                    SettingsToggleRow(
                        icon: "bell.fill",
                        title: "Push Notifications",
                        isOn: $notificationsEnabled,
                        color: .orange
                    )
                    
                    SettingsToggleRow(
                        icon: "iphone.radiowaves.left.and.right",
                        title: "Haptic Feedback",
                        isOn: $hapticFeedbackEnabled,
                        color: .blue
                    )
                    
                    SettingsToggleRow(
                        icon: "moon.fill",
                        title: "Dark Mode",
                        isOn: $darkModeEnabled,
                        color: .purple
                    )
                }
                
                // Data & Privacy
                Section("Data & Privacy") {
                    SettingsNavigationRow(
                        icon: "doc.text.fill",
                        title: "Privacy Policy",
                        color: .green
                    ) {
                        // Handle privacy policy
                    }
                    
                    SettingsNavigationRow(
                        icon: "doc.plaintext.fill",
                        title: "Terms of Service",
                        color: .blue
                    ) {
                        // Handle terms of service
                    }
                    
                    SettingsNavigationRow(
                        icon: "arrow.down.circle.fill",
                        title: "Export Data",
                        color: .orange
                    ) {
                        // Handle data export
                    }
                }
                
                // Support
                Section("Support") {
                    SettingsNavigationRow(
                        icon: "questionmark.circle.fill",
                        title: "Help Center",
                        color: .blue
                    ) {
                        // Handle help center
                    }
                    
                    SettingsNavigationRow(
                        icon: "envelope.fill",
                        title: "Contact Support",
                        color: .green
                    ) {
                        // Handle contact support
                    }
                    
                    SettingsNavigationRow(
                        icon: "star.fill",
                        title: "Rate App",
                        color: .yellow
                    ) {
                        // Handle app rating
                    }
                }
                
                // About
                Section("About") {
                    HStack {
                        Image(systemName: "info.circle.fill")
                            .foregroundColor(.gray)
                            .frame(width: 24)
                        
                        Text("Version")
                            .foregroundColor(.primary)
                        
                        Spacer()
                        
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)
                }
                
                // Account Actions
                Section {
                    Button("Sign Out") {
                        showingLogoutAlert = true
                    }
                    .foregroundColor(.red)
                    
                    Button("Delete Account") {
                        showingDeleteAccountAlert = true
                    }
                    .foregroundColor(.red)
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
        }
        .alert("Sign Out", isPresented: $showingLogoutAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Sign Out", role: .destructive) {
                networkManager.logout()
            }
        } message: {
            Text("Are you sure you want to sign out?")
        }
        .alert("Delete Account", isPresented: $showingDeleteAccountAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Delete", role: .destructive) {
                // Handle account deletion
            }
        } message: {
            Text("This action cannot be undone. All your data will be permanently deleted.")
        }
    }
}

struct SettingsToggleRow: View {
    let icon: String
    let title: String
    @Binding var isOn: Bool
    let color: Color
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(color)
                .frame(width: 24)
            
            Text(title)
                .foregroundColor(.primary)
            
            Spacer()
            
            Toggle("", isOn: $isOn)
                .labelsHidden()
        }
        .padding(.vertical, 4)
    }
}

struct SettingsNavigationRow: View {
    let icon: String
    let title: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .frame(width: 24)
                
                Text(title)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 4)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    SettingsView()
        .environmentObject(NetworkManager())
}