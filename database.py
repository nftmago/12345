# app/database.py
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
import os
print("DATABASE_URL:", os.getenv("DATABASE_URL"))
import time
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from config import settings
from models import *

# ============ DATABASE ENGINE SETUP ============
database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url.startswith("sqlite"):
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
else:
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ============ DATABASE DEPENDENCY ============
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# ============ USER FUNCTIONS ============
async def get_user_by_username(username: str, db: AsyncSession) -> Optional[UserDB]:
    """Get a user by username"""
    result = await db.execute(select(UserDB).where(UserDB.username == username))
    return result.scalar_one_or_none()

async def get_user_by_email(email: str, db: AsyncSession) -> Optional[UserDB]:
    """Get a user by email"""
    result = await db.execute(select(UserDB).where(UserDB.email == email))
    return result.scalar_one_or_none()

async def create_user(user_data: dict, db: AsyncSession) -> UserDB:
    """Create a new user"""
    db_user = UserDB(**user_data)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# ============ USER PROFILE FUNCTIONS ============
async def get_user_profile(user_id: str, db: AsyncSession) -> Optional[UserProfileDB]:
    """Get user profile by user_id"""
    result = await db.execute(select(UserProfileDB).where(UserProfileDB.user_id == user_id))
    return result.scalar_one_or_none()

async def save_user_profile(profile_data: dict, db: AsyncSession) -> UserProfileDB:
    """Create or update user profile"""
    stmt = select(UserProfileDB).where(UserProfileDB.user_id == profile_data["user_id"])
    result = await db.execute(stmt)
    db_profile = result.scalars().first()
    
    if db_profile:
        # Update existing profile - explicit is better than implicit
        updatable_fields = [
            'dietary_preferences', 'favorite_foods', 'disliked_foods',
            'cuisine_preferences', 'allergies', 'activity_level',
            'nutrition_goals', 'ai_personality_type',
            'preferred_communication_style', 'coaching_frequency'
        ]
        for field in updatable_fields:
            if field in profile_data:
                setattr(db_profile, field, profile_data[field])
        db_profile.updated_at = datetime.utcnow()
    else:
        # Create new profile
        db_profile = UserProfileDB(**profile_data)
        db.add(db_profile)
    
    await db.commit()
    await db.refresh(db_profile)
    return db_profile

# ============ FOOD LOG FUNCTIONS ============
async def save_food_log(log_data: dict, db: AsyncSession) -> FoodLogDB:
    """Save a food log entry"""
    food_log = FoodLogDB(**log_data)
    db.add(food_log)
    await db.commit()
    await db.refresh(food_log)
    return food_log

async def get_user_food_logs(
    user_id: str, 
    date_filter: Optional[str], 
    limit: int, 
    db: AsyncSession
) -> List[FoodLogDB]:
    """Get user's food logs with optional date filtering"""
    query = select(FoodLogDB).where(FoodLogDB.user_id == user_id)
    
    if date_filter:
        query = query.where(FoodLogDB.date_string == date_filter)
    
    query = query.order_by(FoodLogDB.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_food_logs_count(user_id: str, db: AsyncSession) -> int:
    """Get total count of user's food logs"""
    result = await db.execute(
        select(func.count(FoodLogDB.id)).where(FoodLogDB.user_id == user_id)
    )
    return result.scalar()

async def get_recent_food_logs(user_id: str, days: int, db: AsyncSession) -> List[FoodLogDB]:
    """Get user's food logs from recent days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    result = await db.execute(
        select(FoodLogDB).where(
            FoodLogDB.user_id == user_id,
            FoodLogDB.created_at >= start_date,
            FoodLogDB.created_at <= end_date
        ).order_by(FoodLogDB.created_at.desc())
    )
    return result.scalars().all()

# ============ AI CACHE FUNCTIONS ============
async def get_cached_ai_response(prompt_hash: str, user_id: str, db: AsyncSession) -> Optional[str]:
    """Get cached AI response if exists and not expired"""
    stmt = select(AIResponseCacheDB).where(
        AIResponseCacheDB.user_id == user_id,
        AIResponseCacheDB.prompt_hash == prompt_hash,
        AIResponseCacheDB.created_at >= datetime.utcnow() - timedelta(seconds=settings.cache_ttl_seconds)
    ).order_by(AIResponseCacheDB.created_at.desc())
    
    result = await db.execute(stmt)
    cached = result.scalars().first()
    return cached.response if cached else None

async def cache_ai_response(prompt: str, response: str, user_id: str, db: AsyncSession):
    """Cache AI response for future use"""
    try:
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        
        cache_entry = AIResponseCacheDB(
            user_id=user_id,
            prompt_hash=prompt_hash,
            prompt=prompt,
            response=response,
            created_at=datetime.utcnow()
        )
        
        db.add(cache_entry)
        await db.commit()
    except Exception as e:
        print(f"Cache save error: {str(e)}")
        await db.rollback()

# ============ ACHIEVEMENT FUNCTIONS ============
async def check_and_award_achievements(user_id: str, db: AsyncSession) -> List[UserAchievementDB]:
    """Check for new achievements and award them"""
    try:
        # Get user's food log count
        logs_result = await db.execute(
            select(func.count(FoodLogDB.id)).where(FoodLogDB.user_id == user_id)
        )
        total_logs = logs_result.scalar()
        
        # Get recent logs for streak checking
        recent_logs = await db.execute(
            select(FoodLogDB.date_string)
            .where(FoodLogDB.user_id == user_id)
            .order_by(FoodLogDB.created_at.desc())
            .limit(10)
        )
        dates = [log[0] for log in recent_logs.fetchall()]
        
        achievements = []
        
        # First meal achievement
        if total_logs == 1:
            achievement = UserAchievementDB(
                user_id=user_id,
                achievement_type="milestone",
                achievement_name="First Steps",
                description="Logged your first meal! 🎉",
                points=10,
                badge_icon="🌟"
            )
            db.add(achievement)
            achievements.append(achievement)
        
        # Week warrior achievement
        if total_logs >= 7:
            # Check if this achievement already exists
            existing = await db.execute(
                select(UserAchievementDB).where(
                    UserAchievementDB.user_id == user_id,
                    UserAchievementDB.achievement_name == "Week Warrior"
                )
            )
            if not existing.scalar_one_or_none():
                achievement = UserAchievementDB(
                    user_id=user_id,
                    achievement_type="streak",
                    achievement_name="Week Warrior",
                    description="7 days of consistent logging! 🔥",
                    points=50,
                    badge_icon="🔥"
                )
                db.add(achievement)
                achievements.append(achievement)
        
        if achievements:
            await db.commit()
            for ach in achievements:
                await db.refresh(ach)
        
        return achievements
        
    except Exception as e:
        print(f"Achievement check error: {str(e)}")
        await db.rollback()
        return []

async def get_user_achievements(user_id: str, db: AsyncSession) -> List[UserAchievementDB]:
    """Get user's achievements"""
    result = await db.execute(
        select(UserAchievementDB).where(
            UserAchievementDB.user_id == user_id
        ).order_by(UserAchievementDB.earned_date.desc())
    )
    return result.scalars().all()

# ============ NOTIFICATION FUNCTIONS ============
async def create_smart_notification(
    user_id: str, 
    notification_type: str, 
    title: str, 
    message: str, 
    scheduled_time: datetime, 
    db: AsyncSession
) -> Optional[int]:
    """Create a smart notification for the user"""
    try:
        notification = SmartNotificationDB(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            scheduled_time=scheduled_time
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification.id
    except Exception as e:
        print(f"Notification creation error: {str(e)}")
        await db.rollback()
        return None

async def get_user_notifications(user_id: str, limit: int, db: AsyncSession) -> List[SmartNotificationDB]:
    """Get user's smart notifications"""
    result = await db.execute(
        select(SmartNotificationDB).where(
            SmartNotificationDB.user_id == user_id
        ).order_by(SmartNotificationDB.scheduled_time.desc()).limit(limit)
    )
    return result.scalars().all()

async def mark_notification_opened(notification_id: int, user_id: str, db: AsyncSession) -> bool:
    """Mark notification as opened"""
    try:
        result = await db.execute(
            select(SmartNotificationDB).where(
                SmartNotificationDB.id == notification_id,
                SmartNotificationDB.user_id == user_id
            )
        )
        notification = result.scalars().first()
        
        if not notification:
            return False
        
        notification.opened = True
        await db.commit()
        return True
    except Exception as e:
        print(f"Notification update error: {str(e)}")
        await db.rollback()
        return False

# ============ DAILY SUMMARY FUNCTIONS ============
async def save_daily_summary(summary_data: dict, db: AsyncSession) -> DailySummaryDB:
    """Save daily nutrition summary"""
    summary = DailySummaryDB(**summary_data)
    db.add(summary)
    await db.commit()
    await db.refresh(summary)
    return summary

async def get_daily_summary(user_id: str, date: str, db: AsyncSession) -> Optional[DailySummaryDB]:
    """Get daily nutrition summary for specific date"""
    result = await db.execute(
        select(DailySummaryDB).where(
            DailySummaryDB.user_id == user_id,
            DailySummaryDB.date == date
        )
    )
    return result.scalar_one_or_none()

# ============ NUTRITION STORY FUNCTIONS ============
async def generate_nutrition_story(user_id: str, story_type: str, db: AsyncSession) -> Optional[Dict]:
    """Generate a nutrition story for the user"""
    try:
        # Get user's recent food logs
        logs = await get_recent_food_logs(user_id, 7 if story_type == "weekly" else 30, db)
        
        if not logs:
            return None
        
        # Analyze patterns
        total_days = len(set(log.date_string for log in logs))
        total_calories = sum(log.total_calories for log in logs)
        meal_types = [log.meal_time for log in logs]
        unique_foods = set()
        for log in logs:
            for food in log.foods:
                unique_foods.add(food.get('name', ''))
        
        # Create story content
        story_content = {
            "total_meals_logged": len(logs),
            "total_calories": total_calories,
            "avg_daily_calories": total_calories / max(total_days, 1),
            "food_variety": len(unique_foods),
            "most_common_meal_type": max(set(meal_types), key=meal_types.count) if meal_types else "breakfast",
            "consistency_score": total_days * 10  # Score out of 70 for weekly
        }
        
        insights = [
            f"You logged {len(logs)} meals this week - amazing consistency!",
            f"You tried {len(unique_foods)} different foods - great variety!",
            f"Your favorite meal time is {story_content['most_common_meal_type']}"
        ]
        
        # Save story to database
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7 if story_type == "weekly" else 30)
        
        story = NutritionStoryDB(
            user_id=user_id,
            story_type=story_type,
            story_title=f"Your {story_type.title()} Nutrition Journey",
            story_content=story_content,
            time_period=f"{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}",
            key_insights=insights
        )
        db.add(story)
        await db.commit()
        await db.refresh(story)
        
        return {
            "title": story.story_title,
            "content": story_content,
            "insights": insights,
            "story_id": story.id
        }
        
    except Exception as e:
        print(f"Story generation error: {str(e)}")
        await db.rollback()
        return None

async def get_nutrition_story(user_id: str, story_type: str, db: AsyncSession) -> Optional[NutritionStoryDB]:
    """Get recent nutrition story"""
    result = await db.execute(
        select(NutritionStoryDB).where(
            NutritionStoryDB.user_id == user_id,
            NutritionStoryDB.story_type == story_type,
            NutritionStoryDB.created_at >= datetime.utcnow() - timedelta(days=1)
        ).order_by(NutritionStoryDB.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()

# ============ AI RECIPE FUNCTIONS ============
async def save_ai_recipe(recipe_data: dict, db: AsyncSession) -> AIRecipeDB:
    """Save AI-generated recipe"""
    recipe = AIRecipeDB(**recipe_data)
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)
    return recipe

async def get_user_recipes(user_id: str, limit: int, db: AsyncSession) -> List[AIRecipeDB]:
    """Get user's saved AI-generated recipes"""
    result = await db.execute(
        select(AIRecipeDB).where(
            AIRecipeDB.user_id == user_id
        ).order_by(AIRecipeDB.created_at.desc()).limit(limit)
    )
    return result.scalars().all()

async def rate_recipe(recipe_id: int, user_id: str, rating: float, db: AsyncSession) -> bool:
    """Rate an AI-generated recipe"""
    try:
        result = await db.execute(
            select(AIRecipeDB).where(
                AIRecipeDB.id == recipe_id,
                AIRecipeDB.user_id == user_id
            )
        )
        recipe = result.scalars().first()
        
        if not recipe:
            return False
        
        recipe.user_rating = rating
        await db.commit()
        return True
    except Exception as e:
        print(f"Recipe rating error: {str(e)}")
        await db.rollback()
        return False

# ============ SMART DINNER PREDICTION FUNCTIONS ============
async def save_dinner_prediction(prediction_data: dict, db: AsyncSession) -> SmartDinnerPredictionDB:
    """Save smart dinner prediction"""
    prediction = SmartDinnerPredictionDB(**prediction_data)
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)
    return prediction

async def get_dinner_predictions(user_id: str, limit: int, db: AsyncSession) -> List[SmartDinnerPredictionDB]:
    """Get user's recent dinner predictions"""
    result = await db.execute(
        select(SmartDinnerPredictionDB).where(
            SmartDinnerPredictionDB.user_id == user_id
        ).order_by(SmartDinnerPredictionDB.created_at.desc()).limit(limit)
    )
    return result.scalars().all()

# ============ NUTRITION TIME TRAVEL FUNCTIONS ============
async def save_time_travel_projection(projection_data: dict, db: AsyncSession) -> NutritionTimeTravelDB:
    """Save nutrition time travel projection"""
    projection = NutritionTimeTravelDB(**projection_data)
    db.add(projection)
    await db.commit()
    await db.refresh(projection)
    return projection

async def get_time_travel_scenarios(user_id: str, limit: int, db: AsyncSession) -> List[NutritionTimeTravelDB]:
    """Get user's nutrition time travel scenarios"""
    result = await db.execute(
        select(NutritionTimeTravelDB).where(
            NutritionTimeTravelDB.user_id == user_id
        ).order_by(NutritionTimeTravelDB.created_at.desc()).limit(limit)
    )
    return result.scalars().all()

# ============ USER IMAGE FUNCTIONS ============
async def save_user_image(image_data: dict, db: AsyncSession) -> UserImageDB:
    """Save user image data"""
    image = UserImageDB(**image_data)
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image

async def get_user_images(user_id: str, image_type: Optional[str], limit: int, db: AsyncSession) -> List[UserImageDB]:
    """Get user's images with optional filtering"""
    query = select(UserImageDB).where(UserImageDB.user_id == user_id)
    if image_type:
        query = query.where(UserImageDB.image_type == image_type)
    query = query.order_by(UserImageDB.uploaded_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_image_by_id(user_id: str, image_id: str, db: AsyncSession) -> Optional[UserImageDB]:
    """Get specific user image"""
    result = await db.execute(
        select(UserImageDB).where(
            UserImageDB.id == image_id,
            UserImageDB.user_id == user_id
        )
    )
    return result.scalar_one_or_none()

async def delete_user_image_from_db(user_id: str, image_id: str, db: AsyncSession) -> Optional[UserImageDB]:
    """Delete user image and return the deleted image data"""
    result = await db.execute(
        select(UserImageDB).where(
            UserImageDB.id == image_id,
            UserImageDB.user_id == user_id
        )
    )
    image = result.scalar_one_or_none()
    if image:
        await db.delete(image)
        await db.commit()
    return image

async def delete_user_image(user_id: str, image_id: str, db: AsyncSession) -> Optional[UserImageDB]:
    """Alias for delete_user_image_from_db for compatibility with services.py"""
    return await delete_user_image_from_db(user_id, image_id, db)

# ============ HEALTH CHECK FUNCTIONS ============
async def get_database_stats(db: AsyncSession) -> Dict[str, int]:
    """Get database statistics for health check"""
    try:
        stats = {}
        
        # Count records in each table
        tables = [
            ("user_profiles", UserProfileDB, UserProfileDB.user_id),
            ("food_logs", FoodLogDB, FoodLogDB.id),
            ("ai_cache_entries", AIResponseCacheDB, AIResponseCacheDB.id),
            ("daily_summaries", DailySummaryDB, DailySummaryDB.id),
            ("achievements", UserAchievementDB, UserAchievementDB.id),
            ("notifications", SmartNotificationDB, SmartNotificationDB.id),
            ("nutrition_stories", NutritionStoryDB, NutritionStoryDB.id),
            ("ai_recipes", AIRecipeDB, AIRecipeDB.id),
            ("time_travel_projections", NutritionTimeTravelDB, NutritionTimeTravelDB.id),
            ("dinner_predictions", SmartDinnerPredictionDB, SmartDinnerPredictionDB.id),
        ]
        
        for name, model, pk_column in tables:
            try:
                result = await db.execute(select(func.count(pk_column)))
                stats[name] = result.scalar()
            except Exception:
                stats[name] = 0
        
        # Check if UserImageDB table exists
        try:
            result = await db.execute(select(func.count(UserImageDB.id)))
            stats["user_images"] = result.scalar()
        except Exception:
            stats["user_images"] = 0
        
        return stats
        
    except Exception as e:
        print(f"Database stats error: {str(e)}")
        return {}
