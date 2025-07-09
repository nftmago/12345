import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var userProfile: UserProfile?
    @State private var achievements: [Achievement] = []
    @State private var isLoading = false
    @State private var showingEditProfile = false
    @State private var showingLogoutAlert = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Profile Header
                    VStack(spacing: 16) {
                        // Avatar
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [.green, .green.opacity(0.7)],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 80, height: 80)
                            .overlay(
                                Text(networkManager.currentUser?.username.prefix(1).uppercased() ?? "U")
                                    .font(.largeTitle)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                            )
                        
                        VStack(spacing: 4) {
                            Text(networkManager.currentUser?.username.capitalized ?? "User")
                                .font(.title2)
                                .fontWeight(.bold)
                            
                            Text(networkManager.currentUser?.email ?? "")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        
                        Button("Edit Profile") {
                            showingEditProfile = true
                        }
                        .font(.subheadline)
                        .foregroundColor(.green)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(8)
                    }
                    .padding(.top)
                    
                    // Quick Stats
                    if let profile = userProfile {
                        ProfileStatsView(profile: profile)
                    }
                    
                    // Achievements Section
                    if !achievements.isEmpty {
                        VStack(alignment: .leading, spacing: 16) {
                            HStack {
                                Text("Achievements")
                                    .font(.title2)
                                    .fontWeight(.semibold)
                                
                                Spacer()
                                
                                Text("\(achievements.count) earned")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .padding(.horizontal)
                            
                            LazyVGrid(columns: [
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                                GridItem(.flexible())
                            ], spacing: 16) {
                                ForEach(achievements.prefix(6)) { achievement in
                                    AchievementBadge(achievement: achievement)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                    
                    // Settings Section
                    VStack(spacing: 0) {
                        SettingsRow(
                            icon: "person.circle",
                            title: "Edit Profile",
                            action: { showingEditProfile = true }
                        )
                        
                        Divider()
                            .padding(.leading, 50)
                        
                        SettingsRow(
                            icon: "bell",
                            title: "Notifications",
                            action: { /* Handle notifications */ }
                        )
                        
                        Divider()
                            .padding(.leading, 50)
                        
                        SettingsRow(
                            icon: "questionmark.circle",
                            title: "Help & Support",
                            action: { /* Handle help */ }
                        )
                        
                        Divider()
                            .padding(.leading, 50)
                        
                        SettingsRow(
                            icon: "info.circle",
                            title: "About",
                            action: { /* Handle about */ }
                        )
                        
                        Divider()
                            .padding(.leading, 50)
                        
                        SettingsRow(
                            icon: "rectangle.portrait.and.arrow.right",
                            title: "Sign Out",
                            titleColor: .red,
                            action: { showingLogoutAlert = true }
                        )
                    }
                    .background(Color(.systemBackground))
                    .cornerRadius(16)
                    .padding(.horizontal)
                    
                    Spacer(minLength: 100)
                }
            }
            .navigationBarHidden(true)
            .refreshable {
                await loadProfileData()
            }
        }
        .sheet(isPresented: $showingEditProfile) {
            EditProfileView(userProfile: $userProfile)
        }
        .alert("Sign Out", isPresented: $showingLogoutAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Sign Out", role: .destructive) {
                networkManager.logout()
            }
        } message: {
            Text("Are you sure you want to sign out?")
        }
        .onAppear {
            Task {
                await loadProfileData()
            }
        }
    }
    
    private func loadProfileData() async {
        isLoading = true
        
        async let profileTask = loadUserProfile()
        async let achievementsTask = loadAchievements()
        
        await profileTask
        await achievementsTask
        
        isLoading = false
    }
    
    private func loadUserProfile() async {
        do {
            userProfile = try await networkManager.getUserProfile()
        } catch {
            print("Failed to load user profile: \(error)")
        }
    }
    
    private func loadAchievements() async {
        do {
            achievements = try await networkManager.getUserAchievements()
        } catch {
            print("Failed to load achievements: \(error)")
        }
    }
}

struct ProfileStatsView: View {
    let profile: UserProfile
    
    var body: some View {
        VStack(spacing: 16) {
            HStack {
                Text("Profile Stats")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
            }
            .padding(.horizontal)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                StatCard(
                    title: "Activity Level",
                    value: profile.activityLevel.capitalized,
                    icon: "figure.walk",
                    color: .blue
                )
                
                StatCard(
                    title: "Preferences",
                    value: "\(profile.dietaryPreferences.count) set",
                    icon: "heart.fill",
                    color: .red
                )
                
                StatCard(
                    title: "Allergies",
                    value: profile.allergies.isEmpty ? "None" : "\(profile.allergies.count)",
                    icon: "exclamationmark.triangle",
                    color: .orange
                )
                
                StatCard(
                    title: "AI Style",
                    value: profile.aiPersonalityType.capitalized,
                    icon: "brain.head.profile",
                    color: .purple
                )
            }
            .padding(.horizontal)
        }
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            
            Text(value)
                .font(.headline)
                .fontWeight(.semibold)
                .foregroundColor(.primary)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct AchievementBadge: View {
    let achievement: Achievement
    
    var body: some View {
        VStack(spacing: 6) {
            Text(achievement.badgeIcon)
                .font(.title)
            
            Text(achievement.achievementName)
                .font(.caption2)
                .fontWeight(.medium)
                .multilineTextAlignment(.center)
                .lineLimit(2)
            
            Text("\(achievement.points) pts")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(8)
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct SettingsRow: View {
    let icon: String
    let title: String
    let titleColor: Color
    let action: () -> Void
    
    init(icon: String, title: String, titleColor: Color = .primary, action: @escaping () -> Void) {
        self.icon = icon
        self.title = title
        self.titleColor = titleColor
        self.action = action
    }
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundColor(titleColor == .red ? .red : .green)
                    .frame(width: 24)
                
                Text(title)
                    .font(.body)
                    .foregroundColor(titleColor)
                
                Spacer()
                
                if titleColor != .red {
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 16)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct EditProfileView: View {
    @Binding var userProfile: UserProfile?
    @EnvironmentObject var networkManager: NetworkManager
    @Environment(\.presentationMode) var presentationMode
    
    @State private var dietaryPreferences: [String] = []
    @State private var favoriteFoods: [String] = []
    @State private var dislikedFoods: [String] = []
    @State private var allergies: [String] = []
    @State private var activityLevel = "normal"
    @State private var aiPersonalityType = "supportive"
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    private let activityLevels = ["sedentary", "light", "normal", "active", "very_active"]
    private let personalityTypes = ["supportive", "motivational", "educational", "fun"]
    
    var body: some View {
        NavigationView {
            Form {
                Section("Activity Level") {
                    Picker("Activity Level", selection: $activityLevel) {
                        ForEach(activityLevels, id: \.self) { level in
                            Text(level.capitalized.replacingOccurrences(of: "_", with: " "))
                                .tag(level)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
                
                Section("AI Personality") {
                    Picker("AI Personality", selection: $aiPersonalityType) {
                        ForEach(personalityTypes, id: \.self) { type in
                            Text(type.capitalized).tag(type)
                        }
                    }
                }
                
                Section("Dietary Preferences") {
                    ForEach(dietaryPreferences, id: \.self) { preference in
                        Text(preference)
                    }
                    .onDelete(perform: deleteDietaryPreference)
                    
                    Button("Add Preference") {
                        // Add preference logic
                    }
                }
                
                Section("Favorite Foods") {
                    ForEach(favoriteFoods, id: \.self) { food in
                        Text(food)
                    }
                    .onDelete(perform: deleteFavoriteFood)
                    
                    Button("Add Favorite Food") {
                        // Add food logic
                    }
                }
                
                Section("Disliked Foods") {
                    ForEach(dislikedFoods, id: \.self) { food in
                        Text(food)
                    }
                    .onDelete(perform: deleteDislikedFood)
                    
                    Button("Add Disliked Food") {
                        // Add food logic
                    }
                }
                
                Section("Allergies") {
                    ForEach(allergies, id: \.self) { allergy in
                        Text(allergy)
                    }
                    .onDelete(perform: deleteAllergy)
                    
                    Button("Add Allergy") {
                        // Add allergy logic
                    }
                }
                
                if let errorMessage = errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("Edit Profile")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarItems(
                leading: Button("Cancel") {
                    presentationMode.wrappedValue.dismiss()
                },
                trailing: Button("Save") {
                    saveProfile()
                }
                .disabled(isLoading)
            )
        }
        .onAppear {
            loadCurrentProfile()
        }
    }
    
    private func loadCurrentProfile() {
        if let profile = userProfile {
            dietaryPreferences = profile.dietaryPreferences
            favoriteFoods = profile.favoriteFoods
            dislikedFoods = profile.dislikedFoods
            allergies = profile.allergies
            activityLevel = profile.activityLevel
            aiPersonalityType = profile.aiPersonalityType
        }
    }
    
    private func saveProfile() {
        guard let currentUser = networkManager.currentUser else { return }
        
        Task {
            isLoading = true
            errorMessage = nil
            
            do {
                let updatedProfile = UserProfile(
                    userId: currentUser.username,
                    dietaryPreferences: dietaryPreferences,
                    favoriteFoods: favoriteFoods,
                    dislikedFoods: dislikedFoods,
                    cuisinePreferences: userProfile?.cuisinePreferences ?? [],
                    allergies: allergies,
                    activityLevel: activityLevel,
                    nutritionGoals: userProfile?.nutritionGoals ?? [:],
                    aiPersonalityType: aiPersonalityType,
                    preferredCommunicationStyle: userProfile?.preferredCommunicationStyle ?? "encouraging",
                    coachingFrequency: userProfile?.coachingFrequency ?? "daily"
                )
                
                try await networkManager.saveUserProfile(updatedProfile)
                userProfile = updatedProfile
                
                await MainActor.run {
                    presentationMode.wrappedValue.dismiss()
                }
                
            } catch {
                errorMessage = error.localizedDescription
            }
            
            isLoading = false
        }
    }
    
    private func deleteDietaryPreference(at offsets: IndexSet) {
        dietaryPreferences.remove(atOffsets: offsets)
    }
    
    private func deleteFavoriteFood(at offsets: IndexSet) {
        favoriteFoods.remove(atOffsets: offsets)
    }
    
    private func deleteDislikedFood(at offsets: IndexSet) {
        dislikedFoods.remove(atOffsets: offsets)
    }
    
    private func deleteAllergy(at offsets: IndexSet) {
        allergies.remove(atOffsets: offsets)
    }
}

#Preview {
    ProfileView()
        .environmentObject(NetworkManager())
}