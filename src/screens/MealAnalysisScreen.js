import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Image,
  Alert,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../config/api';

export default function MealAnalysisScreen() {
  const { user, token } = useAuth();
  const [selectedImage, setSelectedImage] = useState(null);
  const [userInput, setUserInput] = useState('');
  const [mealResult, setMealResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showSaveOptions, setShowSaveOptions] = useState(false);

  const pickImage = async (useCamera = false) => {
    try {
      const result = useCamera
        ? await ImagePicker.launchCameraAsync({
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            allowsEditing: true,
            aspect: [4, 3],
            quality: 0.8,
          })
        : await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            allowsEditing: true,
            aspect: [4, 3],
            quality: 0.8,
          });

      if (!result.canceled) {
        setSelectedImage(result.assets[0]);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const showImagePicker = () => {
    Alert.alert(
      'Select Photo',
      'Choose how you want to add a photo',
      [
        { text: 'Camera', onPress: () => pickImage(true) },
        { text: 'Photo Library', onPress: () => pickImage(false) },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  const analyzeMeal = async () => {
    if (!userInput.trim()) {
      Alert.alert('Error', 'Please describe your meal');
      return;
    }

    setIsAnalyzing(true);

    try {
      let imageUrl = null;

      // Upload image if selected
      if (selectedImage) {
        const formData = new FormData();
        formData.append('file', {
          uri: selectedImage.uri,
          type: 'image/jpeg',
          name: 'meal.jpg',
        });
        formData.append('image_type', 'meal');

        const uploadResponse = await fetch(`${API_BASE_URL}/upload-user-image`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
          body: formData,
        });

        if (uploadResponse.ok) {
          const uploadData = await uploadResponse.json();
          imageUrl = uploadData.url;
        }
      }

      // Analyze meal
      const analysisData = {
        user_input: userInput,
        image_url: imageUrl,
      };

      const result = await apiRequest('/ai/analyze-meal', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(analysisData),
      });

      setMealResult(result);
      setShowSaveOptions(true);
    } catch (error) {
      Alert.alert('Error', 'Failed to analyze meal. Please try again.');
      console.error('Analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const saveMeal = async (mealType) => {
    if (!mealResult) return;

    try {
      const today = new Date().toISOString().split('T')[0];
      
      const saveData = {
        user_id: user.username,
        date_string: today,
        meal_time: mealType,
        foods: mealResult.foods.map(food => ({
          name: food.name,
          calories: food.calories,
          protein_g: food.protein_g,
          carbs_g: food.carbs_g,
          fat_g: food.fat_g,
        })),
        total_calories: mealResult.total_calories,
      };

      await apiRequest('/food-logs', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(saveData),
      });

      Alert.alert('Success', 'Meal saved to your food log!');
      
      // Reset form
      setSelectedImage(null);
      setUserInput('');
      setMealResult(null);
      setShowSaveOptions(false);
    } catch (error) {
      Alert.alert('Error', 'Failed to save meal');
      console.error('Save error:', error);
    }
  };

  const showSaveMealOptions = () => {
    Alert.alert(
      'Save to Food Log',
      'Choose meal type',
      [
        { text: 'Breakfast', onPress: () => saveMeal('breakfast') },
        { text: 'Lunch', onPress: () => saveMeal('lunch') },
        { text: 'Dinner', onPress: () => saveMeal('dinner') },
        { text: 'Snack', onPress: () => saveMeal('snack') },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Analyze Your Meal</Text>
        <Text style={styles.subtitle}>Take a photo or describe your meal</Text>
      </View>

      {/* Image Section */}
      <View style={styles.section}>
        {selectedImage ? (
          <View style={styles.imageContainer}>
            <Image source={{ uri: selectedImage.uri }} style={styles.selectedImage} />
            <TouchableOpacity style={styles.changeImageButton} onPress={showImagePicker}>
              <Text style={styles.changeImageText}>Change Photo</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <TouchableOpacity style={styles.imagePicker} onPress={showImagePicker}>
            <Ionicons name="camera" size={40} color="#33B852" />
            <Text style={styles.imagePickerTitle}>Add Photo</Text>
            <Text style={styles.imagePickerSubtitle}>Take a photo or choose from library</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Text Input Section */}
      <View style={styles.section}>
        <Text style={styles.inputLabel}>Describe Your Meal</Text>
        <TextInput
          style={styles.textInput}
          placeholder="e.g., Grilled chicken with rice and vegetables"
          value={userInput}
          onChangeText={setUserInput}
          multiline
          numberOfLines={4}
        />
        <Text style={styles.inputHint}>Be as specific as possible for better analysis</Text>
      </View>

      {/* Analyze Button */}
      <TouchableOpacity 
        style={[styles.analyzeButton, (!userInput.trim() || isAnalyzing) && styles.disabledButton]}
        onPress={analyzeMeal}
        disabled={!userInput.trim() || isAnalyzing}
      >
        <LinearGradient
          colors={['#33B852', '#2A9644']}
          style={styles.gradient}
        >
          {isAnalyzing ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.analyzeButtonText}>
              {mealResult ? 'Re-analyze' : 'Analyze Meal'}
            </Text>
          )}
        </LinearGradient>
      </TouchableOpacity>

      {/* Results Section */}
      {mealResult && (
        <View style={styles.resultsSection}>
          <View style={styles.resultsHeader}>
            <Text style={styles.resultsTitle}>Analysis Results</Text>
            <TouchableOpacity style={styles.saveButton} onPress={showSaveMealOptions}>
              <Text style={styles.saveButtonText}>Save to Log</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.mealInfo}>
            <Text style={styles.mealName}>{mealResult.meal_name}</Text>
            <View style={styles.mealMeta}>
              <Text style={styles.mealType}>{mealResult.meal_type.toUpperCase()}</Text>
              <Text style={styles.totalCalories}>{mealResult.total_calories} calories</Text>
            </View>
          </View>

          <Text style={styles.foodsTitle}>Food Items</Text>
          {mealResult.foods.map((food, index) => (
            <View key={index} style={styles.foodItem}>
              <View style={styles.foodHeader}>
                <Text style={styles.foodName}>{food.name}</Text>
                <Text style={styles.foodCalories}>{food.calories} cal</Text>
              </View>
              <View style={styles.macros}>
                <View style={styles.macro}>
                  <Text style={styles.macroLabel}>P</Text>
                  <Text style={styles.macroValue}>{food.protein_g.toFixed(1)}g</Text>
                </View>
                <View style={styles.macro}>
                  <Text style={styles.macroLabel}>C</Text>
                  <Text style={styles.macroValue}>{food.carbs_g.toFixed(1)}g</Text>
                </View>
                <View style={styles.macro}>
                  <Text style={styles.macroLabel}>F</Text>
                  <Text style={styles.macroValue}>{food.fat_g.toFixed(1)}g</Text>
                </View>
              </View>
            </View>
          ))}

          <View style={styles.analysisMethod}>
            <Ionicons 
              name={mealResult.analysis_method === 'vision' ? 'eye' : 'text'} 
              size={16} 
              color="#666" 
            />
            <Text style={styles.analysisMethodText}>
              Analyzed using {mealResult.analysis_method === 'vision' ? 'image recognition' : 'text description'}
            </Text>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    padding: 20,
    paddingTop: 60,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 5,
  },
  section: {
    marginHorizontal: 20,
    marginBottom: 20,
  },
  imagePicker: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 40,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#33B852',
    borderStyle: 'dashed',
  },
  imagePickerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#33B852',
    marginTop: 10,
  },
  imagePickerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  imageContainer: {
    alignItems: 'center',
  },
  selectedImage: {
    width: '100%',
    height: 200,
    borderRadius: 15,
  },
  changeImageButton: {
    marginTop: 10,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#33B852',
    borderRadius: 8,
  },
  changeImageText: {
    color: 'white',
    fontWeight: 'bold',
  },
  inputLabel: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  textInput: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    fontSize: 16,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  inputHint: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
  },
  analyzeButton: {
    marginHorizontal: 20,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 20,
  },
  disabledButton: {
    opacity: 0.6,
  },
  gradient: {
    paddingVertical: 15,
    alignItems: 'center',
  },
  analyzeButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  resultsSection: {
    backgroundColor: 'white',
    margin: 20,
    borderRadius: 15,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  saveButton: {
    backgroundColor: '#33B852',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 8,
  },
  saveButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  mealInfo: {
    marginBottom: 20,
  },
  mealName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  mealMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 5,
  },
  mealType: {
    fontSize: 14,
    color: '#666',
  },
  totalCalories: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#33B852',
  },
  foodsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  foodItem: {
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
  },
  foodHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  foodName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  foodCalories: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#33B852',
  },
  macros: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  macro: {
    alignItems: 'center',
  },
  macroLabel: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#666',
  },
  macroValue: {
    fontSize: 14,
    color: '#333',
    marginTop: 2,
  },
  analysisMethod: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 15,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  analysisMethodText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 5,
  },
});