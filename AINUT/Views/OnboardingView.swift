import SwiftUI

struct OnboardingView: View {
    @State private var currentPage = 0
    @Binding var showOnboarding: Bool
    
    private let pages = [
        OnboardingPage(
            title: "Track Your Nutrition",
            subtitle: "Take photos or describe your meals for instant AI-powered nutrition analysis",
            imageName: "camera.fill",
            color: .green
        ),
        OnboardingPage(
            title: "Get Personalized Advice",
            subtitle: "Receive tailored nutrition recommendations based on your goals and preferences",
            imageName: "heart.text.square.fill",
            color: .blue
        ),
        OnboardingPage(
            title: "Achieve Your Goals",
            subtitle: "Earn achievements and build healthy habits with our gamified tracking system",
            imageName: "trophy.fill",
            color: .orange
        )
    ]
    
    var body: some View {
        VStack(spacing: 0) {
            // Page Content
            TabView(selection: $currentPage) {
                ForEach(0..<pages.count, id: \.self) { index in
                    OnboardingPageView(page: pages[index])
                        .tag(index)
                }
            }
            .tabViewStyle(PageTabViewStyle(indexDisplayMode: .never))
            .animation(.easeInOut, value: currentPage)
            
            // Bottom Section
            VStack(spacing: 24) {
                // Page Indicator
                HStack(spacing: 8) {
                    ForEach(0..<pages.count, id: \.self) { index in
                        Circle()
                            .fill(currentPage == index ? Color.green : Color.gray.opacity(0.3))
                            .frame(width: 8, height: 8)
                            .scaleEffect(currentPage == index ? 1.2 : 1.0)
                            .animation(.easeInOut(duration: 0.3), value: currentPage)
                    }
                }
                
                // Action Buttons
                VStack(spacing: 16) {
                    if currentPage == pages.count - 1 {
                        Button("Get Started") {
                            withAnimation(.easeInOut(duration: 0.5)) {
                                showOnboarding = false
                                UserDefaults.standard.set(true, forKey: "hasSeenOnboarding")
                            }
                        }
                        .buttonStyle(PrimaryButtonStyle())
                        .transition(.opacity)
                    } else {
                        Button("Next") {
                            withAnimation(.easeInOut(duration: 0.3)) {
                                currentPage += 1
                            }
                        }
                        .buttonStyle(PrimaryButtonStyle())
                    }
                    
                    Button("Skip") {
                        withAnimation(.easeInOut(duration: 0.5)) {
                            showOnboarding = false
                            UserDefaults.standard.set(true, forKey: "hasSeenOnboarding")
                        }
                    }
                    .foregroundColor(.secondary)
                    .font(.subheadline)
                }
            }
            .padding(.horizontal, 32)
            .padding(.bottom, 50)
        }
        .background(
            LinearGradient(
                colors: [Color(.systemBackground), Color(.systemGray6)],
                startPoint: .top,
                endPoint: .bottom
            )
        )
        .ignoresSafeArea(.all, edges: .top)
    }
}

struct OnboardingPage {
    let title: String
    let subtitle: String
    let imageName: String
    let color: Color
}

struct OnboardingPageView: View {
    let page: OnboardingPage
    
    var body: some View {
        VStack(spacing: 40) {
            Spacer()
            
            // Icon
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [page.color, page.color.opacity(0.7)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 120, height: 120)
                    .shadow(color: page.color.opacity(0.3), radius: 20, x: 0, y: 10)
                
                Image(systemName: page.imageName)
                    .font(.system(size: 50, weight: .medium))
                    .foregroundColor(.white)
            }
            
            // Text Content
            VStack(spacing: 16) {
                Text(page.title)
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.primary)
                
                Text(page.subtitle)
                    .font(.body)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
                    .lineLimit(nil)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.horizontal, 32)
            
            Spacer()
        }
    }
}

#Preview {
    OnboardingView(showOnboarding: .constant(true))
}