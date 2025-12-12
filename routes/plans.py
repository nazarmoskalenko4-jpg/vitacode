from typing import Iterator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Plan, PlanMeal
from schemas import PlanCreate, PlanOut, PlanWithMealsOut, PlanMealOut

router = APIRouter(prefix="/plans", tags=["Плани"])

# Сервіс: сесія БД
def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# POST /plans — створити план (day/week) та його елементи
@router.post(
    "",
    response_model=PlanOut,
    summary="Створити план (день/тиждень) та зберегти його у БД",
)
def create_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
):
    if not payload.meals:
        raise HTTPException(status_code=400, detail="Список прийомів їжі (meals) порожній")

    # Рахуємо підсумки
    total_kcal = sum(m.kcal for m in payload.meals)
    total_price = sum(m.price for m in payload.meals)

    plan = Plan(
        kind=payload.kind,
        user_id=payload.user_id,
        total_kcal=total_kcal,
        total_price=total_price,
    )
    db.add(plan)
    db.flush()  # щоб отримати plan.id до коміту

    for m in payload.meals:
        row = PlanMeal(
            plan_id=plan.id,
            day_index=m.day_index,
            name=m.name,
            meal_type=m.meal_type,
            kcal=m.kcal,
            protein_g=m.protein_g,
            fat_g=m.fat_g,
            carbs_g=m.carbs_g,
            price=m.price,
        )
        db.add(row)

    db.commit()
    db.refresh(plan)
    return plan

# GET /plans/{plan_id} — один план з переліком прийомів їжі
@router.get(
    "/{plan_id}",
    response_model=PlanWithMealsOut,
    summary="Отримати план за ідентифікатором (з елементами)",
)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="План не знайдено")
    return plan

# GET /plans — список планів (опційно за user_id)
@router.get(
    "",
    response_model=List[PlanOut],
    summary="Список планів (опційно відфільтрованих за user_id)",
)
def list_plans(
    user_id: Optional[int] = Query(None, description="Ідентифікатор користувача (profile_id)"),
    db: Session = Depends(get_db),
):
    q = db.query(Plan)
    if user_id is not None:
        q = q.filter(Plan.user_id == user_id)
    items = q.order_by(Plan.id.desc()).all()
    return items
