import SwiftUI

struct MealAnalysisView: View {
    @EnvironmentObject var networkManager: NetworkManager
    @State private var selectedImage: UIImage?
    @State private var userInput = ""
    @State private var corrections = ""
    @State private var mealResponse: MealResponse?
    @State private var isAnalyzing = false
    @State private var showImagePicker = false
    @State private var imageSourceType: UIImagePickerController.SourceType = .camera
    @State private var showingActionSheet = false
    @State private var errorMessage: String?
    @State private var showingSaveOptions = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Header
                    VStack(spacing: 8) {
                        Text("Analyze Your Meal")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("Take a photo or describe your meal")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top)
                    
                    // Image Section
                    VStack(spacing: 16) {
                        if let selectedImage = selectedImage {
                            Image(uiImage: selectedImage)
                                .resizable()
                                .aspectRatio(contentMode: .fill)
                                .frame(height: 200)
                                .clipped()
                                .cornerRadius(16)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 16)
                                        .stroke(Color.green, lineWidth: 2)
                                )
                        } else {
                            Button(action: {
                                showingActionSheet = true
                            }) {
                                VStack(spacing: 16) {
                                    Image(systemName: "camera.fill")
                                        .font(.system(size: 40))
                                        .foregroundColor(.green)
                                    
                                    Text("Add Photo")
                                        .font(.headline)
                                        .foregroundColor(.green)
                                    
                                    Text("Take a photo or choose from library")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                .frame(height: 200)
                                .frame(maxWidth: .infinity)
                                .background(Color(.systemGray6))
                                .cornerRadius(16)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 16)
                                        .stroke(Color.green.opacity(0.3), lineWidth: 2, dash: [5])
                                )
                            }
                        }
                        
                        if selectedImage != nil {
                            Button("Change Photo") {
                                showingActionSheet = true
                            }
                            .font(.subheadline)
                            .foregroundColor(.green)
                        }
                    }
                    .padding(.horizontal)
                    
                    // Text Input Section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Describe Your Meal")
                            .font(.headline)
                        
                        TextField("e.g., Grilled chicken with rice and vegetables", text: $userInput, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(3...6)
                        
                        Text("Be as specific as possible for better analysis")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.horizontal)
                    
                    // Corrections Section
                    if mealResponse != nil {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Corrections (Optional)")
                                .font(.headline)
                            
                            TextField("Any corrections to the analysis?", text: $corrections, axis: .vertical)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .lineLimit(2...4)
                            
                            Text("Help improve accuracy by providing feedback")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(.horizontal)
                    }
                    
                    // Error Message
                    if let errorMessage = errorMessage {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                            .padding(.horizontal)
                    }
                    
                    // Analyze Button
                    Button(action: analyzeMeal) {
                        HStack {
                            if isAnalyzing {
                                ProgressView()
                                    .scaleEffect(0.8)
                                    .foregroundColor(.white)
                            }
                            
                            Text(mealResponse == nil ? "Analyze Meal" : "Re-analyze")
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
                    .disabled(isAnalyzing || userInput.isEmpty)
                    .padding(.horizontal)
                    
                    // Results Section
                    if let mealResponse = mealResponse {
                        MealResultsView(
                            mealResponse: mealResponse,
                            onSave: {
                                showingSaveOptions = true
                            }
                        )
                    }
                    
                    Spacer(minLength: 100)
                }
            }
            .navigationBarHidden(true)
        }
        .actionSheet(isPresented: $showingActionSheet) {
            ActionSheet(
                title: Text("Select Photo"),
                buttons: [
                    .default(Text("Camera")) {
                        imageSourceType = .camera
                        showImagePicker = true
                    },
                    .default(Text("Photo Library")) {
                        imageSourceType = .photoLibrary
                        showImagePicker = true
                    },
                    .cancel()
                ]
            )
        }
        .sheet(isPresented: $showImagePicker) {
            ImagePicker(image: $selectedImage, sourceType: imageSourceType)
        }
        .actionSheet(isPresented: $showingSaveOptions) {
            ActionSheet(
                title: Text("Save to Food Log"),
                message: Text("Choose meal type"),
                buttons: [
                    .default(Text("Breakfast")) { saveMeal(mealType: "breakfast") },
                    .default(Text("Lunch")) { saveMeal(mealType: "lunch") },
                    .default(Text("Dinner")) { saveMeal(mealType: "dinner") },
                    .default(Text("Snack")) { saveMeal(mealType: "snack") },
                    .cancel()
                ]
            )
        }
    }
    
    private func analyzeMeal() {
        Task {
            isAnalyzing = true
            errorMessage = nil
            
            do {
                var imageUrl: String? = nil
                
                // Upload image if selected
                if let selectedImage = selectedImage,
                   let imageData = selectedImage.jpegData(compressionQuality: 0.8) {
                    imageUrl = try await networkManager.uploadImage(imageData)
                }
                
                mealResponse = try await networkManager.analyzeMeal(
                    imageUrl: imageUrl,
                    userInput: userInput,
                    corrections: corrections.isEmpty ? nil : corrections
                )
            } catch {
                errorMessage = error.localizedDescription
            }
            
            isAnalyzing = false
        }
    }
    
    private func saveMeal(mealType: String) {
        guard let mealResponse = mealResponse else { return }
        
        Task {
            do {
                let foodLogItems = mealResponse.foods.map { food in
                    FoodLogItem(
                        name: food.name,
                        calories: Double(food.calories),
                        proteinG: food.proteinG,
                        carbsG: food.carbsG,
                        fatG: food.fatG,
                        micronutrients: nil
                    )
                }
                
                let _ = try await networkManager.saveFoodLog(
                    mealTime: mealType,
                    foods: foodLogItems,
                    totalCalories: Double(mealResponse.totalCalories)
                )
                
                // Show success message or navigate
                // Reset form
                selectedImage = nil
                userInput = ""
                corrections = ""
                self.mealResponse = nil
                
            } catch {
                errorMessage = "Failed to save meal: \(error.localizedDescription)"
            }
        }
    }
}

struct MealResultsView: View {
    let mealResponse: MealResponse
    let onSave: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header
            HStack {
                Text("Analysis Results")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Button("Save to Log", action: onSave)
                    .font(.subheadline)
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.green)
                    .cornerRadius(8)
            }
            
            // Meal Info
            VStack(alignment: .leading, spacing: 8) {
                Text(mealResponse.mealName)
                    .font(.headline)
                
                HStack {
                    Label(mealResponse.mealType.capitalized, systemImage: "clock")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Text("\(mealResponse.totalCalories) calories")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(.green)
                }
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)
            
            // Foods List
            VStack(alignment: .leading, spacing: 12) {
                Text("Food Items")
                    .font(.headline)
                
                ForEach(mealResponse.foods) { food in
                    FoodItemRow(food: food)
                }
            }
            
            // Analysis Method
            HStack {
                Image(systemName: mealResponse.analysisMethod == "vision" ? "eye.fill" : "text.bubble.fill")
                    .foregroundColor(.blue)
                
                Text("Analyzed using \(mealResponse.analysisMethod == "vision" ? "image recognition" : "text description")")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
        .padding(.horizontal)
    }
}

struct FoodItemRow: View {
    let food: Food
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(food.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                HStack(spacing: 16) {
                    MacroLabel(label: "P", value: food.proteinG, color: .blue)
                    MacroLabel(label: "C", value: food.carbsG, color: .orange)
                    MacroLabel(label: "F", value: food.fatG, color: .purple)
                }
            }
            
            Spacer()
            
            Text("\(food.calories) cal")
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(.green)
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
}

struct MacroLabel: View {
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
    }
}

#Preview {
    MealAnalysisView()
        .environmentObject(NetworkManager())
}