import SwiftUI

struct ContentView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var selectedTab = 0
    
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
                    
                    NutritionAdviceView()
                        .tabItem {
                            Image(systemName: "heart.fill")
                            Text("Advice")
                        }
                        .tag(3)
                    
                    ProfileView()
                        .tabItem {
                            Image(systemName: "person.fill")
                            Text("Profile")
                        }
                        .tag(4)
                }
                .accentColor(.green)
            } else {
                AuthView()
            }
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