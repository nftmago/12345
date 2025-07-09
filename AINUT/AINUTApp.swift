import SwiftUI

@main
struct AINUTApp: App {
    @StateObject private var networkManager = NetworkManager()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(networkManager)
        }
    }
}