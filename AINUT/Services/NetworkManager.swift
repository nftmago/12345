import Foundation
import SwiftUI

@MainActor
class NetworkManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let baseURL = "https://nutai-production.up.railway.app" // Update with your backend URL
    private var authToken: String? {
        get { UserDefaults.standard.string(forKey: "auth_token") }
        set { UserDefaults.standard.set(newValue, forKey: "auth_token") }
    }
    
    init() {
        checkAuthStatus()
    }
    
    func checkAuthStatus() {
        isAuthenticated = authToken != nil
        if isAuthenticated {
            Task {
                await getCurrentUser()
            }
        }
    }
    
    // MARK: - Authentication
    func register(username: String, email: String, password: String) async {
        isLoading = true
        errorMessage = nil
        
        let userCreate = UserCreate(username: username, email: email, password: password)
        
        do {
            let user: User = try await performRequest(
                endpoint: "/auth/register",
                method: "POST",
                body: userCreate,
                requiresAuth: false
            )
            
            // After successful registration, log in
            await login(username: username, password: password)
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    func login(username: String, password: String) async {
        isLoading = true
        errorMessage = nil
        
        let userLogin = UserLogin(username: username, password: password)
        
        do {
            let token: Token = try await performRequest(
                endpoint: "/auth/login",
                method: "POST",
                body: userLogin,
                requiresAuth: false
            )
            
            authToken = token.accessToken
            isAuthenticated = true
            await getCurrentUser()
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    func logout() {
        authToken = nil
        isAuthenticated = false
        currentUser = nil
    }
    
    func getCurrentUser() async {
        do {
            let user: User = try await performRequest(
                endpoint: "/auth/me",
                method: "GET",
                requiresAuth: true
            )
            currentUser = user
        } catch {
            // If getting current user fails, token might be expired
            logout()
        }
    }
    
    // MARK: - Meal Analysis
    func analyzeMeal(imageUrl: String? = nil, userInput: String, corrections: String? = nil) async throws -> MealResponse {
        let request = MealRequest(imageUrl: imageUrl, userInput: userInput, corrections: corrections)
        
        return try await performRequest(
            endpoint: "/ai/analyze-meal",
            method: "POST",
            body: request,
            requiresAuth: false
        )
    }
    
    // MARK: - Nutrition Advice
    func getNutritionAdvice(foodLog: [FoodLogItem], dailyTargets: [String: Double]) async throws -> NutritionistResponse {
        let request = [
            "food_log": foodLog,
            "daily_targets": dailyTargets
        ]
        
        return try await performRequest(
            endpoint: "/ai/nutrition-advice",
            method: "POST",
            body: request,
            requiresAuth: false
        )
    }
    
    func getPersonalizedNutritionAdvice(foodLog: [FoodLogItem], dailyTargets: [String: Double]) async throws -> NutritionistResponse {
        guard let userId = currentUser?.username else {
            throw NetworkError.notAuthenticated
        }
        
        let request = [
            "user_id": userId,
            "food_log": foodLog,
            "daily_targets": dailyTargets
        ] as [String : Any]
        
        return try await performRequest(
            endpoint: "/ai/personalized-nutrition-advice",
            method: "POST",
            body: request,
            requiresAuth: true
        )
    }
    
    // MARK: - Food Logging
    func saveFoodLog(mealTime: String, foods: [FoodLogItem], totalCalories: Double) async throws -> SaveFoodLogResponse {
        guard let userId = currentUser?.username else {
            throw NetworkError.notAuthenticated
        }
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        let dateString = dateFormatter.string(from: Date())
        
        let request = SaveFoodLogRequest(
            userId: userId,
            dateString: dateString,
            mealTime: mealTime,
            foods: foods,
            totalCalories: totalCalories
        )
        
        return try await performRequest(
            endpoint: "/food-logs",
            method: "POST",
            body: request,
            requiresAuth: true
        )
    }
    
    func getUserFoodLogs(dateFilter: String? = nil, limit: Int = 50) async throws -> [FoodLogResponse] {
        guard let userId = currentUser?.username else {
            throw NetworkError.notAuthenticated
        }
        
        var endpoint = "/users/\(userId)/food-logs?limit=\(limit)"
        if let dateFilter = dateFilter {
            endpoint += "&date_filter=\(dateFilter)"
        }
        
        return try await performRequest(
            endpoint: endpoint,
            method: "GET",
            requiresAuth: true
        )
    }
    
    // MARK: - User Profile
    func saveUserProfile(_ profile: UserProfile) async throws {
        let _: [String: Any] = try await performRequest(
            endpoint: "/users/profile",
            method: "POST",
            body: profile,
            requiresAuth: true
        )
    }
    
    func getUserProfile() async throws -> UserProfile {
        guard let userId = currentUser?.username else {
            throw NetworkError.notAuthenticated
        }
        
        return try await performRequest(
            endpoint: "/users/\(userId)/profile",
            method: "GET",
            requiresAuth: true
        )
    }
    
    // MARK: - Achievements
    func getUserAchievements() async throws -> [Achievement] {
        guard let userId = currentUser?.username else {
            throw NetworkError.notAuthenticated
        }
        
        return try await performRequest(
            endpoint: "/users/\(userId)/achievements",
            method: "GET",
            requiresAuth: true
        )
    }
    
    // MARK: - Image Upload
    func uploadImage(_ imageData: Data, imageType: String = "meal") async throws -> String {
        guard let token = authToken else {
            throw NetworkError.notAuthenticated
        }
        
        let url = URL(string: "\(baseURL)/upload-user-image")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        
        // Add image data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n".data(using: .utf8)!)
        
        // Add image type
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image_type\"\r\n\r\n".data(using: .utf8)!)
        body.append(imageType.data(using: .utf8)!)
        body.append("\r\n".data(using: .utf8)!)
        
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        
        if httpResponse.statusCode == 200 {
            let uploadResponse = try JSONDecoder().decode([String: String].self, from: data)
            return uploadResponse["url"] ?? ""
        } else {
            throw NetworkError.serverError(httpResponse.statusCode)
        }
    }
    
    // MARK: - Generic Request Handler
    private func performRequest<T: Codable, U: Codable>(
        endpoint: String,
        method: String,
        body: T? = nil,
        requiresAuth: Bool = false
    ) async throws -> U {
        
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if requiresAuth {
            guard let token = authToken else {
                throw NetworkError.notAuthenticated
            }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = try JSONEncoder().encode(body)
        }
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        
        if httpResponse.statusCode == 200 || httpResponse.statusCode == 201 {
            return try JSONDecoder().decode(U.self, from: data)
        } else {
            // Try to decode error message
            if let errorResponse = try? JSONDecoder().decode(APIError.self, from: data) {
                throw NetworkError.apiError(errorResponse.detail)
            } else {
                throw NetworkError.serverError(httpResponse.statusCode)
            }
        }
    }
    
    private func performRequest<U: Codable>(
        endpoint: String,
        method: String,
        body: [String: Any]? = nil,
        requiresAuth: Bool = false
    ) async throws -> U {
        
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if requiresAuth {
            guard let token = authToken else {
                throw NetworkError.notAuthenticated
            }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        
        if httpResponse.statusCode == 200 || httpResponse.statusCode == 201 {
            return try JSONDecoder().decode(U.self, from: data)
        } else {
            // Try to decode error message
            if let errorResponse = try? JSONDecoder().decode(APIError.self, from: data) {
                throw NetworkError.apiError(errorResponse.detail)
            } else {
                throw NetworkError.serverError(httpResponse.statusCode)
            }
        }
    }
}

enum NetworkError: LocalizedError {
    case invalidURL
    case notAuthenticated
    case invalidResponse
    case serverError(Int)
    case apiError(String)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .notAuthenticated:
            return "Not authenticated"
        case .invalidResponse:
            return "Invalid response"
        case .serverError(let code):
            return "Server error: \(code)"
        case .apiError(let message):
            return message
        }
    }
}