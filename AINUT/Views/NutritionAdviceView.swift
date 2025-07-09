import SwiftUI

struct NutritionAdviceView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var nutritionAdvice: NutritionistResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var selectedTimeframe: TimeFrame = .today
    @State private var foodLogs: [FoodLogResponse] = []
    
    enum TimeFrame: String, CaseIterable {
        case today = "Today"
        case week = "This Week"
        
        var days: Int {
            switch self {
            case .today: return 1
            case .week: return 7
            }
        }
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Header
                    VStack(spacing: 8) {
                        Text("Nutrition Advice")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("Get personalized nutrition insights")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top)
                    
                    // Timeframe Selector
                    Picker("Timeframe", selection: $selectedTimeframe) {
                        ForEach(TimeFrame.allCases, id: \.self) { timeframe in
                            Text(timeframe.rawValue).tag(timeframe)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    .padding(.horizontal)
                    .onChange(of: selectedTimeframe) { _ in
                        loadAdvice()
                    }
                    
                    // Get Advice Button
                    Button(action: loadAdvice) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .scaleEffect(0.8)
                                    .foregroundColor(.white)
                            }
                            
                            Text("Get Nutrition Advice")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(
                            LinearGradient(
                                colors: [.green, .green.opacity(0.8)],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .disabled(isLoading)
                    .padding(.horizontal)
                    
                    // Error Message
                    if let errorMessage = errorMessage {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                            .padding(.horizontal)
                    }
                    
                    // Advice Content
                    if let advice = nutritionAdvice {
                        NutritionAdviceContent(advice: advice)
                    } else if !isLoading {
                        EmptyAdviceView()
                    }
                    
                    Spacer(minLength: 100)
                }
            }
            .navigationBarHidden(true)
            .refreshable {
                loadAdvice()
            }
        }
        .onAppear {
            loadAdvice()
        }
    }
    
    private func loadAdvice() {
        Task {
            isLoading = true
            errorMessage = nil
            
            do {
                // Load recent food logs
                await loadRecentFoodLogs()
                
                // Convert food logs to FoodLogItems
                let foodLogItems = convertToFoodLogItems(foodLogs)
                
                // Default daily targets (you might want to get these from user profile)
                let dailyTargets: [String: Double] = [
                    "calories": 2000,
                    "protein_g": 120,
                    "carbs_g": 250,
                    "fat_g": 70
                ]
                
                // Get personalized advice if user is authenticated
                if networkManager.isAuthenticated {
                    nutritionAdvice = try await networkManager.getPersonalizedNutritionAdvice(
                        foodLog: foodLogItems,
                        dailyTargets: dailyTargets
                    )
                } else {
                    nutritionAdvice = try await networkManager.getNutritionAdvice(
                        foodLog: foodLogItems,
                        dailyTargets: dailyTargets
                    )
                }
                
            } catch {
                errorMessage = error.localizedDescription
            }
            
            isLoading = false
        }
    }
    
    private func loadRecentFoodLogs() async {
        do {
            let dateFormatter = DateFormatter()
            dateFormatter.dateFormat = "yyyy-MM-dd"
            
            if selectedTimeframe == .today {
                let today = dateFormatter.string(from: Date())
                foodLogs = try await networkManager.getUserFoodLogs(dateFilter: today, limit: 50)
            } else {
                foodLogs = try await networkManager.getUserFoodLogs(limit: 50)
                // Filter to last week
                let weekAgo = Calendar.current.date(byAdding: .day, value: -7, to: Date()) ?? Date()
                let weekAgoString = dateFormatter.string(from: weekAgo)
                foodLogs = foodLogs.filter { $0.dateString >= weekAgoString }
            }
        } catch {
            print("Failed to load food logs: \(error)")
            foodLogs = []
        }
    }
    
    private func convertToFoodLogItems(_ logs: [FoodLogResponse]) -> [FoodLogItem] {
        var items: [FoodLogItem] = []
        
        for log in logs {
            for food in log.foods {
                if let name = food["name"]?.value as? String,
                   let calories = food["calories"]?.value as? Double {
                    
                    let protein = food["protein_g"]?.value as? Double ?? 0
                    let carbs = food["carbs_g"]?.value as? Double ?? 0
                    let fat = food["fat_g"]?.value as? Double ?? 0
                    
                    let item = FoodLogItem(
                        name: name,
                        calories: calories,
                        proteinG: protein,
                        carbsG: carbs,
                        fatG: fat,
                        micronutrients: nil
                    )
                    items.append(item)
                }
            }
        }
        
        return items
    }
}

struct NutritionAdviceContent: View {
    let advice: NutritionistResponse
    
    var body: some View {
        VStack(spacing: 20) {
            // Overall Summary
            VStack(alignment: .leading, spacing: 12) {
                Text("Overall Summary")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Text(advice.overallSummary)
                    .font(.body)
                    .foregroundColor(.primary)
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(16)
            .padding(.horizontal)
            
            // Safety Notes
            if !advice.safetyNotes.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.orange)
                        Text("Important Notes")
                            .font(.headline)
                            .fontWeight(.semibold)
                    }
                    
                    ForEach(advice.safetyNotes, id: \.self) { note in
                        HStack(alignment: .top) {
                            Text("•")
                                .foregroundColor(.orange)
                            Text(note)
                                .font(.body)
                                .foregroundColor(.primary)
                        }
                    }
                }
                .padding()
                .background(Color.orange.opacity(0.1))
                .cornerRadius(16)
                .padding(.horizontal)
            }
            
            // Nutrients to Focus On
            if !advice.nutrientsToFocusOn.isEmpty {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Focus Areas")
                        .font(.headline)
                        .fontWeight(.semibold)
                        .padding(.horizontal)
                    
                    ForEach(advice.nutrientsToFocusOn) { nutrient in
                        NutrientAdviceCard(nutrient: nutrient)
                    }
                }
            }
            
            // Achievements
            if !advice.achievements.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "star.fill")
                            .foregroundColor(.yellow)
                        Text("Achievements")
                            .font(.headline)
                            .fontWeight(.semibold)
                    }
                    
                    ForEach(advice.achievements, id: \.self) { achievement in
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            Text(achievement)
                                .font(.body)
                                .foregroundColor(.primary)
                        }
                    }
                }
                .padding()
                .background(Color.green.opacity(0.1))
                .cornerRadius(16)
                .padding(.horizontal)
            }
            
            // Tips
            if !advice.tips.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "lightbulb.fill")
                            .foregroundColor(.blue)
                        Text("Tips")
                            .font(.headline)
                            .fontWeight(.semibold)
                    }
                    
                    ForEach(advice.tips, id: \.self) { tip in
                        HStack(alignment: .top) {
                            Text("💡")
                            Text(tip)
                                .font(.body)
                                .foregroundColor(.primary)
                        }
                    }
                }
                .padding()
                .background(Color.blue.opacity(0.1))
                .cornerRadius(16)
                .padding(.horizontal)
            }
            
            // Personalized Insights
            if let insights = advice.personalizedInsights, !insights.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "person.fill")
                            .foregroundColor(.purple)
                        Text("Personal Insights")
                            .font(.headline)
                            .fontWeight(.semibold)
                    }
                    
                    ForEach(insights, id: \.self) { insight in
                        HStack(alignment: .top) {
                            Text("✨")
                            Text(insight)
                                .font(.body)
                                .foregroundColor(.primary)
                        }
                    }
                }
                .padding()
                .background(Color.purple.opacity(0.1))
                .cornerRadius(16)
                .padding(.horizontal)
            }
        }
    }
}

struct NutrientAdviceCard: View {
    let nutrient: NutrientAdvice
    @State private var isExpanded = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            Button(action: {
                withAnimation(.easeInOut(duration: 0.3)) {
                    isExpanded.toggle()
                }
            }) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(nutrient.nutrient.capitalized)
                            .font(.headline)
                            .fontWeight(.semibold)
                            .foregroundColor(.primary)
                        
                        HStack {
                            Text("\(nutrient.currentIntake, specifier: "%.1f") / \(nutrient.target, specifier: "%.1f")")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            
                            if nutrient.deficit > 0 {
                                Text("(\(nutrient.deficit, specifier: "%.1f") needed)")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                            }
                        }
                    }
                    
                    Spacer()
                    
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .foregroundColor(.green)
                }
            }
            .buttonStyle(PlainButtonStyle())
            
            // Progress Bar
            ProgressView(value: min(nutrient.currentIntake / nutrient.target, 1.0))
                .progressViewStyle(LinearProgressViewStyle(tint: progressColor))
                .scaleEffect(x: 1, y: 2, anchor: .center)
            
            if isExpanded {
                VStack(alignment: .leading, spacing: 16) {
                    // Why Important
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Why it's important:")
                            .font(.subheadline)
                            .fontWeight(.medium)
                        
                        Text(nutrient.whyImportant)
                            .font(.body)
                            .foregroundColor(.secondary)
                    }
                    
                    // Suggestions
                    if !nutrient.suggestions.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Meal Suggestions:")
                                .font(.subheadline)
                                .fontWeight(.medium)
                            
                            ForEach(nutrient.suggestions) { suggestion in
                                FoodSuggestionCard(suggestion: suggestion)
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
        .padding(.horizontal)
    }
    
    private var progressColor: Color {
        let percentage = nutrient.currentIntake / nutrient.target
        if percentage >= 0.8 {
            return .green
        } else if percentage >= 0.5 {
            return .orange
        } else {
            return .red
        }
    }
}

struct FoodSuggestionCard: View {
    let suggestion: FoodSuggestion
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(suggestion.mealIdea)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Text("\(Int(suggestion.totalCalories)) cal")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.green)
            }
            
            Text(suggestion.description)
                .font(.caption)
                .foregroundColor(.secondary)
            
            HStack {
                MacroTag(label: "P", value: suggestion.proteinProvided, color: .blue)
                MacroTag(label: "C", value: suggestion.carbsProvided, color: .orange)
                MacroTag(label: "F", value: suggestion.fatProvided, color: .purple)
                
                Spacer()
                
                if suggestion.easyToMake {
                    Text("Easy to make")
                        .font(.caption2)
                        .foregroundColor(.green)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(4)
                }
            }
            
            Text(suggestion.whyPerfect)
                .font(.caption)
                .foregroundColor(.green)
                .italic()
        }
        .padding(12)
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct MacroTag: View {
    let label: String
    let value: Double
    let color: Color
    
    var body: some View {
        HStack(spacing: 2) {
            Text(label)
                .font(.caption2)
                .fontWeight(.bold)
                .foregroundColor(color)
            
            Text("\(value, specifier: "%.1f")g")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 2)
        .background(color.opacity(0.1))
        .cornerRadius(4)
    }
}

struct EmptyAdviceView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "heart.text.square")
                .font(.system(size: 60))
                .foregroundColor(.gray)
            
            Text("No Advice Available")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.primary)
            
            Text("Log some meals first to get personalized nutrition advice")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}

#Preview {
    NutritionAdviceView()
        .environmentObject(NetworkManager())
}