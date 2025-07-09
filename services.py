# app/services.py
import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from openai import OpenAI
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import *
from database import (
    get_user_profile, save_user_profile, save_food_log, get_user_food_logs,
    get_cached_ai_response, cache_ai_response, check_and_award_achievements,
    create_smart_notification, get_user_notifications, mark_notification_opened,
    save_ai_recipe, get_user_recipes, rate_recipe, save_dinner_prediction,
    save_time_travel_projection, save_user_image, get_user_images,
    get_user_image_by_id, delete_user_image_from_db, get_database_stats,
    get_user_achievements, get_recent_food_logs, generate_nutrition_story,
    get_nutrition_story, save_daily_summary, get_daily_summary
)
from utils import AI_PERSONALITIES, generic_nutrition_prompt, create_fallback_nutrition_response, create_nutrition_advice_prompt

# ============ AI SERVICE ============
class AIService:
    """AI service for OpenAI integration with caching"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key, timeout=30.0)
    
    async def analyze_meal(
        self, 
        user_input: str,
        image_url: Optional[str] = None,
        corrections: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Analyze meal from image or text with caching"""
        try:
            prompt = meal_analysis_prompt(user_input, corrections)
            model = settings.vision_model if image_url else settings.text_model
            
            # Check cache for non-image requests
            if settings.enable_ai_caching and db and user_id and not image_url:
                prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
                cached = await get_cached_ai_response(prompt_hash, user_id, db)
                if cached:
                    result = parse_json_response(cached)
                    if result:
                        return validate_meal_response(result)
            
            # Make AI call
            response = await self._call_openai(prompt, model, image_url, user_id)
            
            # Cache response for non-image requests
            if settings.enable_ai_caching and db and user_id and not image_url:
                await cache_ai_response(prompt, response, user_id, db)
            
            result = parse_json_response(response)
            if not result:
                # Retry with simpler prompt
                simple_prompt = f"Analyze this meal: {user_input}. Return JSON with meal_name, meal_type (breakfast/lunch/dinner/snack), foods array, and total_calories."
                response = await self._call_openai(simple_prompt, model, image_url, user_id)
                result = parse_json_response(response)
            
            if not result:
                return create_fallback_meal_response()
            
            return validate_meal_response(result)
            
        except Exception as e:
            print(f"Meal analysis error: {str(e)}")
            return create_fallback_meal_response()
    
    async def get_nutrition_advice(
        self,
        food_log: List[Dict],
        daily_targets: Dict[str, float],
        user_context: Optional[Dict] = None,
        user_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get nutrition advice with simplified prompting"""
        try:
            prompt = create_nutrition_advice_prompt(food_log, daily_targets, user_context)
            if settings.enable_ai_caching and db and user_id:
                prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
                cached = await get_cached_ai_response(prompt_hash, user_id, db)
                if cached:
                    result = self._parse_json_response(cached)
                    if result and self._validate_nutrition_response(result):
                        return result
            response = await self._call_openai(prompt, settings.text_model, user_id=user_id)
            if settings.enable_ai_caching and db and user_id:
                await cache_ai_response(prompt, response, user_id, db)
            result = self._parse_json_response(response)
            if not result or not self._validate_nutrition_response(result):
                return self._create_fallback_nutrition_response()
            return result
        except Exception as e:
            print(f"Nutrition advice error: {str(e)}")
            return self._create_fallback_nutrition_response()
    
    async def _call_openai(
        self, 
        prompt: str, 
        model: str, 
        image_url: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Internal OpenAI API call with timeout and error handling"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a world-class nutrition expert. Provide responses in valid JSON format."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            if image_url:
                messages[1]["content"].append({"type": "image_url", "image_url": {"url": image_url}})

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                user=user_id  # Pass user ID for abuse monitoring
            )
            
            return response.choices[0].message.content
        
        except asyncio.TimeoutError:
            print("OpenAI request timed out")
            raise HTTPException(504, "AI service timed out")
            
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise HTTPException(500, "AI service error")

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        try:
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            parsed = json.loads(response.strip())
            return self._fix_nan_values(parsed)
        except Exception as e:
            print(f"JSON parsing error: {str(e)}")
            return None

    def _fix_nan_values(self, obj):
        if isinstance(obj, dict):
            return {k: self._fix_nan_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._fix_nan_values(item) for item in obj]
        elif isinstance(obj, float) and (obj != obj):
            return 0.0
        elif obj in ["NaN", "nan"]:
            return 0.0
        return obj

    def _validate_nutrition_response(self, data: Dict[str, Any]) -> bool:
        required_fields = ["overall_summary", "nutrients_to_focus_on", "achievements", "tips"]
        if not all(field in data for field in required_fields):
            return False
        nutrients = data.get("nutrients_to_focus_on", [])
        if not nutrients:
            return False
        for nutrient in nutrients:
            if not isinstance(nutrient, dict):
                return False
            if "suggestions" not in nutrient:
                return False
            suggestions = nutrient["suggestions"]
            if not suggestions:
                return False
            for suggestion in suggestions:
                required_suggestion_fields = [
                    "meal_idea", "description", "total_calories", 
                    "protein_provided", "percentage_coverage"
                ]
                if not all(field in suggestion for field in required_suggestion_fields):
                    return False
        return True

    def _create_fallback_nutrition_response(self) -> Dict[str, Any]:
        return {
            "overall_summary": "You're making great progress! Let's focus on getting some quality protein today.",
            "nutrients_to_focus_on": [{
                "nutrient": "protein",
                "current_intake": 0,
                "target": 120,
                "deficit": 120,
                "suggestions": [{
                    "meal_idea": "Greek Yogurt Power Bowl",
                    "description": "1 cup Greek yogurt + granola + fresh berries + almond butter drizzle",
                    "total_calories": 340,
                    "protein_provided": 25.0,
                    "carbs_provided": 28.0,
                    "fat_provided": 12.0,
                    "percentage_coverage": {"protein": 21, "carbs": 11, "fat": 17},
                    "meal_type": "snack",
                    "easy_to_make": True,
                    "why_perfect": "Perfect protein boost that covers 21% of your daily needs"
                }],
                "why_important": "Protein helps build muscle and keeps you satisfied longer"
            }],
            "achievements": ["You're building healthy tracking habits!"],
            "tips": ["Focus on adding protein to your next meal or snack"]
        }
    
    async def search_food(self, query: str) -> Dict[str, Any]:
        """Search for food information"""
        try:
            prompt = food_search_prompt(query)
            response = await self._call_openai(prompt, settings.search_model)
            result = parse_json_response(response)
            
            if not result:
                raise HTTPException(422, "No foods found")
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            print(f"Food search error: {str(e)}")
            raise HTTPException(500, "Search failed")
    
    async def find_substitutes(
        self, 
        food_name: str, 
        restrictions: List[str], 
        goals: str
    ) -> Dict[str, Any]:
        """Find food substitutes with caching"""
        try:
            # Check simple cache
            cache_key = f"{food_name}:{','.join(restrictions)}:{goals}"
            cached_result = get_cached_substitute(cache_key)
            if cached_result:
                return cached_result
            
            prompt = substitute_prompt(food_name, restrictions, goals)
            response = await self._call_openai(prompt, settings.search_model)
            result = parse_json_response(response)
            
            if not result:
                raise HTTPException(422, "Could not find substitutes")
            
            # Cache result
            cache_substitute(cache_key, result)
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            print(f"Substitute search error: {str(e)}")
            raise HTTPException(500, "Substitute search failed")
    
    async def generate_recipe(
        self,
        target_macros: Dict[str, float],
        dietary_restrictions: List[str],
        user_context: Dict[str, Any],
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate AI recipe based on requirements"""
        try:
            prompt = recipe_generation_prompt(target_macros, dietary_restrictions, user_context)
            response = await self._call_openai(prompt, settings.text_model, user_id=user_id)
            result = parse_json_response(response)
            
            if not result:
                raise HTTPException(422, "Could not generate recipe")
            
            validated_result = validate_recipe_response(result)
            
            # Save recipe to database
            recipe_data = {
                "user_id": user_id,
                "recipe_name": validated_result["recipe_name"],
                "description": validated_result["description"],
                "ingredients": validated_result["ingredients"],
                "instructions": validated_result["instructions"],
                "nutrition_info": validated_result["nutrition_info"],
                "target_macros": target_macros,
                "dietary_restrictions": dietary_restrictions,
                "difficulty_level": "easy",
                "prep_time": validated_result["prep_time"],
                "cook_time": validated_result["cook_time"],
                "servings": 1,
                "tags": validated_result.get("tags", []),
                "created_at": datetime.utcnow()
            }
            
            recipe = await save_ai_recipe(recipe_data, db)
            
            return {
                "recipe_id": recipe.id,
                **validated_result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Recipe generation error: {str(e)}")
            raise HTTPException(500, "Recipe generation failed")
    
    async def predict_dinner(
        self,
        current_intake: Dict[str, float],
        daily_targets: Dict[str, float],
        user_context: Dict[str, Any],
        user_id: str,
        prediction_date: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Predict optimal dinner based on daily intake"""
        try:
            prompt = dinner_prediction_prompt(current_intake, daily_targets, user_context)
            response = await self._call_openai(prompt, settings.text_model, user_id=user_id)
            result = parse_json_response(response)
            
            if not result:
                raise HTTPException(422, "Could not generate dinner prediction")
            
            # Calculate remaining needs
            remaining_needs = {}
            for macro, target in daily_targets.items():
                current = current_intake.get(macro, 0)
                remaining_needs[macro] = max(0, target - current)
            
            # Save prediction to database
            prediction_data = {
                "user_id": user_id,
                "prediction_date": prediction_date,
                "current_intake": current_intake,
                "remaining_needs": remaining_needs,
                "suggested_recipes": result.get("suggestions", []),
                "backup_options": result.get("backup_options", []),
                "reasoning": result.get("reasoning", "AI-generated dinner suggestions"),
                "confidence_score": 0.85,
                "created_at": datetime.utcnow()
            }
            
            prediction = await save_dinner_prediction(prediction_data, db)
            
            return {
                "prediction_id": prediction.id,
                "remaining_needs": remaining_needs,
                "suggested_recipes": result.get("suggestions", []),
                "backup_options": result.get("backup_options", []),
                "reasoning": result.get("reasoning", "AI-generated suggestions"),
                "confidence_score": 0.85
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Dinner prediction error: {str(e)}")
            raise HTTPException(500, "Dinner prediction failed")
    
    async def create_time_travel_projection(
        self,
        user_id: str,
        projection_type: str,
        target_goal: Dict[str, Any],
        scenario_name: Optional[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create nutrition time travel projections"""
        try:
            # Get user's current eating patterns
            logs = await get_recent_food_logs(user_id, 30, db)
            
            if not logs:
                raise HTTPException(404, "Not enough data for projection")
            
            # Analyze current patterns
            total_days = len(set(log.date_string for log in logs))
            avg_daily_calories = sum(log.total_calories for log in logs) / max(total_days, 1)
            
            # Calculate average macros
            total_protein = sum(
                sum(food.get('protein_g', 0) for food in log.foods) 
                for log in logs
            )
            total_carbs = sum(
                sum(food.get('carbs_g', 0) for food in log.foods) 
                for log in logs
            )
            total_fat = sum(
                sum(food.get('fat_g', 0) for food in log.foods) 
                for log in logs
            )
            
            current_pattern = {
                "avg_daily_calories": avg_daily_calories,
                "avg_protein": total_protein / max(total_days, 1),
                "avg_carbs": total_carbs / max(total_days, 1),
                "avg_fat": total_fat / max(total_days, 1),
                "consistency_score": total_days / 30 * 100
            }
            
            # Get user context
            profile = await get_user_profile(user_id, db)
            user_context = build_user_context(profile) if profile else {}
            
            prompt = time_travel_prompt(current_pattern, target_goal, user_context)
            response = await self._call_openai(prompt, settings.text_model, user_id=user_id)
            result = parse_json_response(response)
            
            if not result:
                raise HTTPException(422, "Could not generate time travel projection")
            
            # Save projection to database
            projection_data = {
                "user_id": user_id,
                "projection_type": projection_type,
                "current_pattern": current_pattern,
                "target_goal": target_goal,
                "projected_outcome": result.get("projected_outcome", {}),
                "recommended_changes": result.get("recommended_changes", []),
                "timeline": result.get("timeline", []),
                "confidence_score": result.get("confidence_score", 0.75),
                "scenario_name": scenario_name or f"Goal: {target_goal}",
                "created_at": datetime.utcnow()
            }
            
            projection = await save_time_travel_projection(projection_data, db)
            
            return {
                "projection_id": projection.id,
                "scenario_name": projection.scenario_name,
                "current_pattern": current_pattern,
                "projected_outcome": result.get("projected_outcome", {}),
                "recommended_changes": result.get("recommended_changes", []),
                "timeline": result.get("timeline", []),
                "confidence_score": result.get("confidence_score", 0.75),
                "key_insights": result.get("key_insights", [])
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Time travel projection error: {str(e)}")
            raise HTTPException(500, "Time travel projection failed")
    
# ============ NUTRITION SERVICE ============
class NutritionService:
    """Nutrition service for meal analysis and food logging"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    async def analyze_meal(
        self, 
        user_input: str,
        image_url: Optional[str] = None,
        corrections: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Analyze meal and return structured nutrition data"""
        try:
            result = await self.ai_service.analyze_meal(
                user_input, image_url, corrections, user_id, db
            )
            
            # Ensure proper meal_type fallback
            if not result.get("meal_type") or result["meal_type"] not in ["breakfast", "lunch", "dinner", "snack"]:
                result["meal_type"] = "snack"
            
            result["analysis_method"] = "vision" if image_url else "text"
            return result
            
        except Exception as e:
            print(f"Meal analysis service error: {str(e)}")
            return create_fallback_meal_response()
    
    async def save_food_log_with_achievements(
        self, 
        request: SaveFoodLogRequest, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Save food log and check for achievements"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            log_data = {
                "user_id": request.user_id,
                "meal_time": request.meal_time,
                "foods": [food.dict() for food in request.foods],
                "total_calories": request.total_calories,
                "created_at": datetime.utcnow(),
                "date_string": today
            }
            
            food_log = await save_food_log(log_data, db)
            achievements = await check_and_award_achievements(request.user_id, db)
            
            # Create smart notification for next meal if appropriate
            if request.meal_time == "breakfast":
                lunch_time = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
                if lunch_time > datetime.now():
                    await create_smart_notification(
                        user_id=request.user_id,
                        notification_type="reminder",
                        title="Lunch Time Approaching!",
                        message="Don't forget to log your lunch and keep up the great tracking! 🥗",
                        scheduled_time=lunch_time,
                        db=db
                    )
            
            return {
                "message": "Food log saved",
                "log_id": str(food_log.id),
                "achievements": [
                    {
                        "name": ach.achievement_name,
                        "description": ach.description,
                        "points": ach.points,
                        "badge": ach.badge_icon
                    }
                    for ach in achievements
                ]
            }
            
        except Exception as e:
            print(f"Food log service error: {str(e)}")
            raise HTTPException(500, f"Failed to save food log: {str(e)}")
    
    async def get_personalized_advice(
        self, 
        user_id: str,
        food_log: List[FoodLogItem],
        daily_targets: Dict[str, float],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get personalized nutrition advice for user"""
        try:
            # Get user profile
            profile = await get_user_profile(user_id, db)
            user_context = build_user_context(profile) if profile else None
            
            # Get AI advice
            advice = await self.ai_service.get_nutrition_advice(
                [item.dict() for item in food_log],
                daily_targets,
                user_context,
                user_id,
                db
            )
            
            # Add personalized insights if we have context
            if user_context and "personalized_insights" not in advice:
                advice["personalized_insights"] = [
                    "Your food choices are getting better each day!",
                    f"You've logged {len(food_log)} meals today - great consistency!"
                ]
            
            return advice
            
        except Exception as e:
            print(f"Personalized advice service error: {str(e)}")
            raise HTTPException(500, f"Failed to get personalized advice: {str(e)}")
    
    async def get_user_food_logs(
        self, 
        user_id: str, 
        date_filter: Optional[str] = None,
        limit: int = 50,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Get user's food logs with optional date filtering"""
        try:
            food_logs = await get_user_food_logs(user_id, date_filter, limit, db)
            
            return [
                {
                    "id": log.id,
                    "meal_time": log.meal_time,
                    "foods": log.foods or [],
                    "total_calories": log.total_calories,
                    "created_at": log.created_at,
                    "date_string": log.date_string
                }
                for log in food_logs
            ]
        except Exception as e:
            print(f"Food logs service error: {str(e)}")
            raise HTTPException(500, f"Failed to get food logs: {str(e)}")

# ============ USER SERVICE ============
class UserService:
    """User service for profile and user management"""
    
    async def create_or_update_profile(
        self, 
        profile_data: UserProfile, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create or update user profile"""
        try:
            await save_user_profile(profile_data.dict(), db)
            return {"message": "Profile saved", "user_id": profile_data.user_id}
        except Exception as e:
            print(f"Profile service error: {str(e)}")
            raise HTTPException(500, f"Failed to save profile: {str(e)}")
    
    async def get_user_profile(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get user profile"""
        try:
            profile = await get_user_profile(user_id, db)
            if not profile:
                raise HTTPException(404, "Profile not found")
            
            return {
                "user_id": profile.user_id,
                "dietary_preferences": profile.dietary_preferences or [],
                "favorite_foods": profile.favorite_foods or [],
                "disliked_foods": profile.disliked_foods or [],
                "cuisine_preferences": profile.cuisine_preferences or [],
                "allergies": profile.allergies or [],
                "activity_level": profile.activity_level or "normal",
                "nutrition_goals": profile.nutrition_goals or {},
                "ai_personality_type": profile.ai_personality_type or "supportive",
                "preferred_communication_style": profile.preferred_communication_style or "encouraging",
                "coaching_frequency": profile.coaching_frequency or "daily",
                "updated_at": profile.updated_at.isoformat() if hasattr(profile.updated_at, 'isoformat') else profile.updated_at
            }
        except HTTPException:
            raise
        except Exception as e:
            print(f"Get profile service error: {str(e)}")
            raise HTTPException(500, f"Failed to fetch profile: {str(e)}")
    
    async def update_ai_personality(
        self, 
        user_id: str, 
        personality_type: str, 
        communication_style: str, 
        coaching_frequency: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Update user's AI personality preferences"""
        try:
            if personality_type not in AI_PERSONALITIES:
                raise HTTPException(400, f"Invalid personality type. Choose from: {list(AI_PERSONALITIES.keys())}")
            
            profile = await get_user_profile(user_id, db)
            if not profile:
                raise HTTPException(404, "User profile not found")
            
            profile_data = {
                "user_id": user_id,
                "dietary_preferences": profile.dietary_preferences,
                "favorite_foods": profile.favorite_foods,
                "disliked_foods": profile.disliked_foods,
                "cuisine_preferences": profile.cuisine_preferences,
                "allergies": profile.allergies,
                "activity_level": profile.activity_level,
                "nutrition_goals": profile.nutrition_goals,
                "ai_personality_type": personality_type,
                "preferred_communication_style": communication_style,
                "coaching_frequency": coaching_frequency,
                "updated_at": time.time()
            }
            
            await save_user_profile(profile_data, db)
            
            return {
                "message": "AI personality updated",
                "personality_type": personality_type,
                "communication_style": communication_style,
                "coaching_frequency": coaching_frequency
            }
        except HTTPException:
            raise
        except Exception as e:
            print(f"Personality update service error: {str(e)}")
            raise HTTPException(500, f"Failed to update AI personality: {str(e)}")

# ============ IMAGE SERVICE ============
import cloudinary
import cloudinary.uploader
from uuid import uuid4
import filetype
from PIL import Image
import io

class ImageService:
    """Image service for Cloudinary integration"""
    
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret
        )
    
    async def upload_public_image(self, file_content: bytes, filename: str) -> str:
        """Upload public image to Cloudinary"""
        try:
            # Validate file
            self._validate_image(file_content)
            
            upload_result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                file_content,
                resource_type="image",
                folder="nutrition_app",
                quality="auto:good"
            )
            
            return upload_result.get("secure_url")
            
        except Exception as e:
            print(f"Public image upload error: {str(e)}")
            raise HTTPException(500, f"Upload failed: {str(e)}")
    
    async def upload_user_image(
        self, 
        file_content: bytes, 
        filename: str, 
        image_type: str, 
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Upload user image with database storage"""
        try:
            # Validate file
            self._validate_image(file_content)
            
            # Generate unique public_id
            public_id = f"user_{user_id}_{image_type}_{uuid4().hex[:8]}"
            
            # Upload to Cloudinary
            upload_result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                file_content,
                public_id=public_id,
                folder=f"nutai/users/{user_id}/{image_type}",
                overwrite=False,
                resource_type="image",
                quality="auto:good",
                fetch_format="auto"
            )
            
            image_url = upload_result.get("secure_url")
            
            # Save to database
            image_data = {
                "user_id": user_id,
                "public_id": public_id,
                "image_url": image_url,
                "original_filename": filename,
                "file_size": len(file_content),
                "image_type": image_type,
                "uploaded_at": datetime.utcnow()
            }
            
            new_image = await save_user_image(image_data, db)
            
            return {
                "success": True,
                "image_id": new_image.id,
                "url": image_url,
                "public_id": public_id,
                "image_type": image_type,
                "uploaded_at": new_image.uploaded_at
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"User image upload error: {str(e)}")
            raise HTTPException(500, f"Image upload failed: {str(e)}")
    
    async def delete_user_image(
        self, 
        user_id: str, 
        image_id: str, 
        db: AsyncSession
    ) -> bool:
        """Delete user image from Cloudinary and database"""
        try:
            # Get image from database
            image = await get_user_image_by_id(user_id, image_id, db)
            if not image:
                raise HTTPException(404, "Image not found")
            
            # Delete from Cloudinary
            try:
                await asyncio.to_thread(cloudinary.uploader.destroy, image.public_id)
            except Exception as e:
                print(f"Cloudinary deletion error: {str(e)}")
                # Continue with database deletion even if Cloudinary fails
            
            # Delete from database
            deleted_image = await delete_user_image_from_db(user_id, image_id, db)
            
            return deleted_image is not None
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Image deletion error: {str(e)}")
            raise HTTPException(500, f"Failed to delete image: {str(e)}")
    
    def _validate_image(self, file_content: bytes):
        """Validate image file"""
        # Check file size (max 10MB)
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(400, "Image too large (max 10MB)")
        
        # Validate file type
        kind = filetype.guess(file_content)
        if not kind or not kind.mime.startswith('image/'):
            raise HTTPException(400, "File must be an image")
        
        # Validate image format using PIL
        try:
            img = Image.open(io.BytesIO(file_content))
            img.verify()
        except Exception:
            raise HTTPException(400, "Invalid image format")

# ============ NOTIFICATION SERVICE ============
class NotificationService:
    """Smart notification service"""
    
    async def get_user_notifications(
        self, 
        user_id: str, 
        limit: int, 
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get user's smart notifications"""
        try:
            notifications = await get_user_notifications(user_id, limit, db)
            
            return [
                {
                    "id": notif.id,
                    "type": notif.notification_type,
                    "title": notif.title,
                    "message": notif.message,
                    "scheduled_time": notif.scheduled_time,
                    "sent": notif.sent,
                    "opened": notif.opened
                }
                for notif in notifications
            ]
        except Exception as e:
            print(f"Notification service error: {str(e)}")
            raise HTTPException(500, f"Failed to fetch notifications: {str(e)}")
    
    async def mark_notification_opened(
        self, 
        user_id: str, 
        notification_id: int, 
        db: AsyncSession
    ) -> bool:
        """Mark notification as opened"""
        try:
            return await mark_notification_opened(notification_id, user_id, db)
        except Exception as e:
            print(f"Notification update error: {str(e)}")
            raise HTTPException(500, f"Failed to update notification: {str(e)}")

# ============ STORY SERVICE ============
class StoryService:
    """Nutrition story service"""
    
    async def get_or_generate_nutrition_story(
        self, 
        user_id: str, 
        story_type: str, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get or generate nutrition story"""
        try:
            # Check if we have a recent story
            existing_story = await get_nutrition_story(user_id, story_type, db)
            
            if existing_story:
                return {
                    "title": existing_story.story_title,
                    "content": existing_story.story_content,
                    "insights": existing_story.key_insights,
                    "story_id": existing_story.id,
                    "created_at": existing_story.created_at
                }
            
            # Generate new story
            story = await generate_nutrition_story(user_id, story_type, db)
            if not story:
                raise HTTPException(404, "Not enough data to generate story")
            
            return story
        except HTTPException:
            raise
        except Exception as e:
            print(f"Story service error: {str(e)}")
            raise HTTPException(500, f"Failed to generate nutrition story: {str(e)}")

# ============ ACHIEVEMENT SERVICE ============
class AchievementService:
    """Achievement and gamification service"""
    
    async def get_user_achievements(
        self, 
        user_id: str, 
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get user's achievements"""
        try:
            achievements = await get_user_achievements(user_id, db)
            
            return [
                {
                    "achievement_name": ach.achievement_name,
                    "description": ach.description,
                    "points": ach.points,
                    "badge_icon": ach.badge_icon,
                    "earned_date": ach.earned_date,
                    "achievement_type": ach.achievement_type
                }
                for ach in achievements
            ]
        except Exception as e:
            print(f"Achievement service error: {str(e)}")
            raise HTTPException(500, f"Failed to fetch achievements: {str(e)}")

# ============ RECIPE SERVICE ============
class RecipeService:
    """AI recipe service"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    async def generate_custom_recipe(
        self, 
        request: AIRecipeRequest, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate custom AI recipe"""
        try:
            # Get user context
            profile = await get_user_profile(request.user_id, db)
            user_context = build_user_context(profile) if profile else {}
            
            return await self.ai_service.generate_recipe(
                request.target_macros,
                request.dietary_restrictions,
                user_context,
                request.user_id,
                db
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Recipe service error: {str(e)}")
            raise HTTPException(500, f"Failed to generate recipe: {str(e)}")
    
    async def get_user_recipes(
        self, 
        user_id: str, 
        limit: int, 
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get user's saved recipes"""
        try:
            recipes = await get_user_recipes(user_id, limit, db)
            
            return [
                {
                    "recipe_id": recipe.id,
                    "recipe_name": recipe.recipe_name,
                    "description": recipe.description,
                    "nutrition_info": recipe.nutrition_info,
                    "prep_time": recipe.prep_time,
                    "cook_time": recipe.cook_time,
                    "difficulty_level": recipe.difficulty_level,
                    "tags": recipe.tags,
                    "user_rating": recipe.user_rating,
                    "created_at": recipe.created_at
                }
                for recipe in recipes
            ]
        except Exception as e:
            print(f"Recipe fetch error: {str(e)}")
            raise HTTPException(500, f"Failed to fetch recipes: {str(e)}")
    
    async def rate_recipe(
        self, 
        user_id: str, 
        recipe_id: int, 
        rating: float, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Rate a recipe"""
        try:
            if not (1 <= rating <= 5):
                raise HTTPException(400, "Rating must be between 1 and 5")
            
            success = await rate_recipe(recipe_id, user_id, rating, db)
            if not success:
                raise HTTPException(404, "Recipe not found")
            
            return {"message": "Recipe rated successfully", "rating": rating}
        except HTTPException:
            raise
        except Exception as e:
            print(f"Recipe rating error: {str(e)}")
            raise HTTPException(500, f"Failed to rate recipe: {str(e)}")

# ============ SERVICE FACTORY ============
def create_services() -> Dict[str, Any]:
    """Create all service instances"""
    ai_service = AIService()
    nutrition_service = NutritionService(ai_service)
    user_service = UserService()
    image_service = ImageService()
    notification_service = NotificationService()
    story_service = StoryService()
    achievement_service = AchievementService()
    recipe_service = RecipeService(ai_service)
    
    return {
        "ai_service": ai_service,
        "nutrition_service": nutrition_service,
        "user_service": user_service,
        "image_service": image_service,
        "notification_service": notification_service,
        "story_service": story_service,
        "achievement_service": achievement_service,
        "recipe_service": recipe_service
    }
