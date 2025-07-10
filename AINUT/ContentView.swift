import SwiftUI

struct ContentView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var selectedTab = 0
    @State private var showOnboarding = !UserDefaults.standard.bool(forKey: "hasSeenOnboarding")
    
    var body: some View {
        Group {
            if networkManager.isAuthenticated {
                TabView(selection: $selectedTab) {
                    HomeView()
                        .tabItem {
                            Image(systemName: "house.fill")
                            Text("Home")
                        }
                        .tag(0)
                    
                    MealAnalysisView()
                        .tabItem {
                            Image(systemName: "camera.fill")
                            Text("Analyze")
                        }
                        .tag(1)
                    
                    FoodLogView()
                        .tabItem {
                            Image(systemName: "list.bullet")
                            Text("Log")
                        }
                        .tag(2)
                    
                    StatsView()
                        .tabItem {
                            Image(systemName: "chart.bar.fill")
                            Text("Stats")
                        }
                        .tag(3)
                    
                    NutritionAdviceView()
                        .tabItem {
                            Image(systemName: "heart.fill")
                            Text("Advice")
                        }
                        .tag(4)
                    
                    ProfileView()
                        .tabItem {
                            Image(systemName: "person.fill")
                            Text("Profile")
                        }
                        .tag(5)
                }
                .accentColor(.green)
            } else {
                AuthView()
            }
        }
        .fullScreenCover(isPresented: $showOnboarding) {
            OnboardingView(showOnboarding: $showOnboarding)
        }
        .onAppear {
            networkManager.checkAuthStatus()
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(NetworkManager())
}