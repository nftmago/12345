import SwiftUI

struct FoodLogView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var foodLogs: [FoodLogResponse] = []
    @State private var isLoading = false
    @State private var selectedDate = Date()
    @State private var showingDatePicker = false
    
    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()
    
    private let displayDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter
    }()
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Date Picker Header
                VStack(spacing: 16) {
                    HStack {
                        Text("Food Log")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Spacer()
                        
                        Button(action: {
                            showingDatePicker = true
                        }) {
                            HStack {
                                Image(systemName: "calendar")
                                Text(displayDateFormatter.string(from: selectedDate))
                            }
                            .font(.subheadline)
                            .foregroundColor(.green)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color.green.opacity(0.1))
                            .cornerRadius(8)
                        }
                    }
                    
                    // Quick Date Navigation
                    HStack(spacing: 12) {
                        ForEach(recentDates, id: \.self) { date in
                            Button(action: {
                                selectedDate = date
                                loadFoodLogs()
                            }) {
                                Text(quickDateLabel(for: date))
                                    .font(.caption)
                                    .fontWeight(.medium)
                                    .foregroundColor(Calendar.current.isDate(date, inSameDayAs: selectedDate) ? .white : .green)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(
                                        Calendar.current.isDate(date, inSameDayAs: selectedDate) ? 
                                        Color.green : Color.green.opacity(0.1)
                                    )
                                    .cornerRadius(16)
                            }
                        }
                        
                        Spacer()
                    }
                }
                .padding()
                .background(Color(.systemBackground))
                
                Divider()
                
                // Content
                if isLoading {
                    Spacer()
                    ProgressView("Loading food logs...")
                    Spacer()
                } else if foodLogs.isEmpty {
                    EmptyLogView(date: selectedDate)
                } else {
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            // Daily Summary
                            DailySummaryCard(foodLogs: foodLogs)
                            
                            // Meal Groups
                            ForEach(groupedMeals.keys.sorted(), id: \.self) { mealType in
                                if let meals = groupedMeals[mealType] {
                                    MealGroupView(mealType: mealType, meals: meals)
                                }
                            }
                        }
                        .padding()
                        .padding(.bottom, 100)
                    }
                }
            }
            .navigationBarHidden(true)
            .sheet(isPresented: $showingDatePicker) {
                DatePickerSheet(selectedDate: $selectedDate) {
                    loadFoodLogs()
                }
            }
        }
        .onAppear {
            loadFoodLogs()
        }
        .onChange(of: selectedDate) { _ in
            loadFoodLogs()
        }
    }
    
    private var recentDates: [Date] {
        let calendar = Calendar.current
        return (0..<7).compactMap { daysAgo in
            calendar.date(byAdding: .day, value: -daysAgo, to: Date())
        }
    }
    
    private func quickDateLabel(for date: Date) -> String {
        let calendar = Calendar.current
        if calendar.isDateInToday(date) {
            return "Today"
        } else if calendar.isDateInYesterday(date) {
            return "Yesterday"
        } else {
            let formatter = DateFormatter()
            formatter.dateFormat = "MMM d"
            return formatter.string(from: date)
        }
    }
    
    private var groupedMeals: [String: [FoodLogResponse]] {
        Dictionary(grouping: foodLogs) { $0.mealTime }
    }
    
    private func loadFoodLogs() {
        Task {
            isLoading = true
            
            do {
                let dateString = dateFormatter.string(from: selectedDate)
                foodLogs = try await networkManager.getUserFoodLogs(dateFilter: dateString, limit: 50)
            } catch {
                print("Failed to load food logs: \(error)")
                foodLogs = []
            }
            
            isLoading = false
        }
    }
}

struct EmptyLogView: View {
    let date: Date
    
    var body: some View {
        VStack(spacing: 20) {
            Spacer()
            
            Image(systemName: "fork.knife.circle")
                .font(.system(size: 60))
                .foregroundColor(.gray)
            
            Text("No meals logged")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.primary)
            
            Text(Calendar.current.isDateInToday(date) ? 
                 "Start by analyzing your first meal of the day!" :
                 "No meals were logged on this date")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            if Calendar.current.isDateInToday(date) {
                Button("Analyze Meal") {
                    // Navigate to meal analysis
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding(.horizontal, 24)
                .padding(.vertical, 12)
                .background(Color.green)
                .cornerRadius(12)
            }
            
            Spacer()
        }
        .padding()
    }
}

struct DailySummaryCard: View {
    let foodLogs: [FoodLogResponse]
    
    private var totalCalories: Double {
        foodLogs.reduce(0) { $0 + $1.totalCalories }
    }
    
    private var mealCount: Int {
        foodLogs.count
    }
    
    var body: some View {
        VStack(spacing: 16) {
            HStack {
                Text("Daily Summary")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("\(mealCount) meals")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            HStack(spacing: 20) {
                VStack {
                    Text("\(Int(totalCalories))")
                        .font(.title)
                        .fontWeight(.bold)
                        .foregroundColor(.green)
                    
                    Text("Calories")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // You could add more summary stats here
                // like total protein, carbs, fat if you calculate them
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
}

struct MealGroupView: View {
    let mealType: String
    let meals: [FoodLogResponse]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: mealIcon)
                    .foregroundColor(.green)
                
                Text(mealType.capitalized)
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("\(Int(totalCalories)) cal")
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.green)
            }
            
            ForEach(meals) { meal in
                FoodLogEntryView(meal: meal)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
    }
    
    private var mealIcon: String {
        switch mealType.lowercased() {
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
    
    private var totalCalories: Double {
        meals.reduce(0) { $0 + $1.totalCalories }
    }
}

struct FoodLogEntryView: View {
    let meal: FoodLogResponse
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(timeString(from: meal.createdAt))
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text("\(Int(meal.totalCalories)) calories")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.green)
            }
            
            // Display food items if available
            if !meal.foods.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(Array(meal.foods.enumerated()), id: \.offset) { index, food in
                        if let name = food["name"]?.value as? String {
                            Text("• \(name)")
                                .font(.caption)
                                .foregroundColor(.primary)
                        }
                    }
                }
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
    
    private func timeString(from dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
        
        if let date = formatter.date(from: dateString) {
            let timeFormatter = DateFormatter()
            timeFormatter.timeStyle = .short
            return timeFormatter.string(from: date)
        }
        
        return "Unknown time"
    }
}

struct DatePickerSheet: View {
    @Binding var selectedDate: Date
    let onDateSelected: () -> Void
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        NavigationView {
            VStack {
                DatePicker(
                    "Select Date",
                    selection: $selectedDate,
                    in: ...Date(),
                    displayedComponents: .date
                )
                .datePickerStyle(GraphicalDatePickerStyle())
                .padding()
                
                Spacer()
            }
            .navigationTitle("Select Date")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarItems(
                leading: Button("Cancel") {
                    presentationMode.wrappedValue.dismiss()
                },
                trailing: Button("Done") {
                    onDateSelected()
                    presentationMode.wrappedValue.dismiss()
                }
            )
        }
    }
}

#Preview {
    FoodLogView()
        .environmentObject(NetworkManager())
}