import SwiftUI

struct HomeView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var achievements: [Achievement] = []
    @State private var todaysFoodLogs: [FoodLogResponse] = []
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Welcome Header
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            VStack(alignment: .leading) {
                                Text("Welcome back,")
                                    .font(.title2)
                                    .foregroundColor(.secondary)
                                
                                Text(networkManager.currentUser?.username.capitalized ?? "User")
                                    .font(.largeTitle)
                                    .fontWeight(.bold)
                                    .foregroundColor(.primary)
                            }
                            
                            Spacer()
                            
                            Image(systemName: "leaf.fill")
                                .font(.system(size: 40))
                                .foregroundColor(.green)
                        }
                        
                        Text("Let's make today nutritious! 🌱")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.horizontal)
                    
                    // Quick Actions
                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 16) {
                        QuickActionCard(
                            icon: "camera.fill",
                            title: "Analyze Meal",
                            subtitle: "Take a photo",
                            color: .blue,
                            action: { /* Navigate to camera */ }
                        )
                        
                        QuickActionCard(
                            icon: "heart.fill",
                            title: "Get Advice",
                            subtitle: "Nutrition tips",
                            color: .red,
                            action: { /* Navigate to advice */ }
                        )
                        
                        QuickActionCard(
                            icon: "list.bullet",
                            title: "Food Log",
                            subtitle: "View history",
                            color: .orange,
                            action: { /* Navigate to log */ }
                        )
                        
                        QuickActionCard(
                            icon: "person.fill",
                            title: "Profile",
                            subtitle: "Settings",
                            color: .purple,
                            action: { /* Navigate to profile */ }
                        )
                    }
                    .padding(.horizontal)
                    
                    // Today's Summary
                    VStack(alignment: .leading, spacing: 16) {
                        HStack {
                            Text("Today's Summary")
                                .font(.title2)
                                .fontWeight(.semibold)
                            
                            Spacer()
                            
                            Text(todayString)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        if todaysFoodLogs.isEmpty {
                            VStack(spacing: 12) {
                                Image(systemName: "fork.knife.circle")
                                    .font(.system(size: 40))
                                    .foregroundColor(.gray)
                                
                                Text("No meals logged today")
                                    .font(.headline)
                                    .foregroundColor(.secondary)
                                
                                Text("Start by analyzing your first meal!")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                                    .multilineTextAlignment(.center)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 40)
                        } else {
                            LazyVStack(spacing: 12) {
                                ForEach(todaysFoodLogs) { log in
                                    FoodLogCard(log: log)
                                }
                            }
                        }
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(16)
                    .padding(.horizontal)
                    
                    // Recent Achievements
                    if !achievements.isEmpty {
                        VStack(alignment: .leading, spacing: 16) {
                            Text("Recent Achievements")
                                .font(.title2)
                                .fontWeight(.semibold)
                                .padding(.horizontal)
                            
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 16) {
                                    ForEach(achievements.prefix(5)) { achievement in
                                        AchievementCard(achievement: achievement)
                                    }
                                }
                                .padding(.horizontal)
                            }
                        }
                    }
                    
                    Spacer(minLength: 100)
                }
                .padding(.vertical)
            }
            .navigationBarHidden(true)
            .refreshable {
                await loadData()
            }
        }
        .onAppear {
            Task {
                await loadData()
            }
        }
    }
    
    private var todayString: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter.string(from: Date())
    }
    
    private func loadData() async {
        isLoading = true
        
        async let achievementsTask = loadAchievements()
        async let foodLogsTask = loadTodaysFoodLogs()
        
        await achievementsTask
        await foodLogsTask
        
        isLoading = false
    }
    
    private func loadAchievements() async {
        do {
            achievements = try await networkManager.getUserAchievements()
        } catch {
            print("Failed to load achievements: \(error)")
        }
    }
    
    private func loadTodaysFoodLogs() async {
        do {
            let dateFormatter = DateFormatter()
            dateFormatter.dateFormat = "yyyy-MM-dd"
            let today = dateFormatter.string(from: Date())
            
            todaysFoodLogs = try await networkManager.getUserFoodLogs(dateFilter: today, limit: 10)
        } catch {
            print("Failed to load today's food logs: \(error)")
        }
    }
}

struct QuickActionCard: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 30))
                    .foregroundColor(color)
                
                VStack(spacing: 4) {
                    Text(title)
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text(subtitle)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 20)
            .background(Color(.systemBackground))
            .cornerRadius(16)
            .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct FoodLogCard: View {
    let log: FoodLogResponse
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(log.mealTime.capitalized)
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Text("\(Int(log.totalCalories)) calories")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Image(systemName: mealIcon(for: log.mealTime))
                .font(.title2)
                .foregroundColor(.green)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
    }
    
    private func mealIcon(for mealTime: String) -> String {
        switch mealTime.lowercased() {
        case "breakfast":
            return "sunrise.fill"
        case "lunch":
            return "sun.max.fill"
        case "dinner":
            return "moon.fill"
        default:
            return "fork.knife"
        }
    }
}

struct AchievementCard: View {
    let achievement: Achievement
    
    var body: some View {
        VStack(spacing: 8) {
            Text(achievement.badgeIcon)
                .font(.system(size: 30))
            
            Text(achievement.achievementName)
                .font(.caption)
                .fontWeight(.semibold)
                .multilineTextAlignment(.center)
                .foregroundColor(.primary)
            
            Text("\(achievement.points) pts")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(width: 80, height: 80)
        .padding(8)
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

#Preview {
    HomeView()
        .environmentObject(NetworkManager())
}