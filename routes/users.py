from typing import Iterator
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from db import SessionLocal
from models import Profile
from schemas import ProfileIn, ProfileOut

router = APIRouter(prefix="/users", tags=["Користувачі"])

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Розрахунки 
def calc_bmr(sex: str, weight: float, height_cm: float, age: int) -> float:
    # Формула Міффліна-Сан Жеора
    if sex == "male":
        return 10 * weight + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height_cm - 5 * age - 161

def calc_tdee(bmr: float, activity: float) -> float:
    return bmr * activity

# ендпоїнти
@router.post(
    "",
    response_model=ProfileOut,
    response_model_by_alias=True,
    summary="Створити профіль та порахувати BMR/TDEE/target_kcal",
)
def upsert_profile(payload: ProfileIn, db: Session = Depends(get_db)):
    # 1. Розрахунок BMR та TDEE
    bmr = calc_bmr(payload.sex, payload.weight_kg, payload.height_cm, payload.age)
    tdee = calc_tdee(bmr, payload.activity_factor)

    # 2. Логіка цілі 
    goal_key = payload.goal or "maintain"

    if goal_key == "lose":
        target_raw = tdee * 0.8
    elif goal_key == "gain":
        target_raw = tdee * 1.15
    else:  
        target_raw = tdee

    # Не опускаємось нижче BMR
    target = max(bmr, target_raw)
    target_rounded = round(target)

    # 3. Створюємо запис профілю
    row = Profile(
        sex=payload.sex,
        age=payload.age,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        activity_factor=payload.activity_factor,
        budget_per_day=payload.budget_per_day,
        allergies=list(payload.allergies or []),
        goal=goal_key,
        bmr=float(bmr),
        tdee=float(tdee),
        target_kcal=float(target_rounded),
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("/{profile_id}", response_model=ProfileOut, response_model_by_alias=True, summary="Отримати профіль за ідентифікатором")
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    row = db.get(Profile, profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Профіль не знайдено")
    return row

@router.get("", response_model=list[ProfileOut], response_model_by_alias=True, summary="Список профілів")
def list_profiles(db: Session = Depends(get_db)):
    items = db.execute(select(Profile).order_by(Profile.id.desc())).scalars().all()
    return items
