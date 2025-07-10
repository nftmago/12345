import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../config/api';

export default function FoodLogScreen() {
  const { user, token } = useAuth();
  const [foodLogs, setFoodLogs] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFoodLogs();
  }, [selectedDate]);

  const loadFoodLogs = async () => {
    try {
      const dateString = selectedDate.toISOString().split('T')[0];
      const response = await apiRequest(`/users/${user.username}/food-logs?date_filter=${dateString}&limit=50`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      setFoodLogs(response);
    } catch (error) {
      console.error('Error loading food logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadFoodLogs();
    setRefreshing(false);
  };

  const getDateLabel = (date) => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const changeDate = (direction) => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + direction);
    setSelectedDate(newDate);
  };

  const groupedLogs = foodLogs.reduce((groups, log) => {
    const mealTime = log.meal_time;
    if (!groups[mealTime]) {
      groups[mealTime] = [];
    }
    groups[mealTime].push(log);
    return groups;
  }, {});

  const totalCalories = foodLogs.reduce((sum, log) => sum + log.total_calories, 0);
  const mealCount = foodLogs.length;

  const getMealIcon = (mealType) => {
    switch (mealType.toLowerCase()) {
      case 'breakfast':
        return 'sunny';
      case 'lunch':
        return 'partly-sunny';
      case 'dinner':
        return 'moon';
      default:
        return 'restaurant';
    }
  };

  const MealGroup = ({ mealType, logs }) => {
    const mealCalories = logs.reduce((sum, log) => sum + log.total_calories, 0);

    return (
      <View style={styles.mealGroup}>
        <View style={styles.mealHeader}>
          <View style={styles.mealTitleContainer}>
            <Ionicons name={getMealIcon(mealType)} size={20} color="#33B852" />
            <Text style={styles.mealTitle}>{mealType.charAt(0).toUpperCase() + mealType.slice(1)}</Text>
          </View>
          <Text style={styles.mealCalories}>{Math.round(mealCalories)} cal</Text>
        </View>

        {logs.map((log, index) => (
          <View key={index} style={styles.logEntry}>
            <View style={styles.logHeader}>
              <Text style={styles.logTime}>
                {new Date(log.created_at).toLocaleTimeString('en-US', { 
                  hour: 'numeric', 
                  minute: '2-digit' 
                })}
              </Text>
              <Text style={styles.logCalories}>{Math.round(log.total_calories)} calories</Text>
            </View>
            
            {log.foods && log.foods.length > 0 && (
              <View style={styles.foodsList}>
                {log.foods.slice(0, 3).map((food, foodIndex) => (
                  <Text key={foodIndex} style={styles.foodItem}>
                    • {food.name || 'Unknown food'}
                  </Text>
                ))}
                {log.foods.length > 3 && (
                  <Text style={styles.moreFoods}>
                    +{log.foods.length - 3} more items
                  </Text>
                )}
              </View>
            )}
          </View>
        ))}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Food Log</Text>
        
        {/* Date Navigation */}
        <View style={styles.dateNavigation}>
          <TouchableOpacity onPress={() => changeDate(-1)} style={styles.dateButton}>
            <Ionicons name="chevron-back" size={20} color="#33B852" />
          </TouchableOpacity>
          
          <Text style={styles.dateText}>{getDateLabel(selectedDate)}</Text>
          
          <TouchableOpacity 
            onPress={() => changeDate(1)} 
            style={[styles.dateButton, selectedDate >= new Date() && styles.disabledButton]}
            disabled={selectedDate >= new Date()}
          >
            <Ionicons name="chevron-forward" size={20} color="#33B852" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Daily Summary */}
        {foodLogs.length > 0 && (
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Daily Summary</Text>
            <View style={styles.summaryStats}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{Math.round(totalCalories)}</Text>
                <Text style={styles.summaryLabel}>Calories</Text>
              </View>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{mealCount}</Text>
                <Text style={styles.summaryLabel}>Meals</Text>
              </View>
            </View>
          </View>
        )}

        {/* Meal Groups */}
        {loading ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>Loading...</Text>
          </View>
        ) : foodLogs.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="restaurant-outline" size={60} color="#ccc" />
            <Text style={styles.emptyTitle}>No meals logged</Text>
            <Text style={styles.emptyText}>
              {selectedDate.toDateString() === new Date().toDateString()
                ? "Start by analyzing your first meal of the day!"
                : "No meals were logged on this date"}
            </Text>
          </View>
        ) : (
          Object.entries(groupedLogs).map(([mealType, logs]) => (
            <MealGroup key={mealType} mealType={mealType} logs={logs} />
          ))
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
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 20,
  },
  dateNavigation: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  dateButton: {
    padding: 10,
  },
  disabledButton: {
    opacity: 0.3,
  },
  dateText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginHorizontal: 20,
    minWidth: 100,
    textAlign: 'center',
  },
  content: {
    flex: 1,
  },
  summaryCard: {
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
  summaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  summaryItem: {
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#33B852',
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  mealGroup: {
    backgroundColor: 'white',
    margin: 20,
    marginTop: 0,
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
  mealHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  mealTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  mealTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 8,
  },
  mealCalories: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#33B852',
  },
  logEntry: {
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
  },
  logHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  logTime: {
    fontSize: 14,
    color: '#666',
  },
  logCalories: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#33B852',
  },
  foodsList: {
    marginTop: 5,
  },
  foodItem: {
    fontSize: 14,
    color: '#333',
    marginBottom: 2,
  },
  moreFoods: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
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