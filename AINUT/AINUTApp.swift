import SwiftUI
import UserNotifications

@main
struct AINUTApp: App {
    @StateObject private var networkManager = NetworkManager()
    @StateObject private var notificationManager = NotificationManager()
    @StateObject private var healthKitManager = HealthKitManager()
    
    init() {
        setupNotifications()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(networkManager)
                .environmentObject(notificationManager)
                .environmentObject(healthKitManager)
                .onAppear {
                    Task {
                        await requestPermissions()
                    }
                }
        }
    }
    
    private func setupNotifications() {
        let delegate = NotificationDelegate()
        UNUserNotificationCenter.current().delegate = delegate
        
        // Setup notification categories
        notificationManager.setupNotificationCategories()
    }
    
    private func requestPermissions() async {
        await notificationManager.requestPermission()
        await healthKitManager.requestAuthorization()
    }
}