from typing import List, Dict, Any, Optional
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict

# Recipe (видача з UA-ключами)
class RecipeOutUA(BaseModel):
    id: int = Field(serialization_alias="ід")
    name: str = Field(serialization_alias="назва")
    meal_type: str = Field(serialization_alias="тип прийому")
    kcal: float = Field(serialization_alias="ккал")
    protein_g: float = Field(serialization_alias="білки г")
    fat_g: float = Field(serialization_alias="жири г")
    carbs_g: float = Field(serialization_alias="вуглеводи г")
    price: float = Field(serialization_alias="ціна грн")
    weight_g: float = Field(default=0, serialization_alias="вага г")
    description: str = Field(default="", serialization_alias="опис")
    diet_tags: List[str] = Field(serialization_alias="дієт-теґи")
    allergens: List[str] = Field(serialization_alias="алергени")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

# План дня (вхід)
class DayPlanIn(BaseModel):
    kcal: int = Field(..., validation_alias="ккал")
    budget: float = Field(..., validation_alias="бюджет")
    snacks: int = Field(0, validation_alias="перекуси")
    diet_tags: List[str] = Field(default_factory=list, validation_alias="дієт_теґи")
    exclude_allergens: List[str] = Field(default_factory=list, validation_alias="виключити_алергени")
    model_config = ConfigDict(populate_by_name=True)

# План тижня (вхід)
class WeekPlanIn(DayPlanIn):
    days: int = Field(7, ge=1, le=14, validation_alias="днів")

# План дня (вихід) 
class DayPlanOut(BaseModel):
    summary: Dict[str, Any] = Field(serialization_alias="підсумок")
    items: List[RecipeOutUA] = Field(serialization_alias="елементи")
    model_config = ConfigDict(populate_by_name=True)

# План тижня (вихід) 
class WeekPlanOut(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# Профіль користувача (вхід)
class ProfileIn(BaseModel):
    sex: str = Field(..., validation_alias="стать")             
    age: int = Field(..., validation_alias="вік")
    height_cm: float = Field(..., validation_alias="зріст см")
    weight_kg: float = Field(..., validation_alias="вага кг")
    activity_factor: float = Field(..., validation_alias="активність коеф")  
    budget_per_day: float = Field(..., validation_alias="бюджет/день грн")

    # ціль по вазі / калоріях
    goal: Literal["lose", "maintain", "gain"] = Field(
        default="maintain",
        validation_alias="ціль",
    )

    allergies: List[str] = Field(default_factory=list, validation_alias="алергії")
    model_config = ConfigDict(populate_by_name=True)


# Профіль користувача (вихід)
class ProfileOut(BaseModel):
    id: int = Field(serialization_alias="ід")
    sex: str = Field(serialization_alias="стать")
    age: int = Field(serialization_alias="вік")
    height_cm: float = Field(serialization_alias="зріст см")
    weight_kg: float = Field(serialization_alias="вага кг")
    activity_factor: float = Field(serialization_alias="активність коеф")
    budget_per_day: float = Field(serialization_alias="бюджет/день грн")

    goal: Literal["lose", "maintain", "gain"] = Field(
        serialization_alias="ціль"
    )

    allergies: List[str] = Field(serialization_alias="алергії")
    bmr: float = Field(serialization_alias="BMR")
    tdee: float = Field(serialization_alias="TDEE")
    target_kcal: float = Field(serialization_alias="ціль ккал")
    model_config = ConfigDict(populate_by_name=True)


# Схеми для збережених планів (Plan / PlanMeal)

class PlanMealBase(BaseModel):
    day_index: int
    name: str
    meal_type: str
    kcal: float
    protein_g: float
    fat_g: float
    carbs_g: float
    price: float
    weight_g: float = 0
    description: str = ""

class PlanMealCreate(PlanMealBase):
    """Використовується у вхідній схемі PlanCreate."""
    pass

class PlanMealOut(PlanMealBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PlanBase(BaseModel):
    kind: Literal["day", "week"]
    user_id: Optional[int] = None

class PlanCreate(PlanBase):
    meals: List[PlanMealCreate]

class PlanOut(PlanBase):
    id: int
    total_kcal: float
    total_price: float
    model_config = ConfigDict(from_attributes=True)

class PlanWithMealsOut(PlanOut):
    meals: List[PlanMealOut]
    model_config = ConfigDict(from_attributes=True)