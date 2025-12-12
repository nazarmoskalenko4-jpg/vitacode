from typing import List, Optional, Dict, Any, Iterator, Set

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Recipe, Profile
from schemas import RecipeOutUA, DayPlanIn, WeekPlanIn, WeekPlanOut

router = APIRouter(tags=["Страви та плани"])


# Сервіс: сесія БД
def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# UA-словник
def recipe_to_ua_dict(r: Recipe) -> Dict[str, Any]:
    return {
        "ід": r.id,
        "назва": r.name,
        "тип прийому": r.meal_type,
        "ккал": float(r.kcal),
        "білки г": float(r.protein_g),
        "жири г": float(r.fat_g),
        "вуглеводи г": float(r.carbs_g),
        "ціна грн": float(r.price),
        "вага г": float(r.weight_g or 0),
        "опис": str(r.description or ""),
        "дієт-теґи": list(r.diet_tags or []),
        "алергени": list(r.allergens or []),
    }


# /recipes — список страв із фільтрами
@router.get(
    "/recipes",
    response_model=List[RecipeOutUA],
    response_model_by_alias=True,
    summary="Список страв",
)
def list_recipes(
    meal_type: Optional[str] = Query(None, description="breakfast/lunch/dinner/snack"),
    min_kcal: Optional[float] = Query(None),
    max_kcal: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    diet: Optional[List[str]] = Query(
        None, description="включити дієт-теґи (напр. vegetarian)"
    ),
    exclude_allergens: Optional[List[str]] = Query(
        None, description="алергени, яких уникати (напр. gluten)"
    ),
    db: Session = Depends(get_db),
):
    q = db.query(Recipe)

    if meal_type:
        q = q.filter(Recipe.meal_type == meal_type)

    if min_kcal is not None:
        q = q.filter(Recipe.kcal >= min_kcal)

    if max_kcal is not None:
        q = q.filter(Recipe.kcal <= max_kcal)

    if max_price is not None:
        q = q.filter(Recipe.price <= max_price)

    # усі вказані дієт-теґи мають бути присутні
    if diet:
        for tag in diet:
            q = q.filter(text("JSON_CONTAINS(diet_tags, :t)")).params(t=f'["{tag}"]')

    # жоден із вказаних алергенів не повинен зустрічатися
    if exclude_allergens:
        for al in exclude_allergens:
            q = q.filter(text("NOT JSON_CONTAINS(allergens, :a)")).params(
                a=f'["{al}"]'
            )

    items = q.order_by(Recipe.price.asc()).all()

    return [RecipeOutUA.model_validate(r) for r in items]


# Внутрішній генератор дня (Логіка алгоритму)
def _generate_day_plan_internal(
    payload: DayPlanIn,
    db: Session,
    used_ids: Optional[Set[int]] = None,
) -> Dict[str, Any]:
    """
    Розумна генерація:
    - Для малих цілей (<2000) -> суворі ліміти зверху, м'які знизу.
    - Для великих цілей (>2800) -> м'які ліміти зверху, суворі знизу (агресивний добір).
    """
    
    # Налаштування порогів 
    target = payload.kcal
    
    if target < 2000:
        # Режим "Схуднення"
        OVERFLOW_LIMIT = 1.03   # Максимум +3%
        FILLING_GOAL = 0.85     # Досить набрати 85%
    elif target > 2800:
        # Режим "Набір"
        OVERFLOW_LIMIT = 1.10   # Можна перебрати до 10%
        FILLING_GOAL = 0.97     # Але треба набрати хоча б 97%
    else:
        # Збалансований режим
        OVERFLOW_LIMIT = 1.05   # Максимум +5%
        FILLING_GOAL = 0.90     # Мінімально 90%
        

    # 1. Отримуємо пул страв
    q = db.query(Recipe)
    for tag in (payload.diet_tags or []):
        q = q.filter(text("JSON_CONTAINS(diet_tags, :t)")).params(t=f'["{tag}"]')
    for al in (payload.exclude_allergens or []):
        q = q.filter(text("NOT JSON_CONTAINS(allergens, :a)")).params(a=f'["{al}"]')

    pool: List[Recipe] = q.all()
    if not pool:
        raise HTTPException(status_code=404, detail="Не знайдено страв під задані умови")

    # 2. Розбиваємо по типах
    by_type: Dict[str, List[Recipe]] = {
        "breakfast": [], "lunch": [], "dinner": [], "snack": [],
    }
    for r in pool:
        if r.meal_type in by_type:
            by_type[r.meal_type].append(r)

    # 3. Визначаємо ціль на один прийом
    count_meals = 3 + max(0, payload.snacks)
    target_per_meal = target / max(1, count_meals)

    # Сортуємо: 1. чи використано, 2. відхилення ккал, 3. ціна
    for kind, lst in by_type.items():
        lst.sort(key=lambda r: (
            1 if (used_ids and r.id in used_ids) else 0,
            abs(r.kcal - target_per_meal),
            r.price
        ))

    selected: List[Recipe] = []

    # 4. Початковий вибір (Жадібний алгоритм)
    def pick_best(kind: str):
        if by_type[kind]:
            best = by_type[kind][0]
            # Спроба взяти невикористане
            if used_ids:
                for cand in by_type[kind]:
                    if cand.id not in used_ids:
                        best = cand
                        break
            selected.append(best)

    pick_best("breakfast")
    pick_best("lunch")
    pick_best("dinner")

    for _ in range(max(0, payload.snacks)):
        if not by_type["snack"]: break
        cand = None
        for r in by_type["snack"]:
            if r in selected: continue
            if used_ids and r.id in used_ids: continue
            cand = r
            break
        if not cand and by_type["snack"]: cand = by_type["snack"][0]
        if cand: selected.append(cand)

    def get_totals(items):
        return sum(r.kcal for r in items), sum(r.price for r in items)

    # 5. Корекція
    max_kcal_abs = target * OVERFLOW_LIMIT
    
    for _ in range(10):
        curr_kcal, curr_price = get_totals(selected)
        is_kcal_overflow = curr_kcal > max_kcal_abs
        is_budget_overflow = curr_price > payload.budget
        
        if not is_kcal_overflow and not is_budget_overflow:
            break

        # Яку страву видаляти/міняти
        candidates_to_remove = sorted(selected, key=lambda r: r.kcal if is_kcal_overflow else r.price, reverse=True)
        swapped = False
        
        for bad_item in candidates_to_remove:
            options = by_type.get(bad_item.meal_type, [])
            best_swap = None
            
            for opt in options:
                if opt in selected: continue
                
                diff_kcal = bad_item.kcal - opt.kcal
                diff_price = bad_item.price - opt.price
                
                improvement = False
                if is_kcal_overflow:
                    if diff_kcal > 20: improvement = True
                elif is_budget_overflow and not is_kcal_overflow:
                     if diff_price > 0: improvement = True
                
                if improvement:
                    best_swap = opt
                    break
            
            if best_swap:
                selected[selected.index(bad_item)] = best_swap
                swapped = True
                break
        
        if not swapped:
            snacks_in_plan = [s for s in selected if s.meal_type == 'snack']
            if snacks_in_plan and (is_kcal_overflow or is_budget_overflow):
                selected.remove(snacks_in_plan[0])
            else:
                break

    # 6. Добір - Додаємо страву, якщо мало ккал
    curr_kcal, curr_price = get_totals(selected)
    
    if curr_kcal < target * FILLING_GOAL:
        extra_candidates = sorted(pool, key=lambda r: (-r.kcal, r.price))
        
        for r in extra_candidates:
            curr_kcal, curr_price = get_totals(selected)
            if curr_kcal >= target * FILLING_GOAL: 
                break
                
            if curr_price + r.price > payload.budget: continue
            if curr_kcal + r.kcal > target * OVERFLOW_LIMIT: continue
            
            selected.append(r)

    if used_ids is not None:
        used_ids.update(r.id for r in selected)

    final_kcal, final_price = get_totals(selected)
    resp_items = [recipe_to_ua_dict(r) for r in selected]
    summary = {
        "ккал": round(final_kcal, 1),
        "ціна грн": round(final_price, 2),
        "позицій": len(selected),
    }
    return {"підсумок": summary, "елементи": resp_items}


# /plan/day — генерація денного плану
@router.post(
    "/plan/day",
    summary="Згенерувати денний план",
)
def make_day_plan(
    payload: DayPlanIn,
    db: Session = Depends(get_db),
):
    return _generate_day_plan_internal(payload=payload, db=db, used_ids=None)


# /plan/week — тижневий план з різноманіттям
@router.post(
    "/plan/week",
    response_model=WeekPlanOut,
    response_model_by_alias=True,
    summary="Згенерувати тижневий план",
)
def make_week_plan(
    payload: WeekPlanIn,
    db: Session = Depends(get_db),
):
    days = max(1, min(14, payload.days))
    used_ids: Set[int] = set()
    plans: List[Dict[str, Any]] = []
    total_kcal = 0.0
    total_price = 0.0

    for _ in range(days):
        day_plan = _generate_day_plan_internal(payload=payload, db=db, used_ids=used_ids)
        plans.append(day_plan)
        total_kcal += float(day_plan["підсумок"]["ккал"])
        total_price += float(day_plan["підсумок"]["ціна грн"])

    return {
        "днів": days,
        "плани": plans,
        "загалом ккал": round(total_kcal, 1),
        "загалом ціна грн": round(total_price, 2),
    }


@router.post(
    "/plan/day/by-user/{profile_id}",
    tags=["Плани"],
    summary="Згенерувати денний план за профілем",
)
def make_day_plan_by_user(profile_id: int, db: Session = Depends(get_db)):
    prof = db.get(Profile, profile_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Профіль не знайдено")

    payload = DayPlanIn(
        kcal=int(prof.target_kcal or prof.tdee or prof.bmr or 2000),
        budget=float(prof.budget_per_day or 200),
        snacks=0,
        diet_tags=[],
        exclude_allergens=list(prof.allergies or []),
    )
    return make_day_plan(payload, db)



@router.post("/debug/add-light-meals", tags=["Debug"], summary="Додати легкі страви без перезапуску")
def force_add_light_meals(db: Session = Depends(get_db)):
    # Список легких страв
    new_items = [
        Recipe(
            id=31, name="Легкий крем-суп з гарбуза", meal_type="lunch",
            kcal=320.0, protein_g=8.0, fat_g=12.0, carbs_g=45.0, price=50.0,
            weight_g=300.0, description="Гарбуз, вершки, цибуля, спеції",
            diet_tags=["standard", "vegetarian"], allergens=["milk"]
        ),
        Recipe(
            id=32, name="Куряче філе на пару з броколі", meal_type="lunch",
            kcal=350.0, protein_g=45.0, fat_g=5.0, carbs_g=10.0, price=75.0,
            weight_g=280.0, description="Філе курки 150г, броколі 130г",
            diet_tags=["standard"], allergens=[]
        ),
        Recipe(
            id=33, name="Овочевий салат з кіноа", meal_type="lunch",
            kcal=380.0, protein_g=12.0, fat_g=14.0, carbs_g=48.0, price=65.0,
            weight_g=250.0, description="Кіноа, томати, огірок, зелень, олія",
            diet_tags=["standard", "vegetarian", "vegan"], allergens=[]
        ),
        Recipe(
            id=34, name="Салат з тунцем (без майонезу)", meal_type="dinner",
            kcal=310.0, protein_g=28.0, fat_g=10.0, carbs_g=15.0, price=80.0,
            weight_g=240.0, description="Тунець консервований, листя салату, яйце, огірок",
            diet_tags=["standard"], allergens=["fish", "eggs"]
        ),
        Recipe(
            id=35, name="Сир кисломолочний з зеленню", meal_type="dinner",
            kcal=250.0, protein_g=36.0, fat_g=5.0, carbs_g=8.0, price=45.0,
            weight_g=200.0, description="Сир 5%, сметана, кріп, сіль",
            diet_tags=["standard", "vegetarian"], allergens=["milk"]
        ),
    ]

    added_count = 0
    for item in new_items:
        # Перевіряємо, чи є вже така страва
        existing = db.get(Recipe, item.id)
        if not existing:
            db.add(item)
            added_count += 1
        else:
            # Оновлюємо існуючу
            existing.name = item.name
            existing.kcal = item.kcal
            existing.price = item.price
            existing.weight_g = item.weight_g
            existing.description = item.description
            
    db.commit()
    return {"status": "ok", "added": added_count, "message": "Легкі страви перевірено/додано!"}