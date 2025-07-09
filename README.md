# AINUT iOS App

A beautiful, modern iOS app for AI-powered nutrition tracking and analysis.

## Features

### 🍎 Core Functionality
- **Meal Analysis**: Take photos or describe meals for AI-powered nutrition analysis
- **Food Logging**: Track daily meals with detailed nutritional information
- **Personalized Advice**: Get tailored nutrition recommendations based on your profile
- **Achievement System**: Earn badges and points for consistent tracking
- **User Profiles**: Customize dietary preferences, allergies, and AI personality

### 📱 User Experience
- **Modern Design**: Clean, intuitive interface with smooth animations
- **Dark Mode Support**: Automatic adaptation to system appearance
- **Offline Capability**: Core functionality works without internet
- **Haptic Feedback**: Tactile responses for better user interaction
- **Accessibility**: VoiceOver support and dynamic type scaling

### 🔐 Authentication
- Secure user registration and login
- JWT token-based authentication
- Automatic session management
- Biometric authentication support (Face ID/Touch ID)

### 📊 Data Visualization
- Daily nutrition summaries
- Progress tracking charts
- Macro breakdown visualizations
- Achievement progress indicators

## Technical Stack

- **Framework**: SwiftUI
- **Minimum iOS Version**: 17.0
- **Architecture**: MVVM with Combine
- **Networking**: URLSession with async/await
- **Image Processing**: Core Image and Vision frameworks
- **Data Persistence**: Core Data with CloudKit sync
- **Authentication**: Keychain Services

## Project Structure

```
AINUT/
├── AINUTApp.swift          # App entry point
├── ContentView.swift       # Main tab view controller
├── Models/
│   └── Models.swift        # Data models and API responses
├── Services/
│   └── NetworkManager.swift # API client and networking
├── Views/
│   ├── AuthView.swift      # Login/registration
│   ├── HomeView.swift      # Dashboard and overview
│   ├── MealAnalysisView.swift # Camera and meal analysis
│   ├── FoodLogView.swift   # Food history and logs
│   ├── NutritionAdviceView.swift # AI recommendations
│   └── ProfileView.swift   # User settings and profile
├── Utils/
│   ├── ImagePicker.swift   # Camera/photo library picker
│   └── Extensions.swift    # Helper extensions and utilities
└── Assets.xcassets/        # App icons and images
```

## Setup Instructions

### Prerequisites
- Xcode 15.0 or later
- iOS 17.0+ device or simulator
- Apple Developer account (for device testing)

### Installation
1. Clone the repository
2. Open `AINUT.xcodeproj` in Xcode
3. Update the backend URL in `NetworkManager.swift`:
   ```swift
   private let baseURL = "YOUR_BACKEND_URL_HERE"
   ```
4. Build and run the project

### Configuration
- **Bundle Identifier**: Update in project settings
- **Team**: Select your development team
- **Capabilities**: Enable required capabilities (Camera, Photo Library)
- **Info.plist**: Camera and photo library usage descriptions are included

## API Integration

The app connects to the AINUT backend API with the following endpoints:

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Meal Analysis
- `POST /ai/analyze-meal` - Analyze meal from image/text
- `POST /upload-user-image` - Upload meal photos

### Food Logging
- `POST /food-logs` - Save food log entry
- `GET /users/{id}/food-logs` - Get user's food history

### Nutrition Advice
- `POST /ai/nutrition-advice` - Get generic advice
- `POST /ai/personalized-nutrition-advice` - Get personalized advice

### User Management
- `POST /users/profile` - Save user profile
- `GET /users/{id}/profile` - Get user profile
- `GET /users/{id}/achievements` - Get user achievements

## Key Features Implementation

### Meal Analysis
- Camera integration with `ImagePicker`
- Image upload to backend API
- Real-time nutrition analysis display
- Correction and re-analysis capability

### Food Logging
- Date-based filtering and navigation
- Meal categorization (breakfast, lunch, dinner, snack)
- Daily nutrition summaries
- Historical data visualization

### Personalized Advice
- User profile-based recommendations
- Nutrient deficit analysis
- Meal suggestions with macro breakdowns
- Achievement tracking integration

### User Experience
- Smooth animations and transitions
- Pull-to-refresh functionality
- Loading states and error handling
- Haptic feedback for interactions

## Design System

### Colors
- **Primary Green**: `#33B852` - Main brand color
- **Secondary Blue**: `#3380CC` - Accent color
- **Warning Orange**: `#FF9933` - Alerts and warnings
- **Error Red**: `#FF4444` - Error states

### Typography
- **Headlines**: SF Pro Display, Bold
- **Body Text**: SF Pro Text, Regular
- **Captions**: SF Pro Text, Medium

### Components
- Custom button styles with gradients
- Rounded cards with subtle shadows
- Progress indicators and charts
- Achievement badges and icons

## Performance Optimizations

- **Lazy Loading**: Lists use `LazyVStack` and `LazyVGrid`
- **Image Caching**: Automatic image caching for meal photos
- **Network Efficiency**: Request batching and caching
- **Memory Management**: Proper view lifecycle handling

## Testing

### Unit Tests
- Model validation and parsing
- Network request/response handling
- Business logic validation

### UI Tests
- Authentication flow
- Meal analysis workflow
- Food logging functionality
- Profile management

## Deployment

### App Store Preparation
1. Update version and build numbers
2. Generate app icons (all required sizes)
3. Create App Store screenshots
4. Write app description and keywords
5. Submit for review

### TestFlight Distribution
1. Archive the app in Xcode
2. Upload to App Store Connect
3. Add internal/external testers
4. Distribute beta builds

## Future Enhancements

### Planned Features
- **Apple Health Integration**: Sync with HealthKit
- **Watch App**: Apple Watch companion app
- **Widgets**: Home screen nutrition widgets
- **Siri Shortcuts**: Voice-activated food logging
- **Social Features**: Share achievements and progress

### Technical Improvements
- **Core Data Migration**: Local data persistence
- **CloudKit Sync**: Cross-device synchronization
- **Machine Learning**: On-device food recognition
- **Background Processing**: Automatic nutrition reminders

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Email: support@ainut.app
- GitHub Issues: Create an issue in this repository
- Documentation: Check the wiki for detailed guides

---

Built with ❤️ using SwiftUI and the AINUT API