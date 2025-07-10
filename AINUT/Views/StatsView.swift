import SwiftUI
import Charts

struct StatsView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var selectedTimeframe: TimeFrame = .week
    @State private var foodLogs: [FoodLogResponse] = []
    @State private var isLoading = false
    
    enum TimeFrame: String, CaseIterable {
        case week = "Week"
        case month = "Month"
        case year = "Year"
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Timeframe Selector
                    Picker("Timeframe", selection: $selectedTimeframe) {
                        ForEach(TimeFrame.allCases, id: \.self) { timeframe in
                            Text(timeframe.rawValue).tag(timeframe)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    .padding(.horizontal)
                    
                    if isLoading {
                        ProgressView("Loading stats...")
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else {
                        // Summary Cards
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 16) {
                            SummaryCard(
                                title: "Total Meals",
                                value: "\(foodLogs.count)",
                                icon: "fork.knife",
                                color: .green
                            )
                            
                            SummaryCard(
                                title: "Avg Calories",
                                value: "\(Int(averageCalories))",
                                icon: "flame.fill",
                                color: .orange
                            )
                            
                            SummaryCard(
                                title: "Protein",
                                value: "\(Int(totalProtein))g",
                                icon: "dumbbell.fill",
                                color: .blue
                            )
                            
                            SummaryCard(
                                title: "Streak",
                                value: "\(currentStreak) days",
                                icon: "calendar.badge.checkmark",
                                color: .purple
                            )
                        }
                        .padding(.horizontal)
                        
                        // Charts Section
                        VStack(spacing: 20) {
                            // Calories Chart
                            ChartCard(title: "Daily Calories") {
                                CaloriesChart(data: dailyCaloriesData)
                            }
                            
                            // Macros Chart
                            ChartCard(title: "Macro Distribution") {
                                MacrosChart(data: macroData)
                            }
                            
                            // Meal Types Chart
                            ChartCard(title: "Meal Types") {
                                MealTypesChart(data: mealTypeData)
                            }
                        }
                        .padding(.horizontal)
                    }
                    
                    Spacer(minLength: 100)
                }
                .padding(.vertical)
            }
            .navigationTitle("Statistics")
            .navigationBarTitleDisplayMode(.large)
            .refreshable {
                await loadData()
            }
        }
        .onAppear {
            Task {
                await loadData()
            }
        }
        .onChange(of: selectedTimeframe) { _ in
            Task {
                await loadData()
            }
        }
    }
    
    private var averageCalories: Double {
        guard !foodLogs.isEmpty else { return 0 }
        let total = foodLogs.reduce(0) { $0 + $1.totalCalories }
        return total / Double(foodLogs.count)
    }
    
    private var totalProtein: Double {
        foodLogs.reduce(0) { total, log in
            total + log.foods.reduce(0) { foodTotal, food in
                foodTotal + (food["protein_g"]?.value as? Double ?? 0)
            }
        }
    }
    
    private var currentStreak: Int {
        // Calculate consecutive days of logging
        let uniqueDates = Set(foodLogs.map { $0.dateString })
        return uniqueDates.count // Simplified calculation
    }
    
    private var dailyCaloriesData: [DailyCalories] {
        let grouped = Dictionary(grouping: foodLogs) { $0.dateString }
        return grouped.map { date, logs in
            DailyCalories(
                date: date,
                calories: logs.reduce(0) { $0 + $1.totalCalories }
            )
        }.sorted { $0.date < $1.date }
    }
    
    private var macroData: [MacroData] {
        let totalProtein = foodLogs.reduce(0) { total, log in
            total + log.foods.reduce(0) { $0 + (($1["protein_g"]?.value as? Double) ?? 0) }
        }
        let totalCarbs = foodLogs.reduce(0) { total, log in
            total + log.foods.reduce(0) { $0 + (($1["carbs_g"]?.value as? Double) ?? 0) }
        }
        let totalFat = foodLogs.reduce(0) { total, log in
            total + log.foods.reduce(0) { $0 + (($1["fat_g"]?.value as? Double) ?? 0) }
        }
        
        return [
            MacroData(name: "Protein", value: totalProtein, color: .blue),
            MacroData(name: "Carbs", value: totalCarbs, color: .orange),
            MacroData(name: "Fat", value: totalFat, color: .purple)
        ]
    }
    
    private var mealTypeData: [MealTypeData] {
        let grouped = Dictionary(grouping: foodLogs) { $0.mealTime }
        return grouped.map { mealType, logs in
            MealTypeData(mealType: mealType.capitalized, count: logs.count)
        }.sorted { $0.count > $1.count }
    }
    
    private func loadData() async {
        guard let userId = networkManager.currentUser?.username else { return }
        
        isLoading = true
        
        do {
            // Load data based on timeframe
            let limit = selectedTimeframe == .year ? 365 : (selectedTimeframe == .month ? 30 : 7)
            foodLogs = try await networkManager.getUserFoodLogs(limit: limit)
        } catch {
            print("Failed to load stats data: \(error)")
        }
        
        isLoading = false
    }
}

struct SummaryCard: View {
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

struct ChartCard<Content: View>: View {
    let title: String
    let content: Content
    
    init(title: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.content = content()
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(title)
                .font(.headline)
                .fontWeight(.semibold)
            
            content
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
    }
}

struct CaloriesChart: View {
    let data: [DailyCalories]
    
    var body: some View {
        VStack {
            if #available(iOS 16.0, *) {
                Chart(data) { item in
                    LineMark(
                        x: .value("Date", item.date),
                        y: .value("Calories", item.calories)
                    )
                    .foregroundStyle(.green)
                    .lineStyle(StrokeStyle(lineWidth: 3))
                }
                .frame(height: 200)
            } else {
                // Fallback for iOS 15
                Text("Chart requires iOS 16+")
                    .foregroundColor(.secondary)
                    .frame(height: 200)
            }
        }
    }
}

struct MacrosChart: View {
    let data: [MacroData]
    
    var body: some View {
        VStack {
            if #available(iOS 16.0, *) {
                Chart(data) { item in
                    SectorMark(
                        angle: .value("Value", item.value),
                        innerRadius: .ratio(0.5),
                        angularInset: 2
                    )
                    .foregroundStyle(item.color)
                }
                .frame(height: 200)
            } else {
                // Fallback for iOS 15
                HStack {
                    ForEach(data, id: \.name) { item in
                        VStack {
                            Circle()
                                .fill(item.color)
                                .frame(width: 20, height: 20)
                            Text(item.name)
                                .font(.caption)
                            Text("\(Int(item.value))g")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .frame(height: 200)
            }
        }
    }
}

struct MealTypesChart: View {
    let data: [MealTypeData]
    
    var body: some View {
        VStack {
            if #available(iOS 16.0, *) {
                Chart(data) { item in
                    BarMark(
                        x: .value("Meal Type", item.mealType),
                        y: .value("Count", item.count)
                    )
                    .foregroundStyle(.blue)
                }
                .frame(height: 200)
            } else {
                // Fallback for iOS 15
                VStack(spacing: 8) {
                    ForEach(data, id: \.mealType) { item in
                        HStack {
                            Text(item.mealType)
                                .font(.subheadline)
                            Spacer()
                            Text("\(item.count)")
                                .font(.subheadline)
                                .fontWeight(.medium)
                        }
                    }
                }
                .frame(height: 200)
            }
        }
    }
}

// Data Models
struct DailyCalories: Identifiable {
    let id = UUID()
    let date: String
    let calories: Double
}

struct MacroData: Identifiable {
    let id = UUID()
    let name: String
    let value: Double
    let color: Color
}

struct MealTypeData: Identifiable {
    let id = UUID()
    let mealType: String
    let count: Int
}

#Preview {
    StatsView()
        .environmentObject(NetworkManager())
}