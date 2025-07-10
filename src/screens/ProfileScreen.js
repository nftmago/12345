import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../config/api';

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      // Load user profile
      try {
        const profileResponse = await apiRequest(`/users/${user.username}/profile`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        setProfile(profileResponse);
      } catch (error) {
        // Profile might not exist yet
        console.log('No profile found');
      }

      // Load achievements
      try {
        const achievementsResponse = await apiRequest(`/users/${user.username}/achievements`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        setAchievements(achievementsResponse);
      } catch (error) {
        console.log('No achievements found');
      }
    } catch (error) {
      console.error('Error loading profile data:', error);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Sign Out', style: 'destructive', onPress: logout },
      ]
    );
  };

  const SettingsRow = ({ icon, title, onPress, showArrow = true, rightComponent }) => (
    <TouchableOpacity style={styles.settingsRow} onPress={onPress}>
      <View style={styles.settingsLeft}>
        <Ionicons name={icon} size={24} color="#33B852" />
        <Text style={styles.settingsTitle}>{title}</Text>
      </View>
      {rightComponent || (showArrow && (
        <Ionicons name="chevron-forward" size={20} color="#ccc" />
      ))}
    </TouchableOpacity>
  );

  const StatCard = ({ title, value, icon, color }) => (
    <View style={styles.statCard}>
      <Ionicons name={icon} size={24} color={color} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statTitle}>{title}</Text>
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <LinearGradient
          colors={['#33B852', '#2A9644']}
          style={styles.profileCard}
        >
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </Text>
          </View>
          <Text style={styles.username}>{user?.username || 'User'}</Text>
          <Text style={styles.email}>{user?.email || ''}</Text>
        </LinearGradient>
      </View>

      {/* Quick Stats */}
      {achievements.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Progress</Text>
          <View style={styles.statsContainer}>
            <StatCard
              title="Achievements"
              value={achievements.length}
              icon="trophy"
              color="#F39C12"
            />
            <StatCard
              title="Total Points"
              value={achievements.reduce((sum, ach) => sum + ach.points, 0)}
              icon="star"
              color="#E74C3C"
            />
            <StatCard
              title="Level"
              value={Math.floor(achievements.reduce((sum, ach) => sum + ach.points, 0) / 100) + 1}
              icon="trending-up"
              color="#9B59B6"
            />
          </View>
        </View>
      )}

      {/* Recent Achievements */}
      {achievements.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Achievements</Text>
          <View style={styles.achievementsContainer}>
            {achievements.slice(0, 6).map((achievement, index) => (
              <View key={index} style={styles.achievementBadge}>
                <Text style={styles.badgeIcon}>{achievement.badge_icon}</Text>
                <Text style={styles.badgeName}>{achievement.achievement_name}</Text>
                <Text style={styles.badgePoints}>{achievement.points} pts</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Settings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Settings</Text>
        <View style={styles.settingsContainer}>
          <SettingsRow
            icon="person-circle"
            title="Edit Profile"
            onPress={() => {
              Alert.alert('Coming Soon', 'Profile editing will be available in the next update!');
            }}
          />
          
          <SettingsRow
            icon="notifications"
            title="Notifications"
            showArrow={false}
            rightComponent={
              <Switch
                value={notificationsEnabled}
                onValueChange={setNotificationsEnabled}
                trackColor={{ false: '#ccc', true: '#33B852' }}
              />
            }
          />
          
          <SettingsRow
            icon="help-circle"
            title="Help & Support"
            onPress={() => {
              Alert.alert('Help & Support', 'For support, please contact us at support@ainut.app');
            }}
          />
          
          <SettingsRow
            icon="information-circle"
            title="About"
            onPress={() => {
              Alert.alert('About AINUT', 'AINUT v1.0\nYour AI-Powered Nutrition Assistant');
            }}
          />
          
          <SettingsRow
            icon="log-out"
            title="Sign Out"
            onPress={handleLogout}
            showArrow={false}
          />
        </View>
      </View>

      {/* App Info */}
      <View style={styles.appInfo}>
        <Text style={styles.appInfoText}>AINUT v1.0</Text>
        <Text style={styles.appInfoText}>Made with ❤️ for better nutrition</Text>
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
    padding: 20,
    paddingTop: 60,
  },
  profileCard: {
    borderRadius: 20,
    padding: 30,
    alignItems: 'center',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 15,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
  },
  username: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    textTransform: 'capitalize',
  },
  email: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    marginTop: 5,
  },
  section: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 20,
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
    padding: 20,
    alignItems: 'center',
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
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 10,
  },
  statTitle: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
  },
  achievementsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 20,
    justifyContent: 'space-between',
  },
  achievementBadge: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
    width: '30%',
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
  badgeIcon: {
    fontSize: 24,
    marginBottom: 5,
  },
  badgeName: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 3,
  },
  badgePoints: {
    fontSize: 10,
    color: '#666',
  },
  settingsContainer: {
    backgroundColor: 'white',
    marginHorizontal: 20,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingsLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingsTitle: {
    fontSize: 16,
    color: '#333',
    marginLeft: 15,
  },
  appInfo: {
    alignItems: 'center',
    padding: 20,
    marginBottom: 30,
  },
  appInfoText: {
    fontSize: 14,
    color: '#999',
    marginBottom: 5,
  },
});