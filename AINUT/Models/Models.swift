import Foundation

// MARK: - Authentication Models
struct User: Codable, Identifiable {
    let id: Int
    let username: String
    let email: String
    let isActive: Bool
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, username, email
        case isActive = "is_active"
        case createdAt = "created_at"
    }
}

struct UserCreate: Codable {
    let username: String
    let email: String
    let password: String
}

struct UserLogin: Codable {
    let username: String
    let password: String
}

struct Token: Codable {
    let accessToken: String
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
    }
}

// MARK: - Meal Analysis Models
struct MealRequest: Codable {
    let imageUrl: String?
    let userInput: String
    let corrections: String?
    
    enum CodingKeys: String, CodingKey {
        case imageUrl = "image_url"
        case userInput = "user_input"
        case corrections
    }
}

struct Food: Codable, Identifiable {
    let id = UUID()
    let name: String
    let calories: Int
    let proteinG: Double
    let carbsG: Double
    let fatG: Double
    
    enum CodingKeys: String, CodingKey {
        case name, calories
        case proteinG = "protein_g"
        case carbsG = "carbs_g"
        case fatG = "fat_g"
    }
}

struct MealResponse: Codable {
    let mealName: String
    let mealType: String
    let foods: [Food]
    let totalCalories: Int
    let analysisMethod: String
    
    enum CodingKeys: String, CodingKey {
        case mealName = "meal_name"
        case mealType = "meal_type"
        case foods
        case totalCalories = "total_calories"
        case analysisMethod = "analysis_method"
    }
}

// MARK: - Nutrition Advice Models
struct FoodLogItem: Codable {
    let name: String
    let calories: Double
    let proteinG: Double
    let carbsG: Double
    let fatG: Double
    let micronutrients: [String: Double]?
    
    enum CodingKeys: String, CodingKey {
        case name, calories
        case proteinG = "protein_g"
        case carbsG = "carbs_g"
        case fatG = "fat_g"
        case micronutrients
    }
}

struct FoodSuggestion: Codable, Identifiable {
    let id = UUID()
    let mealIdea: String
    let description: String
    let totalCalories: Double
    let proteinProvided: Double
    let carbsProvided: Double
    let fatProvided: Double
    let percentageCoverage: [String: Int]
    let mealType: String
    let easyToMake: Bool
    let whyPerfect: String
    
    enum CodingKeys: String, CodingKey {
        case mealIdea = "meal_idea"
        case description
        case totalCalories = "total_calories"
        case proteinProvided = "protein_provided"
        case carbsProvided = "carbs_provided"
        case fatProvided = "fat_provided"
        case percentageCoverage = "percentage_coverage"
        case mealType = "meal_type"
        case easyToMake = "easy_to_make"
        case whyPerfect = "why_perfect"
    }
}

struct NutrientAdvice: Codable, Identifiable {
    let id = UUID()
    let nutrient: String
    let currentIntake: Double
    let target: Double
    let deficit: Double
    let suggestions: [FoodSuggestion]
    let whyImportant: String
    
    enum CodingKeys: String, CodingKey {
        case nutrient
        case currentIntake = "current_intake"
        case target, deficit, suggestions
        case whyImportant = "why_important"
    }
}

struct NutritionistResponse: Codable {
    let overallSummary: String
    let safetyNotes: [String]
    let nutrientsToFocusOn: [NutrientAdvice]
    let achievements: [String]
    let tips: [String]
    let personalizedInsights: [String]?
    
    enum CodingKeys: String, CodingKey {
        case overallSummary = "overall_summary"
        case safetyNotes = "safety_notes"
        case nutrientsToFocusOn = "nutrients_to_focus_on"
        case achievements, tips
        case personalizedInsights = "personalized_insights"
    }
}

// MARK: - Food Log Models
struct SaveFoodLogRequest: Codable {
    let userId: String
    let dateString: String
    let mealTime: String
    let foods: [FoodLogItem]
    let totalCalories: Double
    
    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case dateString = "date_string"
        case mealTime = "meal_time"
        case foods
        case totalCalories = "total_calories"
    }
}

struct FoodLogResponse: Codable, Identifiable {
    let id = UUID()
    let logId: String
    let mealTime: String
    let foods: [[String: AnyCodable]]
    let totalCalories: Double
    let createdAt: String
    let dateString: String
    
    enum CodingKeys: String, CodingKey {
        case logId = "log_id"
        case mealTime = "meal_time"
        case foods
        case totalCalories = "total_calories"
        case createdAt = "created_at"
        case dateString = "date_string"
    }
}

// MARK: - User Profile Models
struct UserProfile: Codable {
    let userId: String
    let dietaryPreferences: [String]
    let favoriteFoods: [String]
    let dislikedFoods: [String]
    let cuisinePreferences: [String]
    let allergies: [String]
    let activityLevel: String
    let nutritionGoals: [String: Double]
    let aiPersonalityType: String
    let preferredCommunicationStyle: String
    let coachingFrequency: String
    
    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case dietaryPreferences = "dietary_preferences"
        case favoriteFoods = "favorite_foods"
        case dislikedFoods = "disliked_foods"
        case cuisinePreferences = "cuisine_preferences"
        case allergies
        case activityLevel = "activity_level"
        case nutritionGoals = "nutrition_goals"
        case aiPersonalityType = "ai_personality_type"
        case preferredCommunicationStyle = "preferred_communication_style"
        case coachingFrequency = "coaching_frequency"
    }
}

// MARK: - Achievement Models
struct Achievement: Codable, Identifiable {
    let id: Int
    let achievementName: String
    let description: String
    let points: Int
    let badgeIcon: String
    let earnedDate: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case achievementName = "achievement_name"
        case description, points
        case badgeIcon = "badge_icon"
        case earnedDate = "earned_date"
    }
}

// MARK: - Helper Types
struct AnyCodable: Codable {
    let value: Any
    
    init<T>(_ value: T?) {
        self.value = value ?? ()
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if let intValue = try? container.decode(Int.self) {
            value = intValue
        } else if let doubleValue = try? container.decode(Double.self) {
            value = doubleValue
        } else if let stringValue = try? container.decode(String.self) {
            value = stringValue
        } else if let boolValue = try? container.decode(Bool.self) {
            value = boolValue
        } else {
            value = ()
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        if let intValue = value as? Int {
            try container.encode(intValue)
        } else if let doubleValue = value as? Double {
            try container.encode(doubleValue)
        } else if let stringValue = value as? String {
            try container.encode(stringValue)
        } else if let boolValue = value as? Bool {
            try container.encode(boolValue)
        }
    }
}

// MARK: - API Response Models
struct APIError: Codable {
    let detail: String
}

struct SaveFoodLogResponse: Codable {
    let message: String
    let logId: String
    let achievements: [AchievementResponse]
    
    enum CodingKeys: String, CodingKey {
        case message
        case logId = "log_id"
        case achievements
    }
}

struct AchievementResponse: Codable {
    let name: String
    let description: String
    let points: Int
    let badge: String
}