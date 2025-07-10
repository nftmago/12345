import SwiftUI

struct AchievementsView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var achievements: [Achievement] = []
    @State private var isLoading = false
    @State private var selectedAchievement: Achievement?
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Header Stats
                    VStack(spacing: 16) {
                        Text("Your Progress")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        HStack(spacing: 20) {
                            StatCard(
                                title: "Achievements",
                                value: "\(achievements.count)",
                                icon: "trophy.fill",
                                color: .yellow
                            )
                            
                            StatCard(
                                title: "Total Points",
                                value: "\(totalPoints)",
                                icon: "star.fill",
                                color: .orange
                            )
                            
                            StatCard(
                                title: "Level",
                                value: "\(currentLevel)",
                                icon: "crown.fill",
                                color: .purple
                            )
                        }
                    }
                    .padding(.horizontal)
                    
                    // Progress Bar
                    VStack(spacing: 8) {
                        HStack {
                            Text("Level \(currentLevel)")
                                .font(.headline)
                                .fontWeight(.semibold)
                            
                            Spacer()
                            
                            Text("\(pointsToNextLevel) points to next level")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        ProgressView(value: levelProgress)
                            .progressViewStyle(LinearProgressViewStyle(tint: .green))
                            .scaleEffect(x: 1, y: 2, anchor: .center)
                    }
                    .padding(.horizontal)
                    
                    // Achievements Grid
                    if isLoading {
                        ProgressView("Loading achievements...")
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if achievements.isEmpty {
                        EmptyAchievementsView()
                    } else {
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 16) {
                            ForEach(achievements) { achievement in
                                AchievementCard(achievement: achievement) {
                                    selectedAchievement = achievement
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                    
                    Spacer(minLength: 100)
                }
                .padding(.vertical)
            }
            .navigationTitle("Achievements")
            .navigationBarTitleDisplayMode(.large)
            .refreshable {
                await loadAchievements()
            }
        }
        .sheet(item: $selectedAchievement) { achievement in
            AchievementDetailView(achievement: achievement)
        }
        .onAppear {
            Task {
                await loadAchievements()
            }
        }
    }
    
    private var totalPoints: Int {
        achievements.reduce(0) { $0 + $1.points }
    }
    
    private var currentLevel: Int {
        max(1, totalPoints / 100)
    }
    
    private var pointsToNextLevel: Int {
        let nextLevelPoints = (currentLevel + 1) * 100
        return nextLevelPoints - totalPoints
    }
    
    private var levelProgress: Double {
        let currentLevelPoints = currentLevel * 100
        let nextLevelPoints = (currentLevel + 1) * 100
        let progressPoints = totalPoints - currentLevelPoints
        return Double(progressPoints) / Double(nextLevelPoints - currentLevelPoints)
    }
    
    private func loadAchievements() async {
        guard let userId = networkManager.currentUser?.username else { return }
        
        isLoading = true
        
        do {
            achievements = try await networkManager.getUserAchievements()
        } catch {
            print("Failed to load achievements: \(error)")
        }
        
        isLoading = false
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
                .font(.title2)
                .fontWeight(.bold)
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

struct AchievementCard: View {
    let achievement: Achievement
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 12) {
                Text(achievement.badgeIcon)
                    .font(.system(size: 40))
                
                VStack(spacing: 4) {
                    Text(achievement.achievementName)
                        .font(.headline)
                        .fontWeight(.semibold)
                        .multilineTextAlignment(.center)
                        .foregroundColor(.primary)
                    
                    Text(achievement.description)
                        .font(.caption)
                        .multilineTextAlignment(.center)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                    
                    Text("\(achievement.points) points")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.green)
                }
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(16)
            .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct EmptyAchievementsView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "trophy.circle")
                .font(.system(size: 60))
                .foregroundColor(.gray)
            
            Text("No Achievements Yet")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.primary)
            
            Text("Start logging your meals to earn your first achievement!")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}

struct AchievementDetailView: View {
    let achievement: Achievement
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        NavigationView {
            VStack(spacing: 32) {
                // Badge
                VStack(spacing: 16) {
                    Text(achievement.badgeIcon)
                        .font(.system(size: 80))
                    
                    Text(achievement.achievementName)
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .multilineTextAlignment(.center)
                }
                
                // Details
                VStack(spacing: 16) {
                    Text(achievement.description)
                        .font(.body)
                        .multilineTextAlignment(.center)
                        .foregroundColor(.secondary)
                    
                    HStack {
                        Label("\(achievement.points) Points", systemImage: "star.fill")
                            .foregroundColor(.orange)
                        
                        Spacer()
                        
                        Label(achievement.earnedDate.formatted(date: .abbreviated, time: .omitted), systemImage: "calendar")
                            .foregroundColor(.blue)
                    }
                    .font(.subheadline)
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("Achievement")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarItems(trailing: Button("Done") {
                presentationMode.wrappedValue.dismiss()
            })
        }
    }
}

#Preview {
    AchievementsView()
        .environmentObject(NetworkManager())
}