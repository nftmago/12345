import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../config/api';

export default function NutritionAdviceScreen() {
  const { user, token } = useAuth();
  const [advice, setAdvice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTimeframe, setSelectedTimeframe] = useState('today');

  useEffect(() => {
    loadAdvice();
  }, [selectedTimeframe]);

  const loadAdvice = async () => {
    setLoading(true);
    try {
      // Get recent food logs
      const dateFilter = selectedTimeframe === 'today' 
        ? new Date().toISOString().split('T')[0]
        : null;
      
      const foodLogsResponse = await apiRequest(
        `/users/${user.username}/food-logs${dateFilter ? `?date_filter=${dateFilter}` : '?limit=50'}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      // Convert food logs to the format expected by the API
      const foodLogItems = [];
      foodLogsResponse.forEach(log => {
        if (log.foods) {
          log.foods.forEach(food => {
            foodLogItems.push({
              name: food.name || 'Unknown food',
              calories: food.calories || 0,
              protein_g: food.protein_g || 0,
              carbs_g: food.carbs_g || 0,
              fat_g: food.fat_g || 0,
            });
          });
        }
      });

      // Default daily targets
      const dailyTargets = {
        calories: 2000,
        protein_g: 120,
        carbs_g: 250,
        fat_g: 70,
      };

      // Get personalized advice if user is authenticated
      const adviceResponse = await apiRequest('/ai/personalized-nutrition-advice', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: user.username,
          food_log: foodLogItems,
          daily_targets: dailyTargets,
        }),
      });

      setAdvice(adviceResponse);
    } catch (error) {
      console.error('Error loading advice:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadAdvice();
    setRefreshing(false);
  };

  const NutrientCard = ({ nutrient }) => {
    const progressPercentage = Math.min((nutrient.current_intake / nutrient.target) * 100, 100);
    const progressColor = progressPercentage >= 80 ? '#33B852' : progressPercentage >= 50 ? '#F39C12' : '#E74C3C';

    return (
      <View style={styles.nutrientCard}>
        <View style={styles.nutrientHeader}>
          <Text style={styles.nutrientName}>{nutrient.nutrient.toUpperCase()}</Text>
          <Text style={styles.nutrientValues}>
            {nutrient.current_intake.toFixed(1)} / {nutrient.target.toFixed(1)}
          </Text>
        </View>

        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View 
              style={[
                styles.progressFill, 
                { width: `${progressPercentage}%`, backgroundColor: progressColor }
              ]} 
            />
          </View>
          <Text style={styles.progressText}>{progressPercentage.toFixed(0)}%</Text>
        </View>

        {nutrient.deficit > 0 && (
          <Text style={styles.deficitText}>
            Need {nutrient.deficit.toFixed(1)}g more
          </Text>
        )}

        <Text style={styles.whyImportant}>{nutrient.why_important}</Text>

        {nutrient.suggestions && nutrient.suggestions.length > 0 && (
          <View style={styles.suggestionsContainer}>
            <Text style={styles.suggestionsTitle}>Meal Suggestions:</Text>
            {nutrient.suggestions.slice(0, 2).map((suggestion, index) => (
              <View key={index} style={styles.suggestionCard}>
                <Text style={styles.suggestionName}>{suggestion.meal_idea}</Text>
                <Text style={styles.suggestionDescription}>{suggestion.description}</Text>
                <View style={styles.suggestionMacros}>
                  <Text style={styles.suggestionCalories}>{suggestion.total_calories} cal</Text>
                  <Text style={styles.suggestionProtein}>P: {suggestion.protein_provided}g</Text>
                </View>
                <Text style={styles.whyPerfect}>{suggestion.why_perfect}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Nutrition Advice</Text>
        <Text style={styles.subtitle}>Get personalized nutrition insights</Text>
      </View>

      {/* Timeframe Selector */}
      <View style={styles.timeframeContainer}>
        <TouchableOpacity
          style={[styles.timeframeButton, selectedTimeframe === 'today' && styles.activeTimeframe]}
          onPress={() => setSelectedTimeframe('today')}
        >
          <Text style={[styles.timeframeText, selectedTimeframe === 'today' && styles.activeTimeframeText]}>
            Today
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.timeframeButton, selectedTimeframe === 'week' && styles.activeTimeframe]}
          onPress={() => setSelectedTimeframe('week')}
        >
          <Text style={[styles.timeframeText, selectedTimeframe === 'week' && styles.activeTimeframeText]}>
            This Week
          </Text>
        </TouchableOpacity>
      </View>

      {/* Get Advice Button */}
      <TouchableOpacity style={styles.adviceButton} onPress={loadAdvice} disabled={loading}>
        <LinearGradient colors={['#33B852', '#2A9644']} style={styles.gradient}>
          {loading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.adviceButtonText}>Get Nutrition Advice</Text>
          )}
        </LinearGradient>
      </TouchableOpacity>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {advice ? (
          <View style={styles.adviceContainer}>
            {/* Overall Summary */}
            <View style={styles.summaryCard}>
              <Text style={styles.summaryTitle}>Overall Summary</Text>
              <Text style={styles.summaryText}>{advice.overall_summary}</Text>
            </View>

            {/* Safety Notes */}
            {advice.safety_notes && advice.safety_notes.length > 0 && (
              <View style={styles.safetyCard}>
                <View style={styles.safetyHeader}>
                  <Ionicons name="warning" size={20} color="#F39C12" />
                  <Text style={styles.safetyTitle}>Important Notes</Text>
                </View>
                {advice.safety_notes.map((note, index) => (
                  <Text key={index} style={styles.safetyNote}>• {note}</Text>
                ))}
              </View>
            )}

            {/* Nutrients to Focus On */}
            {advice.nutrients_to_focus_on && advice.nutrients_to_focus_on.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Focus Areas</Text>
                {advice.nutrients_to_focus_on.map((nutrient, index) => (
                  <NutrientCard key={index} nutrient={nutrient} />
                ))}
              </View>
            )}

            {/* Achievements */}
            {advice.achievements && advice.achievements.length > 0 && (
              <View style={styles.achievementsCard}>
                <View style={styles.achievementsHeader}>
                  <Ionicons name="trophy" size={20} color="#F39C12" />
                  <Text style={styles.achievementsTitle}>Achievements</Text>
                </View>
                {advice.achievements.map((achievement, index) => (
                  <View key={index} style={styles.achievementItem}>
                    <Ionicons name="checkmark-circle" size={16} color="#33B852" />
                    <Text style={styles.achievementText}>{achievement}</Text>
                  </View>
                ))}
              </View>
            )}

            {/* Tips */}
            {advice.tips && advice.tips.length > 0 && (
              <View style={styles.tipsCard}>
                <View style={styles.tipsHeader}>
                  <Ionicons name="bulb" size={20} color="#4A90E2" />
                  <Text style={styles.tipsTitle}>Tips</Text>
                </View>
                {advice.tips.map((tip, index) => (
                  <Text key={index} style={styles.tipText}>💡 {tip}</Text>
                ))}
              </View>
            )}

            {/* Personalized Insights */}
            {advice.personalized_insights && advice.personalized_insights.length > 0 && (
              <View style={styles.insightsCard}>
                <View style={styles.insightsHeader}>
                  <Ionicons name="person" size={20} color="#9B59B6" />
                  <Text style={styles.insightsTitle}>Personal Insights</Text>
                </View>
                {advice.personalized_insights.map((insight, index) => (
                  <Text key={index} style={styles.insightText}>✨ {insight}</Text>
                ))}
              </View>
            )}
          </View>
        ) : !loading && (
          <View style={styles.emptyState}>
            <Ionicons name="heart-outline" size={60} color="#ccc" />
            <Text style={styles.emptyTitle}>No Advice Available</Text>
            <Text style={styles.emptyText}>
              Log some meals first to get personalized nutrition advice
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
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
  timeframeContainer: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginBottom: 20,
    backgroundColor: '#f0f0f0',
    borderRadius: 10,
    padding: 4,
  },
  timeframeButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  activeTimeframe: {
    backgroundColor: '#33B852',
  },
  timeframeText: {
    fontSize: 16,
    color: '#666',
  },
  activeTimeframeText: {
    color: 'white',
    fontWeight: 'bold',
  },
  adviceButton: {
    marginHorizontal: 20,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 20,
  },
  gradient: {
    paddingVertical: 15,
    alignItems: 'center',
  },
  adviceButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
  },
  adviceContainer: {
    padding: 20,
  },
  summaryCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  summaryText: {
    fontSize: 16,
    color: '#333',
    lineHeight: 24,
  },
  safetyCard: {
    backgroundColor: '#FFF3CD',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
  },
  safetyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  safetyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#856404',
    marginLeft: 8,
  },
  safetyNote: {
    fontSize: 14,
    color: '#856404',
    marginBottom: 5,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  nutrientCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  nutrientHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  nutrientName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  nutrientValues: {
    fontSize: 14,
    color: '#666',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  progressBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    marginRight: 10,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 12,
    color: '#666',
    minWidth: 35,
  },
  deficitText: {
    fontSize: 14,
    color: '#E74C3C',
    marginBottom: 10,
  },
  whyImportant: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
  },
  suggestionsContainer: {
    marginTop: 10,
  },
  suggestionsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  suggestionCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
  },
  suggestionName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  suggestionDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  suggestionMacros: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  suggestionCalories: {
    fontSize: 12,
    color: '#33B852',
    fontWeight: 'bold',
    marginRight: 15,
  },
  suggestionProtein: {
    fontSize: 12,
    color: '#4A90E2',
    fontWeight: 'bold',
  },
  whyPerfect: {
    fontSize: 12,
    color: '#33B852',
    fontStyle: 'italic',
  },
  achievementsCard: {
    backgroundColor: '#D4EDDA',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
  },
  achievementsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  achievementsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#155724',
    marginLeft: 8,
  },
  achievementItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
  },
  achievementText: {
    fontSize: 14,
    color: '#155724',
    marginLeft: 8,
  },
  tipsCard: {
    backgroundColor: '#D1ECF1',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
  },
  tipsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0C5460',
    marginLeft: 8,
  },
  tipText: {
    fontSize: 14,
    color: '#0C5460',
    marginBottom: 5,
  },
  insightsCard: {
    backgroundColor: '#E2D9F3',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
  },
  insightsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  insightsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#5A2D82',
    marginLeft: 8,
  },
  insightText: {
    fontSize: 14,
    color: '#5A2D82',
    marginBottom: 5,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
    marginTop: 50,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 15,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
  },
});