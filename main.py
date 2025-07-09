# app/main.py
import os
import time
import sys
import traceback
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from dotenv import load_dotenv

from config import settings
from models import User, UserCreate, UserLogin, MealRequest, MealResponse, NutritionistRequest, NutritionistResponse, PersonalizedNutritionistRequest, PersonalizedNutritionistResponse, SearchRequest, SearchResponse, SubstituteRequest, SubstituteResponse, SaveFoodLogRequest, FoodLogResponse, UserProfile, ImageUploadResponse, UserImageResponse, DailySummaryRequest, DailySummaryResponse, AIRecipeRequest, AIRecipeResponse, SmartDinnerPredictionRequest, SmartDinnerPredictionResponse, NutritionTimeTravelRequest, NutritionTimeTravelResponse, Token, UserDB, AchievementResponse
from database import (
    get_db, save_food_log, get_user_food_logs, get_dinner_predictions, get_time_travel_scenarios,
    get_user_profile, save_user_profile, get_cached_ai_response, cache_ai_response,
    check_and_award_achievements, create_smart_notification, get_user_notifications,
    mark_notification_opened, save_daily_summary, get_daily_summary, generate_nutrition_story,
    get_nutrition_story, save_ai_recipe, get_user_recipes, rate_recipe, save_dinner_prediction,
    save_time_travel_projection, save_user_image, get_user_images, get_user_image_by_id,
    delete_user_image_from_db, get_database_stats, get_user_achievements, get_recent_food_logs
)
from auth import register_user, login_user, get_current_active_user, get_current_user_optional, verify_user_access, get_current_user
from services import create_services
import utils

try:
    print("✅ All imports successful")
    
except Exception as e:
    print(f"❌ Import error: {str(e)}")
    print(traceback.format_exc())
    sys.exit(1)

# ============ CREATE FASTAPI APP ============
app = FastAPI(
    title="AINUT API",
    version="6.0",
    description="AI-Powered Nutrition Assistant with comprehensive meal analysis and personalized advice"
)

# ============ CORS CONFIGURATION ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://nutai-production.up.railway.app",
        "https://app.base44.com"
    ] if settings.environment == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ============ INITIALIZE SERVICES ============
services = create_services()
ai_service = services["ai_service"]
nutrition_service = services["nutrition_service"]
user_service = services["user_service"]
image_service = services["image_service"]
notification_service = services["notification_service"]
story_service = services["story_service"]
achievement_service = services["achievement_service"]
recipe_service = services["recipe_service"]

# ============ AUTHENTICATION ENDPOINTS ============
@app.post("/auth/register", response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user with enhanced error handling"""
    try:
        db_user = await register_user(user, db)
        return User(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        raise HTTPException(500, f"Registration failed: {str(e)}")

@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token with enhanced error handling"""
    try:
        token_data = await login_user(user_credentials, db)
        return token_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(500, f"Login failed: {str(e)}")

@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: UserDB = Depends(get_current_active_user)):
    """Get current user information"""
    return User(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

@app.post("/auth/refresh", response_model=Token)
async def refresh_token(
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Refresh user's access token"""
    try:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": current_user.username}, 
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print(f"Token refresh error: {str(e)}")
        raise HTTPException(500, "Token refresh failed")

# ============ MEAL ANALYSIS ENDPOINTS ============
@app.post("/ai/analyze-meal", response_model=MealResponse)
async def analyze_meal(
    request: MealRequest, 
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Analyze meal from image or text description"""
    try:
        user_id = current_user.username if current_user else None
        
        result = await nutrition_service.analyze_meal(
            user_input=request.user_input,
            image_url=str(request.image_url) if request.image_url else None,
            corrections=request.corrections,
            user_id=user_id,
            db=db
        )
        
        return MealResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Meal analysis endpoint error: {str(e)}")
        # Return safe fallback response
        return MealResponse(
            meal_name="Unknown Meal",
            meal_type="snack",
            foods=[],
            total_calories=0,
            analysis_method="error_fallback"
        )

# ============ NUTRITION ADVICE ENDPOINTS ============
@app.post("/ai/nutrition-advice", response_model=NutritionistResponse)
async def get_nutrition_advice(
    request: NutritionistRequest, 
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get generic nutrition advice"""
    try:
        user_id = current_user.username if current_user else None
        
        advice = await ai_service.get_nutrition_advice(
            food_log=[item.dict() for item in request.food_log],
            daily_targets=request.daily_targets,
            user_id=user_id,
            db=db
        )
        
        return NutritionistResponse(**advice)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Nutrition advice endpoint error: {str(e)}")
        raise HTTPException(500, f"Advice generation failed: {str(e)}")

@app.post("/ai/personalized-nutrition-advice", response_model=PersonalizedNutritionistResponse)
async def get_personalized_nutrition_advice(
    request: PersonalizedNutritionistRequest, 
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized nutrition advice based on user profile"""
    try:
        # Verify user access
        if current_user.username != request.user_id:
            raise HTTPException(403, "Access denied")
        
        advice = await nutrition_service.get_personalized_advice(
            user_id=request.user_id,
            food_log=request.food_log,
            daily_targets=request.daily_targets,
            db=db
        )
        
        return PersonalizedNutritionistResponse(**advice)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Personalized advice endpoint error: {str(e)}")
        raise HTTPException(500, f"Personalized advice failed: {str(e)}")

# ============ FOOD SEARCH AND SUBSTITUTES ============
@app.post("/ai/search", response_model=SearchResponse)
async def search_food(request: SearchRequest):
    """Search for food information"""
    try:
        result = await ai_service.search_food(request.query)
        return SearchResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Food search endpoint error: {str(e)}")
        raise HTTPException(500, f"Search failed: {str(e)}")

@app.post("/ai/find-substitutes", response_model=SubstituteResponse)
async def find_substitutes(request: SubstituteRequest):
    """Find healthy food substitutes"""
    try:
        result = await ai_service.find_substitutes(
            food_name=request.food_name,
            restrictions=request.dietary_restrictions,
            goals=request.nutrition_goals
        )
        return SubstituteResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Substitute search endpoint error: {str(e)}")
        raise HTTPException(500, f"Substitute search failed: {str(e)}")

# ============ FOOD LOGGING ENDPOINTS ============
@app.post("/food-logs")
async def save_food_log(
    request: SaveFoodLogRequest,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Save food log entry with achievement checking"""
    try:
        # Verify user access
        if current_user.username != request.user_id:
            raise HTTPException(403, "Access denied")
        
        return await nutrition_service.save_food_log_with_achievements(request, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Food log endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to save food log: {str(e)}")

@app.get("/users/{user_id}/food-logs", response_model=List[FoodLogResponse])
async def get_user_food_logs(
    user_id: str,
    date_filter: Optional[str] = None,
    limit: int = 50,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's food logs with optional date filtering"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        food_logs = await nutrition_service.get_user_food_logs(user_id, date_filter, limit, db)
        return [FoodLogResponse(**log) for log in food_logs]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Food logs fetch endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to get food logs: {str(e)}")

# ============ USER PROFILE ENDPOINTS ============
@app.post("/users/profile")
async def create_user_profile(
    profile: UserProfile, 
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update user profile"""
    try:
        # Verify user access
        if current_user.username != profile.user_id:
            raise HTTPException(403, "Access denied")
        
        return await user_service.create_or_update_profile(profile, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Profile creation endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to save profile: {str(e)}")

@app.get("/users/{user_id}/profile")
async def get_user_profile_endpoint(
    user_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        return await user_service.get_user_profile(user_id, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Profile fetch endpoint error: {str(e)}")
        raise HTTPException(500, f"Error fetching profile: {str(e)}")

@app.get("/users/{user_id}/achievements", response_model=List[AchievementResponse], summary="Get User Achievements")
async def get_user_achievements_endpoint(
    user_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all achievements for a specific user."""
    await verify_user_access(user_id, current_user)
    
    try:
        achievements = await get_user_achievements(user_id, db)
        return achievements
    except Exception as e:
        print(f"Error fetching achievements for user {user_id}: {str(e)}")
        raise HTTPException(500, f"Could not fetch achievements: {str(e)}")

@app.post("/users/{user_id}/personality")
async def update_ai_personality(
    user_id: str,
    personality_type: str,
    communication_style: str,
    coaching_frequency: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's AI personality preferences"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        return await user_service.update_ai_personality(
            user_id, personality_type, communication_style, coaching_frequency, db
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Personality update endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to update AI personality: {str(e)}")

# ============ IMAGE UPLOAD ENDPOINTS ============
@app.post("/upload-public-image")
async def upload_public_image(file: UploadFile = File(...)):
    """Upload public image to Cloudinary"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")
        
        contents = await file.read()
        image_url = await image_service.upload_public_image(contents, file.filename)
        
        return {"image_url": image_url}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Public image upload endpoint error: {str(e)}")
        raise HTTPException(500, f"Upload failed: {str(e)}")

@app.post("/upload-user-image", response_model=ImageUploadResponse)
async def upload_user_image(
    file: UploadFile = File(...),
    image_type: str = Form(default="meal"),
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload image for authenticated user"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")
        
        contents = await file.read()
        
        result = await image_service.upload_user_image(
            file_content=contents,
            filename=file.filename,
            image_type=image_type,
            user_id=current_user.username,
            db=db
        )
        
        return ImageUploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"User image upload endpoint error: {str(e)}")
        raise HTTPException(500, f"Image upload failed: {str(e)}")

@app.get("/users/{user_id}/images", response_model=List[UserImageResponse])
async def get_user_images_endpoint(
    user_id: str,
    image_type: Optional[str] = None,
    limit: int = 50,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's images with optional filtering"""
    try:
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        images = await get_user_images(user_id, image_type, limit, db)
        return [
            UserImageResponse(
                image_id=img.id,
                public_id=img.public_id,
                url=img.image_url,
                original_filename=img.original_filename,
                file_size=img.file_size,
                image_type=img.image_type,
                uploaded_at=img.uploaded_at
            )
            for img in images
        ]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Images fetch endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to fetch images: {str(e)}")

@app.delete("/users/{user_id}/images/{image_id}")
async def delete_user_image_endpoint(
    user_id: str,
    image_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user's image"""
    try:
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        image_service = services["image_service"]
        success = await image_service.delete_user_image(user_id, image_id, db)
        if success:
            return {"success": True, "message": "Image deleted successfully"}
        else:
            raise HTTPException(404, "Image not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Image deletion endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to delete image: {str(e)}")

# ============ ACHIEVEMENT ENDPOINTS ============
@app.get("/users/{user_id}/achievements")
async def get_user_achievements(
    user_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's achievements"""
    verify_user_access(current_user, user_id)
    try:
        return await achievement_service.get_user_achievements(user_id, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Achievements fetch endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to fetch achievements: {str(e)}")

# ============ NOTIFICATION ENDPOINTS ============
@app.get("/users/{user_id}/notifications")
async def get_user_notifications(
    user_id: str,
    limit: int = 10,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's smart notifications"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        return await get_user_notifications(user_id, limit, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Notifications fetch endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to fetch notifications: {str(e)}")

@app.post("/users/{user_id}/notifications/{notification_id}/mark-opened")
async def mark_notification_opened(
    user_id: str,
    notification_id: int,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notification as opened"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        success = await mark_notification_opened(user_id, notification_id, db)
        
        if success:
            return {"message": "Notification marked as opened"}
        else:
            raise HTTPException(404, "Notification not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Notification update endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to update notification: {str(e)}")

# ============ NUTRITION STORY ENDPOINTS ============
@app.get("/users/{user_id}/nutrition-story")
async def get_nutrition_story(
    user_id: str,
    story_type: str = "weekly",
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get or generate nutrition story"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        return await get_nutrition_story(user_id, story_type, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Nutrition story endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to generate nutrition story: {str(e)}")

# ============ DAILY SUMMARY ENDPOINTS ============
@app.post("/daily-summary")
async def save_daily_summary(
    request: DailySummaryRequest,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Save daily nutrition summary"""
    try:
        # Verify user access
        if current_user.username != request.user_id:
            raise HTTPException(403, "Access denied")
        
        summary_data = request.dict()
        summary_data["created_at"] = datetime.utcnow()
        
        summary = await save_daily_summary(summary_data, db)
        
        return {"message": "Daily summary saved", "summary_id": summary.id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Daily summary endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to save daily summary: {str(e)}")

@app.get("/users/{user_id}/daily-summary/{date}", response_model=Optional[DailySummaryResponse])
async def get_daily_summary_endpoint(
    user_id: str,
    date: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get daily nutrition summary for specific date"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        summary = await get_daily_summary(user_id, date, db)
        
        if not summary:
            return None
        
        return DailySummaryResponse(
            id=summary.id,
            user_id=summary.user_id,
            date=summary.date,
            summary_json=summary.summary_json,
            calories_total=summary.calories_total,
            macro_split=summary.macro_split,
            created_at=summary.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Daily summary fetch endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to fetch daily summary: {str(e)}")

# ============ AI RECIPE ENDPOINTS ============
@app.post("/ai/generate-recipe", response_model=AIRecipeResponse)
async def generate_custom_recipe(
    request: AIRecipeRequest,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a custom AI recipe based on macro targets and preferences"""
    try:
        # Verify user access
        if current_user.username != request.user_id:
            raise HTTPException(403, "Access denied")
        
        recipe = await recipe_service.generate_custom_recipe(request, db)
        
        return AIRecipeResponse(
            recipe_id=recipe["recipe_id"],
            recipe_name=recipe["recipe_name"],
            description=recipe["description"],
            ingredients=recipe["ingredients"],
            instructions=recipe["instructions"],
            nutrition_info=recipe["nutrition_info"],
            prep_time=recipe["prep_time"],
            cook_time=recipe["cook_time"],
            difficulty_level=recipe.get("difficulty_level", "easy"),
            tags=recipe["tags"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Recipe generation endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to generate recipe: {str(e)}")

@app.get("/users/{user_id}/recipes")
async def get_user_recipes(
    user_id: str,
    limit: int = 10,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's saved AI-generated recipes"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        return await recipe_service.get_user_recipes(user_id, limit, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"User recipes fetch endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to fetch recipes: {str(e)}")

@app.post("/users/{user_id}/recipes/{recipe_id}/rate")
async def rate_recipe_endpoint(
    user_id: str,
    recipe_id: int,
    rating: float,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Rate an AI-generated recipe"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        return await recipe_service.rate_recipe(user_id, recipe_id, rating, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Recipe rating endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to rate recipe: {str(e)}")

# ============ SMART DINNER PREDICTION ENDPOINTS ============
@app.post("/ai/smart-dinner-prediction", response_model=SmartDinnerPredictionResponse)
async def get_smart_dinner_prediction(
    request: SmartDinnerPredictionRequest,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-powered dinner suggestions based on today's intake"""
    try:
        # Verify user access
        if current_user.username != request.user_id:
            raise HTTPException(403, "Access denied")
        
        # Get today's food logs
        today_logs = await get_user_food_logs(request.user_id, request.prediction_date, 50, db)
        
        # Get user's daily targets
        profile = await get_user_profile(request.user_id, db)
        if not profile or not profile.nutrition_goals:
            raise HTTPException(404, "User nutrition goals not found")
        
        # Calculate current intake
        current_intake = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
        for log in today_logs:
            for food in log.foods:
                current_intake["calories"] += food.get("calories", 0)
                current_intake["protein_g"] += food.get("protein_g", 0)
                current_intake["carbs_g"] += food.get("carbs_g", 0)
                current_intake["fat_g"] += food.get("fat_g", 0)
        
        # Get user context
        user_context = build_user_context(profile)
        
        prediction = await ai_service.predict_dinner(
            current_intake=current_intake,
            daily_targets=profile.nutrition_goals,
            user_context=user_context,
            user_id=request.user_id,
            prediction_date=request.prediction_date,
            db=db
        )
        
        return SmartDinnerPredictionResponse(**prediction)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Dinner prediction endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to create dinner prediction: {str(e)}")

@app.get("/users/{user_id}/dinner-predictions")
async def get_dinner_predictions_endpoint(
    user_id: str,
    limit: int = 7,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's recent dinner predictions"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        predictions = await get_dinner_predictions(user_id, limit, db)
        
        return [
            {
                "prediction_id": pred.id,
                "prediction_date": pred.prediction_date,
                "remaining_needs": pred.remaining_needs,
                "suggested_recipes": pred.suggested_recipes,
                "reasoning": pred.reasoning,
                "confidence_score": pred.confidence_score,
                "user_feedback": pred.user_feedback,
                "created_at": pred.created_at
            }
            for pred in predictions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Dinner predictions fetch endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to fetch dinner predictions: {str(e)}")

# ============ NUTRITION TIME TRAVEL ENDPOINTS ============
@app.post("/ai/nutrition-time-travel", response_model=NutritionTimeTravelResponse)
async def create_nutrition_time_travel_projection(
    request: NutritionTimeTravelRequest,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create nutrition time travel projections and goal-based plans"""
    try:
        # Verify user access
        if current_user.username != request.user_id:
            raise HTTPException(403, "Access denied")
        
        projection = await ai_service.create_time_travel_projection(
            user_id=request.user_id,
            projection_type=request.projection_type,
            target_goal=request.target_goal,
            scenario_name=request.scenario_name,
            db=db
        )
        
        return NutritionTimeTravelResponse(**projection)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Time travel projection endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to create time travel projection: {str(e)}")

@app.get("/users/{user_id}/time-travel-scenarios")
async def get_time_travel_scenarios(
    user_id: str,
    limit: int = 5,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's nutrition time travel scenarios"""
    try:
        # Verify user access
        if current_user.username != user_id:
            raise HTTPException(403, "Access denied")
        
        scenarios = await get_time_travel_scenarios(user_id, limit, db)
        
        return [
            {
                "projection_id": scenario.id,
                "scenario_name": scenario.scenario_name,
                "projection_type": scenario.projection_type,
                "target_goal": scenario.target_goal,
                "confidence_score": scenario.confidence_score,
                "created_at": scenario.created_at
            }
            for scenario in scenarios
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Time travel scenarios fetch endpoint error: {str(e)}")
        raise HTTPException(500, f"Failed to fetch time travel scenarios: {str(e)}")

# ============ DEBUG ENDPOINT ============
@app.post("/debug/test-nutrition-advice")
async def debug_test_nutrition_advice(
    user_id: str = "debug_user", 
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to test the new nutrition advice format"""
    try:
        # Create test data
        test_food_log = [
            {
                "name": "Test lunch",
                "calories": 400,
                "protein_g": 13.0,
                "carbs_g": 46.0,
                "fat_g": 18.0
            }
        ]
        
        test_targets = {
            "calories": 2000,
            "protein_g": 112,
            "carbs_g": 250,
            "fat_g": 70
        }
        
        # Test personalized advice
        profile = await get_user_profile(user_id, db)
        user_context = build_user_context(profile) if profile else None
        
        advice = await ai_service.get_nutrition_advice(
            food_log=test_food_log,
            daily_targets=test_targets,
            user_context=user_context,
            user_id=user_id,
            db=db
        )
        
        return {
            "status": "success",
            "prompt_used": "personalized" if user_context else "generic",
            "has_new_format": bool(
                advice.get("nutrients_to_focus_on", [{}])[0]
                .get("suggestions", [{}])[0]
                .get("meal_idea")
            ),
            "suggestion_format": "NEW" if "meal_idea" in str(advice) else "OLD",
            "full_response": advice
        }
        
    except Exception as e:
        print(f"Debug test error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "traceback": "Check server logs for details"
        }

# ============ SYSTEM ENDPOINTS ============
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "6.0",
            "environment": settings.environment,
            "services": {}
        }
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(select(1))
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        try:
            test_client = OpenAI(api_key=settings.openai_api_key, timeout=5.0)
            health_status["services"]["openai"] = "healthy"
        except Exception as e:
            health_status["services"]["openai"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        try:
            import cloudinary
            cloudinary.config(
                cloud_name=settings.cloudinary_cloud_name,
                api_key=settings.cloudinary_api_key,
                api_secret=settings.cloudinary_api_secret
            )
            health_status["services"]["cloudinary"] = "healthy"
        except Exception as e:
            health_status["services"]["cloudinary"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@app.get("/version")
async def get_version():
    """Get API version information"""
    return {
        "version": "6.0",
        "codename": "SIMPLIFIED_REFACTOR",
        "architecture": {
            "files": 7,
            "structure": "modular",
            "services": "dependency_injection",
            "database": "async_sqlalchemy",
            "auth": "jwt_bearer"
        },
        "features": {
            "core": ["meal_analysis", "nutrition_advice", "food_search", "substitutes"],
            "user_management": ["profiles", "achievements", "notifications"],
            "advanced_ai": ["recipe_generation", "dinner_predictions", "time_travel"],
            "storage": ["food_logs", "daily_summaries", "ai_caching", "image_upload"]
        },
        "ai_improvements": [
            "forced_new_response_format", "enhanced_prompt_strictness", 
            "automatic_format_conversion", "robust_validation_system", 
            "fallback_response_protection", "personality_based_responses"
        ],
        "status": "refactored_and_production_ready"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
