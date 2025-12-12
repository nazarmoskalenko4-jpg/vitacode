from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

# Таблиця: Користувачі
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    
    # Основні дані
    sex = Column(String(10), nullable=False)        
    age = Column(Integer, nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    activity_factor = Column(Float, nullable=False) 
    
    # Налаштування
    budget_per_day = Column(Float, default=0.0)
    goal = Column(String(50), default="maintain")   
    allergies = Column(JSON, default=list)      

    # Розраховані показники (кеш)
    bmr = Column(Float, default=0.0)
    tdee = Column(Float, default=0.0)
    target_kcal = Column(Float, default=0.0)



# Таблиця: Рецепти 
class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    meal_type = Column(String(50), index=True)  
    kcal = Column(Float, nullable=False)
    protein_g = Column(Float, default=0.0)
    fat_g = Column(Float, default=0.0)
    carbs_g = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    weight_g = Column(Float, default=0.0)        
    description = Column(String(500), default="") 
    diet_tags = Column(JSON, default=list)      
    allergens = Column(JSON, default=list)     


# Таблиця: Збережені плани (Plans)
class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(20), default="day") 
    user_id = Column(Integer, nullable=True) 
    total_kcal = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    meals = relationship("PlanMeal", back_populates="plan", cascade="all, delete-orphan")


class PlanMeal(Base):
    __tablename__ = "plan_meals"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    day_index = Column(Integer, default=1)  
    name = Column(String(150))
    meal_type = Column(String(50))
    kcal = Column(Float)
    protein_g = Column(Float)
    fat_g = Column(Float)
    carbs_g = Column(Float)
    price = Column(Float)
    weight_g = Column(Float, default=0.0)
    description = Column(String(500), default="")

    plan = relationship("Plan", back_populates="meals")