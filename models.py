# app/models.py
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, JSON, Float, Integer, Text, DateTime, Boolean
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import uuid4
import time
import re

# SQLAlchemy Base
Base = declarative_base()

# ============ DATABASE MODELS ============
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserProfileDB(Base):
    __tablename__ = "user_profiles"
    
    user_id = Column(String, primary_key=True, index=True)
    dietary_preferences = Column(JSON, default=[])
    favorite_foods = Column(JSON, default=[])
    disliked_foods = Column(JSON, default=[])
    cuisine_preferences = Column(JSON, default=[])
    allergies = Column(JSON, default=[])
    activity_level = Column(String, default="normal")
    nutrition_goals = Column(JSON, default={})
    ai_personality_type = Column(String, default="supportive")
    preferred_communication_style = Column(String, default="encouraging")
    coaching_frequency = Column(String, default="daily")
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)

class FoodLogDB(Base):
    __tablename__ = "food_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    meal_time = Column(String)
    foods = Column(JSON)
    total_calories = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    date_string = Column(String, index=True)

class DailySummaryDB(Base):
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    date = Column(String, index=True)
    summary_json = Column(JSON)
    calories_total = Column(Float)
    macro_split = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIResponseCacheDB(Base):
    __tablename__ = "ai_response_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    prompt_hash = Column(String, index=True)
    prompt = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserAchievementDB(Base):
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    achievement_type = Column(String)
    achievement_name = Column(String)
    description = Column(String)
    points = Column(Integer, default=0)
    badge_icon = Column(String, default="🏆")
    earned_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class SmartNotificationDB(Base):
    __tablename__ = "smart_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    notification_type = Column(String)
    title = Column(String)
    message = Column(Text)
    scheduled_time = Column(DateTime)
    sent = Column(Boolean, default=False)
    opened = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class NutritionStoryDB(Base):
    __tablename__ = "nutrition_stories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    story_type = Column(String)
    story_title = Column(String)
    story_content = Column(JSON)
    time_period = Column(String)
    key_insights = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIRecipeDB(Base):
    __tablename__ = "ai_recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    recipe_name = Column(String)
    description = Column(Text)
    ingredients = Column(JSON)
    instructions = Column(JSON)
    nutrition_info = Column(JSON)
    target_macros = Column(JSON)
    dietary_restrictions = Column(JSON)
    difficulty_level = Column(String)
    prep_time = Column(Integer)
    cook_time = Column(Integer)
    servings = Column(Integer)
    tags = Column(JSON)
    user_rating = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SmartDinnerPredictionDB(Base):
    __tablename__ = "smart_dinner_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    prediction_date = Column(String, index=True)
    current_intake = Column(JSON)
    remaining_needs = Column(JSON)
    suggested_recipes = Column(JSON)
    backup_options = Column(JSON)
    reasoning = Column(Text)
    confidence_score = Column(Float)
    user_feedback = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class NutritionTimeTravelDB(Base):
    __tablename__ = "nutrition_time_travel"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    projection_type = Column(String)
    current_pattern = Column(JSON)
    target_goal = Column(JSON)
    projected_outcome = Column(JSON)
    recommended_changes = Column(JSON)
    timeline = Column(JSON)
    confidence_score = Column(Float)
    scenario_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserImageDB(Base):
    __tablename__ = "user_images"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, index=True)
    public_id = Column(String, unique=True)
    image_url = Column(String)
    original_filename = Column(String)
    file_size = Column(Integer)
    image_type = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

# ============ PYDANTIC SCHEMAS ============

# Request/Response Models
class MealRequest(BaseModel):
    image_url: Optional[HttpUrl] = None
    user_input: str = Field(..., max_length=1000)
    corrections: Optional[str] = Field(None, max_length=500)

class Food(BaseModel):
    name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

class MealResponse(BaseModel):
    meal_name: str
    meal_type: str
    foods: List[Food]
    total_calories: int
    analysis_method: Literal["vision", "text", "error_fallback"]

class SearchRequest(BaseModel):
    query: str = Field(..., max_length=100)

class SearchResult(BaseModel):
    name: str
    nutrition_per_100g: Dict[str, float]
    portion_suggestions: List[Dict[str, Any]]

class SearchResponse(BaseModel):
    results: List[SearchResult]

class FoodLogItem(BaseModel):
    name: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    micronutrients: Optional[Dict[str, float]] = None

class FoodSuggestion(BaseModel):
    meal_idea: str
    description: str
    total_calories: float
    protein_provided: float
    carbs_provided: float
    fat_provided: float
    percentage_coverage: Dict[str, int]
    meal_type: str
    easy_to_make: bool = True
    why_perfect: str

class NutrientAdvice(BaseModel):
    nutrient: str
    current_intake: float
    target: float
    deficit: float
    suggestions: List[FoodSuggestion]
    why_important: str

class NutritionistRequest(BaseModel):
    food_log: List[FoodLogItem]
    daily_targets: Dict[str, float]
    dietary_prefs: Optional[str] = None
    user_context: Optional[str] = None

class NutritionistResponse(BaseModel):
    overall_summary: str
    safety_notes: List[str] = []
    nutrients_to_focus_on: List[NutrientAdvice]
    achievements: List[str]
    tips: List[str]

class PersonalizedNutritionistRequest(BaseModel):
    user_id: str
    food_log: List[FoodLogItem]
    daily_targets: Dict[str, float]

class PersonalizedNutritionistResponse(BaseModel):
    overall_summary: str
    safety_notes: List[str] = []
    nutrients_to_focus_on: List[NutrientAdvice]
    achievements: List[str]
    tips: List[str]
    personalized_insights: List[str] = []

class SubstituteRequest(BaseModel):
    food_name: str = Field(..., max_length=100)
    dietary_restrictions: List[str] = Field(default=[], max_items=5)
    nutrition_goals: str = Field(..., max_length=200)

class SubstituteOption(BaseModel):
    food: str
    reason: str
    nutrition_comparison: str
    availability: str

class SubstituteResponse(BaseModel):
    original_food: str
    substitutes: List[SubstituteOption]

class SaveFoodLogRequest(BaseModel):
    user_id: str
    date_string: str 
    meal_time: str
    foods: List[FoodLogItem]
    total_calories: float

class FoodLogResponse(BaseModel):
    log_id: str
    meal_time: str
    foods: List[Dict[str, Any]]
    total_calories: float
    created_at: datetime
    date_string: str

# User Management Models
class UserProfile(BaseModel):
    user_id: str
    dietary_preferences: List[str] = Field(default=[], max_items=5)
    favorite_foods: List[str] = Field(default=[], max_items=10)
    disliked_foods: List[str] = Field(default=[], max_items=10)
    cuisine_preferences: List[str] = Field(default=[], max_items=5)
    allergies: List[str] = Field(default=[], max_items=10)
    activity_level: str = "normal"
    nutrition_goals: Dict[str, float] = {}
    ai_personality_type: str = "supportive"
    preferred_communication_style: str = "encouraging"
    coaching_frequency: str = "daily"
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()

    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="Username is required")
    password: str = Field(..., min_length=1, max_length=100, description="Password is required")

class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Advanced AI Models
class AIRecipeRequest(BaseModel):
    user_id: str
    target_macros: Dict[str, float]
    dietary_restrictions: List[str] = []
    cuisine_preference: Optional[str] = None
    difficulty_level: str = "easy"
    max_prep_time: int = 30
    servings: int = 1

class AIRecipeResponse(BaseModel):
    recipe_id: int
    recipe_name: str
    description: str
    ingredients: List[Dict[str, Any]]
    instructions: List[str]
    nutrition_info: Dict[str, float]
    prep_time: int
    cook_time: int
    difficulty_level: str
    tags: List[str]

class SmartDinnerPredictionRequest(BaseModel):
    user_id: str
    prediction_date: str

class SmartDinnerPredictionResponse(BaseModel):
    prediction_id: int
    remaining_needs: Dict[str, float]
    suggested_recipes: List[Dict[str, Any]]
    backup_options: List[Dict[str, Any]]
    reasoning: str
    confidence_score: float

class NutritionTimeTravelRequest(BaseModel):
    user_id: str
    projection_type: str
    target_goal: Dict[str, Any]
    scenario_name: Optional[str] = None

class NutritionTimeTravelResponse(BaseModel):
    projection_id: int
    scenario_name: str
    current_pattern: Dict[str, Any]
    projected_outcome: Dict[str, Any]
    recommended_changes: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    confidence_score: float
    key_insights: List[str]

class DailySummaryRequest(BaseModel):
    user_id: str
    date: str
    summary_json: Dict[str, Any]
    calories_total: float
    macro_split: Dict[str, float]

class DailySummaryResponse(BaseModel):
    id: int
    user_id: str
    date: str
    summary_json: Dict[str, Any]
    calories_total: float
    macro_split: Dict[str, float]
    created_at: datetime

# Achievement and Notification Models
class UserAchievement(BaseModel):
    achievement_type: str
    achievement_name: str
    description: str
    points: int = 0
    badge_icon: str = "🏆"

class AchievementResponse(BaseModel):
    id: int
    achievement_name: str
    description: str
    points: int
    badge_icon: str
    earned_date: datetime

    class Config:
        from_attributes = True

class SmartNotification(BaseModel):
    user_id: str
    notification_type: str
    title: str
    message: str
    scheduled_time: datetime

class NutritionStory(BaseModel):
    user_id: str
    story_type: str
    story_title: str
    story_content: Dict[str, Any]
    time_period: str
    key_insights: List[str]

# Image Upload Models
class ImageUploadResponse(BaseModel):
    success: bool
    image_id: str
    url: str
    public_id: str
    image_type: str
    uploaded_at: datetime

class UserImageResponse(BaseModel):
    image_id: str
    public_id: str
    url: str
    original_filename: Optional[str]
    file_size: int
    image_type: str
    uploaded_at: datetime

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    message: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SuccessResponse(BaseModel):
    """Standard success response model"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
