import Foundation
import HealthKit

@MainActor
class HealthKitManager: ObservableObject {
    private let healthStore = HKHealthStore()
    @Published var isAuthorized = false
    
    private let typesToRead: Set<HKObjectType> = [
        HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!,
        HKObjectType.quantityType(forIdentifier: .basalEnergyBurned)!,
        HKObjectType.quantityType(forIdentifier: .stepCount)!,
        HKObjectType.quantityType(forIdentifier: .bodyMass)!,
        HKObjectType.quantityType(forIdentifier: .height)!
    ]
    
    private let typesToWrite: Set<HKSampleType> = [
        HKObjectType.quantityType(forIdentifier: .dietaryEnergyConsumed)!,
        HKObjectType.quantityType(forIdentifier: .dietaryProtein)!,
        HKObjectType.quantityType(forIdentifier: .dietaryCarbohydrates)!,
        HKObjectType.quantityType(forIdentifier: .dietaryFatTotal)!,
        HKObjectType.quantityType(forIdentifier: .dietaryFiber)!,
        HKObjectType.quantityType(forIdentifier: .dietarySugar)!,
        HKObjectType.quantityType(forIdentifier: .dietarySodium)!
    ]
    
    func requestAuthorization() async {
        guard HKHealthStore.isHealthDataAvailable() else {
            print("HealthKit is not available on this device")
            return
        }
        
        do {
            try await healthStore.requestAuthorization(toShare: typesToWrite, read: typesToRead)
            isAuthorized = true
        } catch {
            print("HealthKit authorization failed: \(error)")
            isAuthorized = false
        }
    }
    
    func saveMealToHealthKit(
        calories: Double,
        protein: Double,
        carbs: Double,
        fat: Double,
        mealName: String,
        date: Date = Date()
    ) async {
        guard isAuthorized else { return }
        
        var samples: [HKQuantitySample] = []
        
        // Calories
        if let caloriesType = HKQuantityType.quantityType(forIdentifier: .dietaryEnergyConsumed) {
            let caloriesQuantity = HKQuantity(unit: .kilocalorie(), doubleValue: calories)
            let caloriesSample = HKQuantitySample(
                type: caloriesType,
                quantity: caloriesQuantity,
                start: date,
                end: date,
                metadata: [HKMetadataKeyFoodType: mealName]
            )
            samples.append(caloriesSample)
        }
        
        // Protein
        if let proteinType = HKQuantityType.quantityType(forIdentifier: .dietaryProtein) {
            let proteinQuantity = HKQuantity(unit: .gram(), doubleValue: protein)
            let proteinSample = HKQuantitySample(
                type: proteinType,
                quantity: proteinQuantity,
                start: date,
                end: date,
                metadata: [HKMetadataKeyFoodType: mealName]
            )
            samples.append(proteinSample)
        }
        
        // Carbohydrates
        if let carbsType = HKQuantityType.quantityType(forIdentifier: .dietaryCarbohydrates) {
            let carbsQuantity = HKQuantity(unit: .gram(), doubleValue: carbs)
            let carbsSample = HKQuantitySample(
                type: carbsType,
                quantity: carbsQuantity,
                start: date,
                end: date,
                metadata: [HKMetadataKeyFoodType: mealName]
            )
            samples.append(carbsSample)
        }
        
        // Fat
        if let fatType = HKQuantityType.quantityType(forIdentifier: .dietaryFatTotal) {
            let fatQuantity = HKQuantity(unit: .gram(), doubleValue: fat)
            let fatSample = HKQuantitySample(
                type: fatType,
                quantity: fatQuantity,
                start: date,
                end: date,
                metadata: [HKMetadataKeyFoodType: mealName]
            )
            samples.append(fatSample)
        }
        
        // Save all samples
        do {
            try await healthStore.save(samples)
            print("Successfully saved meal data to HealthKit")
        } catch {
            print("Failed to save meal data to HealthKit: \(error)")
        }
    }
    
    func getTodaysCaloriesBurned() async -> Double {
        guard isAuthorized else { return 0 }
        
        guard let energyType = HKQuantityType.quantityType(forIdentifier: .activeEnergyBurned) else {
            return 0
        }
        
        let calendar = Calendar.current
        let startOfDay = calendar.startOfDay(for: Date())
        let endOfDay = calendar.date(byAdding: .day, value: 1, to: startOfDay)!
        
        let predicate = HKQuery.predicateForSamples(
            withStart: startOfDay,
            end: endOfDay,
            options: .strictStartDate
        )
        
        return await withCheckedContinuation { continuation in
            let query = HKStatisticsQuery(
                quantityType: energyType,
                quantitySamplePredicate: predicate,
                options: .cumulativeSum
            ) { _, result, error in
                if let error = error {
                    print("HealthKit query error: \(error)")
                    continuation.resume(returning: 0)
                    return
                }
                
                let calories = result?.sumQuantity()?.doubleValue(for: .kilocalorie()) ?? 0
                continuation.resume(returning: calories)
            }
            
            healthStore.execute(query)
        }
    }
    
    func getTodaysSteps() async -> Double {
        guard isAuthorized else { return 0 }
        
        guard let stepsType = HKQuantityType.quantityType(forIdentifier: .stepCount) else {
            return 0
        }
        
        let calendar = Calendar.current
        let startOfDay = calendar.startOfDay(for: Date())
        let endOfDay = calendar.date(byAdding: .day, value: 1, to: startOfDay)!
        
        let predicate = HKQuery.predicateForSamples(
            withStart: startOfDay,
            end: endOfDay,
            options: .strictStartDate
        )
        
        return await withCheckedContinuation { continuation in
            let query = HKStatisticsQuery(
                quantityType: stepsType,
                quantitySamplePredicate: predicate,
                options: .cumulativeSum
            ) { _, result, error in
                if let error = error {
                    print("HealthKit steps query error: \(error)")
                    continuation.resume(returning: 0)
                    return
                }
                
                let steps = result?.sumQuantity()?.doubleValue(for: .count()) ?? 0
                continuation.resume(returning: steps)
            }
            
            healthStore.execute(query)
        }
    }
}