"""app/utils.py - Utility functions for AINUT"""
import json
import re
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

# ============ AI PERSONALITY CONFIGURATIONS ============
AI_PERSONALITIES = {
    "supportive": {
        "tone": "warm and encouraging",
        "style": "gentle guidance with positive reinforcement"
    },
    "motivational": {
        "tone": "energetic and inspiring", 
        "style": "challenging you to reach your goals"
    },
    "educational": {
        "tone": "informative and detailed",
        "style": "teaching you about nutrition science"
    },
    "fun": {
        "tone": "playful and engaging",
        "style": "making nutrition enjoyable with humor"
    }
}

def get_ai_personality_prompt(user_context: Dict, base_prompt: str) -> str:
    """Enhance prompts with AI personality"""
    personality_type = user_context.get("ai_personality_type", "supportive")
    personality = AI_PERSONALITIES.get(personality_type, AI_PERSONALITIES["supportive"])
    
    personality_instruction = f"""
IMPORTANT: Respond with a {personality['tone']} tone. 
Communication style: {personality['style']}
"""
    
    return f"{personality_instruction}\n\n{base_prompt}"

# ============ AI PROMPT TEMPLATES ============
def meal_analysis_prompt(user_input: str, corrections: Optional[str] = None) -> str:
    """Generate meal analysis prompt"""
    corrections_text = f"\nUser corrections: {corrections}" if corrections else ""
    return f"""
Analyze this meal and provide ACCURATE nutrition information. Be specific and precise.

Meal: {user_input}{corrections_text}

Analyze each food item carefully and provide realistic portions and nutrition values.

Return ONLY valid JSON:
{{
  "meal_name": "Clear, descriptive name for the meal",
  "meal_type": "breakfast/lunch/dinner/snack",
  "foods": [
    {{
      "name": "specific food item",
      "calories": 150,
      "protein_g": 12.5,
      "carbs_g": 18.0,
      "fat_g": 4.2
    }}
  ],
  "total_calories": 150
}}

CRITICAL REQUIREMENTS:
- meal_type MUST be one of: "breakfast", "lunch", "dinner", "snack" 
- NEVER leave meal_type empty or undefined
- If unsure about meal type, use "snack" as default
- Use realistic portion sizes
- Provide accurate nutrition values
- Be specific with food names
- Ensure total_calories matches the sum of individual food calories
"""

def generic_nutrition_prompt(food_log: List[Dict], daily_targets: Dict[str, float]) -> str:
    """Generate generic nutrition advice prompt"""
    food_summary = []
    total_macros = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    
    for item in food_log:
        food_summary.append(f"- {item.get('name', 'Unknown')}: {item.get('calories', 0)}cal")
        total_macros["calories"] += item.get("calories", 0)
        total_macros["protein_g"] += item.get("protein_g", 0)
        total_macros["carbs_g"] += item.get("carbs_g", 0)
        total_macros["fat_g"] += item.get("fat_g", 0)
    
    # Calculate what's needed
    calories_needed = max(0, daily_targets.get("calories", 2000) - total_macros["calories"])
    protein_needed = max(0, daily_targets.get("protein_g", 120) - total_macros["protein_g"])
    carbs_needed = max(0, daily_targets.get("carbs_g", 250) - total_macros["carbs_g"])
    fat_needed = max(0, daily_targets.get("fat_g", 70) - total_macros["fat_g"])
    
    return f"""
You MUST return EXACTLY this JSON format with specific meal ideas:

CURRENT STATUS:
- Eaten today: {food_summary}
- Current totals: {total_macros["calories"]} cal, {total_macros["protein_g"]}g protein, {total_macros["carbs_g"]}g carbs, {total_macros["fat_g"]}g fat
- Still need: {calories_needed} cal, {protein_needed}g protein, {carbs_needed}g carbs, {fat_needed}g fat

CRITICAL: You MUST give complete meal ideas with exact macro counts and percentages.

Return EXACTLY this structure (no variations allowed):
{{
  "overall_summary": "Clear advice like: You need {protein_needed}g more protein - let's get you some delicious high-protein meals!",
  "nutrients_to_focus_on": [
    {{
      "nutrient": "protein",
      "current_intake": {total_macros["protein_g"]},
      "target": {daily_targets.get("protein_g", 120)},
      "deficit": {protein_needed},
      "suggestions": [
        {{
          "meal_idea": "Greek Yogurt Power Bowl",
          "description": "1 cup Greek yogurt + 1/4 cup granola + 1 tbsp almond butter + berries",
          "total_calories": 340,
          "protein_provided": 25.0,
          "carbs_provided": 28.0,
          "fat_provided": 12.0,
          "percentage_coverage": {{"protein": 21, "carbs": 11, "fat": 17}},
          "meal_type": "snack",
          "easy_to_make": true,
          "why_perfect": "Quick protein boost that covers 21% of your daily protein needs in one delicious bowl"
        }},
        {{
          "meal_idea": "Chicken & Rice Power Bowl", 
          "description": "4oz grilled chicken breast + 1/2 cup brown rice + steamed broccoli + olive oil drizzle",
          "total_calories": 420,
          "protein_provided": 35.0,
          "carbs_provided": 40.0,
          "fat_provided": 8.0,
          "percentage_coverage": {{"protein": 29, "carbs": 16, "fat": 11}},
          "meal_type": "lunch",
          "easy_to_make": true,
          "why_perfect": "Balanced meal that delivers nearly 30% of your daily protein target"
        }}
      ],
      "why_important": "Protein helps build muscle and keeps you full between meals"
    }}
  ],
  "achievements": ["Great job starting your nutrition tracking today!"],
  "tips": [
    "Focus on getting protein with every meal and snack",
    "Try one of the meal suggestions above for your next meal"
  ]
}}

RULES:
1. NEVER use old format with "food", "serving_size", "amount_provided"
2. ALWAYS use "meal_idea", "description", "total_calories", "percentage_coverage"
3. Give 2 specific meal suggestions minimum
4. Calculate realistic percentages for daily coverage
5. Make suggestions encouraging and specific
"""

def personalized_nutrition_prompt(food_log: List[Dict], daily_targets: Dict[str, float], user_context: Dict[str, Any]) -> str:
    """Generate personalized nutrition advice prompt"""
    food_summary = []
    total_macros = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    
    for item in food_log:
        food_summary.append(f"- {item.get('name', 'Unknown')}: {item.get('calories', 0)}cal")
        total_macros["calories"] += item.get("calories", 0)
        total_macros["protein_g"] += item.get("protein_g", 0)
        total_macros["carbs_g"] += item.get("carbs_g", 0)
        total_macros["fat_g"] += item.get("fat_g", 0)
    
    # Calculate what's needed
    calories_needed = max(0, daily_targets.get("calories", 2000) - total_macros["calories"])
    protein_needed = max(0, daily_targets.get("protein_g", 120) - total_macros["protein_g"])
    carbs_needed = max(0, daily_targets.get("carbs_g", 250) - total_macros["carbs_g"])
    fat_needed = max(0, daily_targets.get("fat_g", 70) - total_macros["fat_g"])
    
    # User preferences
    likes = user_context.get("likes", [])
    dislikes = user_context.get("dislikes", [])
    cuisines = user_context.get("cuisines", [])
    allergies = user_context.get("allergies", [])
    activity = user_context.get("activity", "normal")
    
    preferences_text = ""
    if likes:
        preferences_text += f"User LOVES: {', '.join(likes[:3])}\n"
    if dislikes:
        preferences_text += f"User AVOIDS: {', '.join(dislikes[:3])}\n"
    if cuisines:
        preferences_text += f"Favorite cuisines: {', '.join(cuisines[:2])}\n"
    if allergies:
        preferences_text += f"ALLERGIC to: {', '.join(allergies)}\n"
    
    return f"""
You MUST return EXACTLY this JSON format with personalized meal ideas based on user preferences:

CURRENT STATUS:
- Eaten today: {food_summary}
- Current totals: {total_macros["calories"]} cal, {total_macros["protein_g"]}g protein, {total_macros["carbs_g"]}g carbs, {total_macros["fat_g"]}g fat
- Still need: {calories_needed} cal, {protein_needed}g protein, {carbs_needed}g carbs, {fat_needed}g fat
- Activity level: {activity}

USER PREFERENCES:
{preferences_text}

CRITICAL: You MUST give personalized meal ideas that match their preferences and avoid allergies/dislikes.

Return EXACTLY this structure (no variations allowed):
{{
  "overall_summary": "Personalized advice like: You need {protein_needed}g more protein - here are some {cuisines[0] if cuisines else 'delicious'} options you'll love!",
  "nutrients_to_focus_on": [
    {{
      "nutrient": "protein", 
      "current_intake": {total_macros["protein_g"]},
      "target": {daily_targets.get("protein_g", 120)},
      "deficit": {protein_needed},
      "suggestions": [
        {{
          "meal_idea": "Mediterranean Protein Bowl (matches your taste!)",
          "description": "Grilled chicken + chickpeas + feta cheese + olive oil + cucumber + cherry tomatoes",
          "total_calories": 380,
          "protein_provided": 32.0,
          "carbs_provided": 18.0,
          "fat_provided": 16.0,
          "percentage_coverage": {{"protein": 27, "carbs": 7, "fat": 23}},
          "meal_type": "lunch",
          "easy_to_make": true,
          "why_perfect": "Perfect for your Mediterranean preferences and delivers 27% of your daily protein in one delicious bowl"
        }},
        {{
          "meal_idea": "Greek Yogurt Parfait (your favorite!)",
          "description": "1 cup Greek yogurt + mixed berries + granola + honey drizzle + chopped nuts",
          "total_calories": 320,
          "protein_provided": 22.0,
          "carbs_provided": 35.0,
          "fat_provided": 8.0,
          "percentage_coverage": {{"protein": 18, "carbs": 14, "fat": 11}},
          "meal_type": "snack",
          "easy_to_make": true,
          "why_perfect": "Features foods you love and gives you 18% of your daily protein target"
        }}
      ],
      "why_important": "Based on your {activity} activity level, protein helps with muscle recovery and keeps you energized"
    }}
  ],
  "achievements": ["You're consistently choosing foods you enjoy - fantastic strategy!"],
  "tips": [
    "Focus on {cuisines[0] if cuisines else 'your favorite'} foods with added protein",
    "Your next meal should include {likes[0] if likes else 'something you enjoy'} - try the suggestions above!"
  ],
  "personalized_insights": [
    "You've eaten {len(set(item.get('name', '') for item in food_log))} different foods today - great variety!",
    "Your protein intake is {(total_macros['protein_g']/daily_targets.get('protein_g', 120)*100):.0f}% of your daily goal"
  ]
}}

RULES:
1. NEVER use old format with "food", "serving_size", "amount_provided"  
2. ALWAYS use "meal_idea", "description", "total_calories", "percentage_coverage"
3. Include user preferences in meal names and descriptions
4. Avoid any allergies/dislikes completely
5. Make it personal and encouraging
6. Give 2 specific meal suggestions minimum
"""

def food_search_prompt(query: str) -> str:
    """Generate food search prompt"""
    return f"""
Find 3-5 foods matching: "{query}"

Return ONLY valid JSON:
{{
  "results": [
    {{
      "name": "food name",
      "nutrition_per_100g": {{"calories": 0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}},
      "portion_suggestions": [{{"description": "1 medium", "grams": 100}}]
    }}
  ]
}}
"""

def substitute_prompt(food_name: str, restrictions: List[str], goals: str) -> str:
    """Generate food substitute prompt"""
    restrictions_text = f"Restrictions: {', '.join(restrictions)}" if restrictions else ""
    return f"""
Find 3-4 healthier alternatives for: "{food_name}"
Goal: {goals}
{restrictions_text}

Return ONLY valid JSON:
{{
  "original_food": "{food_name}",
  "substitutes": [
    {{
      "food": "substitute name",
      "reason": "why it's better",
      "nutrition_comparison": "specific comparison",
      "availability": "easy/moderate/specialty"
    }}
  ]
}}
"""

def recipe_generation_prompt(target_macros: Dict[str, float], dietary_restrictions: List[str], user_context: Dict[str, Any]) -> str:
    """Generate recipe creation prompt"""
    cuisine_text = f"Cuisine: {user_context.get('cuisines', ['Any'])[0]}" if user_context.get('cuisines') else "Cuisine: Any"
    restrictions_text = f"Dietary restrictions: {', '.join(dietary_restrictions)}" if dietary_restrictions else ""
    
    return f"""
Create a personalized recipe that matches these exact specifications:

Target Macros:
- Protein: {target_macros.get('protein', 0)}g
- Carbs: {target_macros.get('carbs', 0)}g  
- Fat: {target_macros.get('fat', 0)}g
- Calories: {target_macros.get('calories', 0)}

Requirements:
{cuisine_text}
{restrictions_text}

User Context:
- Likes: {', '.join(user_context.get('likes', [])[:3])}
- Dislikes: {', '.join(user_context.get('dislikes', [])[:3])}
- Allergies: {', '.join(user_context.get('allergies', []))}

Create a complete recipe that hits these macros within 5% accuracy.

Return ONLY valid JSON:
{{
  "recipe_name": "Delicious Recipe Name",
  "description": "Brief appetizing description",
  "ingredients": [
    {{"name": "chicken breast", "amount": "6 oz", "grams": 170}},
    {{"name": "brown rice", "amount": "1/2 cup dry", "grams": 95}}
  ],
  "instructions": [
    "Step 1: Detailed instruction",
    "Step 2: Next step"
  ],
  "nutrition_info": {{
    "calories": 420,
    "protein": 30.2,
    "carbs": 39.8,
    "fat": 15.1,
    "fiber": 4.2
  }},
  "prep_time": 15,
  "cook_time": 20,
  "tags": ["high-protein", "healthy", "quick"],
  "tips": ["Optional cooking tip", "Storage suggestion"]
}}
"""

def dinner_prediction_prompt(current_intake: Dict[str, float], daily_targets: Dict[str, float], user_context: Dict[str, Any]) -> str:
    """Generate dinner prediction prompt"""
    # Calculate remaining needs
    remaining_needs = {}
    for macro, target in daily_targets.items():
        current = current_intake.get(macro, 0)
        remaining_needs[macro] = max(0, target - current)
    
    return f"""
Predict the optimal dinner for this user based on their current intake:

Current Intake Today: {current_intake}
Daily Targets: {daily_targets}
Remaining Needs: {remaining_needs}

User Preferences:
- Likes: {', '.join(user_context.get('likes', []))}
- Cuisines: {', '.join(user_context.get('cuisines', []))}
- Allergies: {', '.join(user_context.get('allergies', []))}

Create 3 dinner suggestions that fill the remaining macro gaps.

Return ONLY valid JSON:
{{
  "reasoning": "Why these suggestions make sense for their remaining needs",
  "suggestions": [
    {{
      "meal_name": "Salmon with Sweet Potato",
      "description": "Grilled salmon with roasted sweet potato and steamed broccoli",
      "macros": {{"protein": 35, "carbs": 25, "fat": 18, "calories": 380}},
      "covers_needs": {{"protein": 85, "carbs": 60, "fat": 40}},
      "prep_time": 25,
      "why_perfect": "Fills your protein gap perfectly and adds healthy fats"
    }}
  ],
  "backup_options": [
    {{
      "meal_name": "Quick Protein Smoothie",
      "description": "Greek yogurt, banana, protein powder, almond butter",
      "prep_time": 5,
      "why_good": "Super quick if you're in a hurry"
    }}
  ]
}}
"""

def time_travel_prompt(current_pattern: Dict[str, Any], target_goal: Dict[str, Any], user_context: Dict[str, Any]) -> str:
    """Generate nutrition time travel prompt"""
    return f"""
Create a nutrition time travel analysis for this user:

Current Pattern (last 30 days):
{current_pattern}

Goal: {target_goal}

User Context:
- Activity Level: {user_context.get('activity', 'normal')}
- Preferences: {', '.join(user_context.get('likes', []))}
- Restrictions: {', '.join(user_context.get('allergies', []))}

Create a detailed time travel analysis.

Return ONLY valid JSON:
{{
  "projected_outcome": {{
    "30_day_weight_change": -2.5,
    "body_composition_change": "2 lbs muscle gain, 4.5 lbs fat loss",
    "energy_levels": "Significantly improved",
    "health_markers": "Improved cholesterol, stable blood sugar"
  }},
  "recommended_changes": [
    {{
      "change": "Increase protein to 120g daily",
      "reason": "Support muscle growth and satiety",
      "impact": "15% faster progress toward goal"
    }}
  ],
  "timeline": [
    {{
      "week": 1,
      "focus": "Establish protein baseline",
      "target_calories": 2000,
      "expected_result": "Increased energy, reduced cravings"
    }}
  ],
  "confidence_score": 0.78,
  "key_insights": [
    "Your current consistency is excellent - 87% tracking rate",
    "Increasing protein by 20g daily will accelerate fat loss by 30%"
  ]
}}
"""

# ============ RESPONSE PARSERS ============
def parse_json_response(response: str) -> Optional[Dict[str, Any]]:
    """Parse JSON response with common cleaning and validation"""
    try:
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        
        parsed = json.loads(response.strip())
        return fix_nan_values(parsed)
    except Exception as e:
        print(f"JSON parsing error: {str(e)}")
        return None

def fix_nan_values(obj):
    """Recursively fix NaN values in parsed JSON"""
    if isinstance(obj, dict):
        return {k: fix_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_nan_values(item) for item in obj]
    elif isinstance(obj, float) and (obj != obj):  # NaN check
        return 0.0
    elif obj in ["NaN", "nan"]:
        return 0.0
    return obj

def validate_meal_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate meal response has required fields"""
    if "meal_name" not in data:
        data["meal_name"] = "Unknown Meal"
    
    if "meal_type" not in data or data["meal_type"] not in ["breakfast", "lunch", "dinner", "snack"]:
        data["meal_type"] = "snack"
    
    if "foods" not in data:
        data["foods"] = []
    
    if "total_calories" not in data:
        data["total_calories"] = 0
    
    return data

def validate_nutrition_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate nutrition advice response"""
    if "overall_summary" not in data:
        data["overall_summary"] = "Let's focus on getting great nutrition today!"
    
    if "nutrients_to_focus_on" not in data:
        data["nutrients_to_focus_on"] = []
    
    if "achievements" not in data:
        data["achievements"] = ["Great job tracking your nutrition!"]
    
    if "tips" not in data:
        data["tips"] = ["Keep up the good work with consistent tracking"]
    
    # Ensure all suggestions use NEW FORMAT
    for nutrient in data.get("nutrients_to_focus_on", []):
        if "suggestions" in nutrient:
            for suggestion in nutrient["suggestions"]:
                ensure_new_suggestion_format(suggestion)
    
    return data

def ensure_new_suggestion_format(suggestion: Dict[str, Any]):
    """Ensure suggestion uses new format"""
    required_fields = {
        "meal_idea": "Nutritious Meal",
        "description": "Balanced meal with good nutrition",
        "total_calories": 300,
        "protein_provided": 15.0,
        "carbs_provided": 20.0,
        "fat_provided": 10.0,
        "percentage_coverage": {"protein": 13, "carbs": 8, "fat": 14},
        "meal_type": "snack",
        "easy_to_make": True,
        "why_perfect": "Great for your nutrition goals"
    }
    
    for field, default_value in required_fields.items():
        if field not in suggestion:
            suggestion[field] = default_value
    
    # Remove any old format fields that might still exist
    old_format_fields = ["food", "serving_size", "amount_provided", "easy_to_find"]
    for old_field in old_format_fields:
        if old_field in suggestion:
            del suggestion[old_field]
    
    # Validate numeric values
    for key in ["total_calories", "protein_provided", "carbs_provided", "fat_provided"]:
        try:
            suggestion[key] = float(suggestion[key])
            if suggestion[key] != suggestion[key]:  # NaN check
                suggestion[key] = required_fields[key]
        except (ValueError, TypeError):
            suggestion[key] = required_fields[key]

# ============ USER CONTEXT HELPERS ============
def build_user_context(profile) -> Dict[str, Any]:
    """Build user context from profile for AI personalization"""
    if not profile:
        return {}
    
    return {
        "likes": (profile.favorite_foods or [])[:5],
        "dislikes": (profile.disliked_foods or [])[:3],
        "cuisines": (profile.cuisine_preferences or [])[:3],
        "allergies": (profile.allergies or [])[:5],
        "activity": profile.activity_level or "normal",
        "goals": profile.nutrition_goals or {},
        "ai_personality_type": profile.ai_personality_type or "supportive",
        "preferred_communication_style": profile.preferred_communication_style or "encouraging",
        "coaching_frequency": profile.coaching_frequency or "daily"
    }

# ============ SIMPLE CACHING ============
# Simple in-memory cache for substitutes
substitute_cache = {}
substitute_cache_lock = asyncio.Lock()
MAX_CACHE_SIZE = 100

def get_cached_substitute(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached substitute result (thread-safe)"""
    async def _get():
        async with substitute_cache_lock:
            return substitute_cache.get(cache_key)
    import asyncio
    return asyncio.run(_get())

def cache_substitute(cache_key: str, result: Dict[str, Any]):
    """Cache substitute result (thread-safe)"""
    async def _cache():
        async with substitute_cache_lock:
            if len(substitute_cache) < MAX_CACHE_SIZE:
                substitute_cache[cache_key] = result
    import asyncio
    asyncio.run(_cache())

def clear_substitute_cache():
    """Clear substitute cache (thread-safe)"""
    async def _clear():
        async with substitute_cache_lock:
            global substitute_cache
            substitute_cache = {}
    import asyncio
    asyncio.run(_clear())

# ============ VALIDATION HELPERS ============
def validate_meal_type(meal_type: str) -> str:
    """Validate and fix meal type"""
    allowed_types = ["breakfast", "lunch", "dinner", "snack"]
    if meal_type and meal_type.lower() in allowed_types:
        return meal_type.lower()
    return "snack"  # Safe default

def validate_macros(macros: Dict[str, float]) -> Dict[str, float]:
    """Validate and fix macro values"""
    validated = {}
    for key, value in macros.items():
        try:
            validated[key] = max(0, float(value)) if value is not None else 0.0
        except (ValueError, TypeError):
            validated[key] = 0.0
    return validated

def validate_percentage_coverage(coverage: Dict[str, Any]) -> Dict[str, int]:
    """Validate percentage coverage values"""
    validated = {}
    for key, value in coverage.items():
        try:
            validated[key] = max(0, min(100, int(float(value))))
        except (ValueError, TypeError):
            validated[key] = 0
    return validated

# ============ ERROR HANDLING HELPERS ============
def create_fallback_meal_response() -> Dict[str, Any]:
    """Create fallback meal response for errors"""
    return {
        "meal_name": "Unknown Meal",
        "meal_type": "snack",
        "foods": [],
        "total_calories": 0,
        "analysis_method": "error_fallback"
    }

def create_fallback_nutrition_response() -> Dict[str, Any]:
    """Create fallback nutrition response for errors"""
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
                "why_perfect": "Perfect protein boost that covers 21% of your daily needs in one delicious bowl"
            }],
            "why_important": "Protein helps build muscle and keeps you satisfied longer"
        }],
        "achievements": ["You're building healthy tracking habits!"],
        "tips": ["Focus on adding protein to your next meal or snack"]
    }

# ============ UTILITY FUNCTIONS ============
def generate_cache_key(*args) -> str:
    """Generate cache key from arguments"""
    import hashlib
    key_string = ":".join(str(arg) for arg in args)
    return hashlib.md5(key_string.encode()).hexdigest()

def format_time(seconds: int) -> str:
    """Format seconds into human readable time"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        return f"{seconds // 60} minutes"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def clean_string(text: str) -> str:
    """Clean string for safe processing"""
    if not text:
        return ""
    return re.sub(r'[^\w\s-]', '', text).strip()

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def get_current_timestamp() -> float:
    """Get current timestamp"""
    return time.time()

def calculate_percentage(part: float, whole: float) -> int:
    """Calculate percentage with safe division"""
    if whole == 0:
        return 0
    return min(100, max(0, int((part / whole) * 100)))

# ============ AI RESPONSE QUALITY CHECKS ============
def is_valid_json_structure(data: Any, required_keys: List[str]) -> bool:
    """Check if data has required JSON structure"""
    if not isinstance(data, dict):
        return False
    
    for key in required_keys:
        if key not in data:
            return False
    
    return True

def has_valid_suggestions(nutrition_response: Dict[str, Any]) -> bool:
    """Check if nutrition response has valid suggestions"""
    nutrients = nutrition_response.get("nutrients_to_focus_on", [])
    if not nutrients:
        return False
    
    for nutrient in nutrients:
        suggestions = nutrient.get("suggestions", [])
        if not suggestions:
            continue
        
        for suggestion in suggestions:
            required_fields = ["meal_idea", "description", "total_calories", "protein_provided"]
            if not all(field in suggestion for field in required_fields):
                return False
    
    return True

def validate_recipe_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate recipe generation response"""
    required_fields = {
        "recipe_name": "Healthy Recipe",
        "description": "Nutritious and delicious meal",
        "ingredients": [],
        "instructions": [],
        "nutrition_info": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0},
        "prep_time": 30,
        "cook_time": 0,
        "tags": []
    }
    
    for field, default_value in required_fields.items():
        if field not in data:
            data[field] = default_value
    
    return data

def create_nutrition_advice_prompt(food_log: List[Dict], daily_targets: Dict[str, float], user_context: Optional[Dict] = None) -> str:
    """Create simplified, reliable nutrition advice prompt"""
    total_calories = sum(item.get("calories", 0) for item in food_log)
    total_protein = sum(item.get("protein_g", 0) for item in food_log)
    total_carbs = sum(item.get("carbs_g", 0) for item in food_log)
    total_fat = sum(item.get("fat_g", 0) for item in food_log)
    calories_needed = max(0, daily_targets.get("calories", 2000) - total_calories)
    protein_needed = max(0, daily_targets.get("protein_g", 120) - total_protein)
    carbs_needed = max(0, daily_targets.get("carbs_g", 250) - total_carbs)
    fat_needed = max(0, daily_targets.get("fat_g", 70) - total_fat)
    user_prefs = ""
    if user_context:
        likes = user_context.get("favorite_foods", [])
        dislikes = user_context.get("disliked_foods", [])
        allergies = user_context.get("allergies", [])
        if likes:
            user_prefs += f"User likes: {', '.join(likes[:3])}\n"
        if dislikes:
            user_prefs += f"User avoids: {', '.join(dislikes[:3])}\n"
        if allergies:
            user_prefs += f"ALLERGIES (avoid completely): {', '.join(allergies)}\n"
    return f"""
You are a nutrition coach. Analyze this user's daily intake and provide specific meal suggestions.

CURRENT INTAKE TODAY:
- Total calories: {total_calories}
- Protein: {total_protein}g
- Carbs: {total_carbs}g
- Fat: {total_fat}g

DAILY TARGETS:
- Calories: {daily_targets.get('calories', 2000)}
- Protein: {daily_targets.get('protein_g', 120)}g
- Carbs: {daily_targets.get('carbs_g', 250)}g
- Fat: {daily_targets.get('fat_g', 70)}g

REMAINING NEEDS:
- Calories: {calories_needed}
- Protein: {protein_needed}g
- Carbs: {carbs_needed}g
- Fat: {fat_needed}g

{user_prefs}

Give 2 specific meal suggestions that help meet their remaining needs.

RETURN EXACTLY THIS JSON FORMAT:
{{
  "overall_summary": "Brief encouraging summary about their progress and what they need",
  "nutrients_to_focus_on": [
    {{
      "nutrient": "protein",
      "current_intake": {total_protein},
      "target": {daily_targets.get('protein_g', 120)},
      "deficit": {protein_needed},
      "suggestions": [
        {{
          "meal_idea": "Greek Yogurt Bowl",
          "description": "1 cup Greek yogurt + granola + fresh berries + almonds",
          "total_calories": 320,
          "protein_provided": 20.0,
          "carbs_provided": 25.0,
          "fat_provided": 12.0,
          "percentage_coverage": {{"protein": 17, "carbs": 10, "fat": 17}},
          "meal_type": "snack",
          "easy_to_make": true,
          "why_perfect": "High protein snack that covers 17% of daily protein needs"
        }},
        {{
          "meal_idea": "Chicken Rice Bowl", 
          "description": "4oz grilled chicken + 1/2 cup brown rice + vegetables",
          "total_calories": 400,
          "protein_provided": 30.0,
          "carbs_provided": 35.0,
          "fat_provided": 8.0,
          "percentage_coverage": {{"protein": 25, "carbs": 14, "fat": 11}},
          "meal_type": "lunch",
          "easy_to_make": true,
          "why_perfect": "Balanced meal providing 25% of daily protein target"
        }}
      ],
      "why_important": "Protein helps build muscle and keeps you satisfied"
    }}
  ],
  "achievements": ["Great job tracking your nutrition today!"],
  "tips": ["Focus on protein with your next meal", "Try one of the suggested meals above"]
}}

CRITICAL RULES:
1. Use EXACT field names shown above
2. Give realistic calorie and macro amounts
3. Calculate percentages accurately
4. Make suggestions specific and actionable
5. Return ONLY valid JSON, no extra text
"""