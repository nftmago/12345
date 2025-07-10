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
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../config/api';

export default function HomeScreen({ navigation }) {
  const { user, token } = useAuth();
  const [refreshing, setRefreshing] = useState(false);
  const [todayStats, setTodayStats] = useState({
    meals: 0,
    calories: 0,
    protein: 0,
  });

  useEffect(() => {
    loadTodayStats();
  }, []);

  const loadTodayStats = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await apiRequest(`/users/${user.username}/food-logs?date_filter=${today}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      const totalCalories = response.reduce((sum, log) => sum + log.total_calories, 0);
      const totalProtein = response.reduce((sum, log) => {
        return sum + log.foods.reduce((foodSum, food) => foodSum + (food.protein_g || 0), 0);
      }, 0);

      setTodayStats({
        meals: response.length,
        calories: Math.round(totalCalories),
        protein: Math.round(totalProtein),
      });
    } catch (error) {
      console.error('Error loading today stats:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadTodayStats();
    setRefreshing(false);
  };

  const QuickActionCard = ({ icon, title, subtitle, color, onPress }) => (
    <TouchableOpacity style={styles.actionCard} onPress={onPress}>
      <LinearGradient
        colors={[color, `${color}CC`]}
        style={styles.actionGradient}
      >
        <Ionicons name={icon} size={30} color="white" />
        <Text style={styles.actionTitle}>{title}</Text>
        <Text style={styles.actionSubtitle}>{subtitle}</Text>
      </LinearGradient>
    </TouchableOpacity>
  );

  const StatCard = ({ title, value, unit, icon, color }) => (
    <View style={styles.statCard}>
      <View style={styles.statHeader}>
        <Ionicons name={icon} size={24} color={color} />
        <Text style={styles.statTitle}>{title}</Text>
      </View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statUnit}>{unit}</Text>
    </View>
  );

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.username}>{user?.username || 'User'}</Text>
        </View>
        <Ionicons name="leaf" size={40} color="#33B852" />
      </View>

      <Text style={styles.motivationText}>Let's make today nutritious! 🌱</Text>

      {/* Today's Stats */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Today's Summary</Text>
        <View style={styles.statsContainer}>
          <StatCard
            title="Meals"
            value={todayStats.meals}
            unit="logged"
            icon="restaurant"
            color="#33B852"
          />
          <StatCard
            title="Calories"
            value={todayStats.calories}
            unit="kcal"
            icon="flame"
            color="#FF6B35"
          />
          <StatCard
            title="Protein"
            value={todayStats.protein}
            unit="grams"
            icon="fitness"
            color="#4A90E2"
          />
        </View>
      </View>

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsContainer}>
          <QuickActionCard
            icon="camera"
            title="Analyze Meal"
            subtitle="Take a photo"
            color="#4A90E2"
            onPress={() => navigation.navigate('Analyze')}
          />
          <QuickActionCard
            icon="heart"
            title="Get Advice"
            subtitle="Nutrition tips"
            color="#E74C3C"
            onPress={() => navigation.navigate('Advice')}
          />
          <QuickActionCard
            icon="list"
            title="Food Log"
            subtitle="View history"
            color="#F39C12"
            onPress={() => navigation.navigate('Log')}
          />
          <QuickActionCard
            icon="person"
            title="Profile"
            subtitle="Settings"
            color="#9B59B6"
            onPress={() => navigation.navigate('Profile')}
          />
        </View>
      </View>

      {/* Motivation Section */}
      <View style={styles.motivationSection}>
        <LinearGradient
          colors={['#33B852', '#2A9644']}
          style={styles.motivationCard}
        >
          <Ionicons name="trophy" size={30} color="white" />
          <Text style={styles.motivationTitle}>Keep it up!</Text>
          <Text style={styles.motivationDescription}>
            You're building healthy habits. Every meal logged is progress toward your goals.
          </Text>
        </LinearGradient>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
  },
  greeting: {
    fontSize: 18,
    color: '#666',
  },
  username: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    textTransform: 'capitalize',
  },
  motivationText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  section: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
    paddingHorizontal: 20,
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    justifyContent: 'space-between',
  },
  statCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 15,
    flex: 1,
    marginHorizontal: 5,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  statTitle: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  statUnit: {
    fontSize: 12,
    color: '#999',
  },
  actionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 20,
    justifyContent: 'space-between',
  },
  actionCard: {
    width: '48%',
    marginBottom: 15,
    borderRadius: 15,
    overflow: 'hidden',
  },
  actionGradient: {
    padding: 20,
    alignItems: 'center',
  },
  actionTitle: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 10,
  },
  actionSubtitle: {
    color: 'white',
    fontSize: 12,
    opacity: 0.9,
    marginTop: 5,
  },
  motivationSection: {
    paddingHorizontal: 20,
    marginBottom: 30,
  },
  motivationCard: {
    borderRadius: 15,
    padding: 20,
    alignItems: 'center',
  },
  motivationTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 10,
  },
  motivationDescription: {
    color: 'white',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 10,
    opacity: 0.9,
  },
});