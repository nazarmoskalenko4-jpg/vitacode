import json
import csv
import io
from typing import Iterator, List, Any, Optional

from fastapi import APIRouter, Depends, Form, Request, Query
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Profile
from schemas import DayPlanIn, WeekPlanIn
from routes.recipes import make_day_plan, make_week_plan
from routes.users import calc_bmr, calc_tdee

router = APIRouter(prefix="/ui", tags=["Web UI"])
templates = Jinja2Templates(directory="templates")


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/plan", response_class=HTMLResponse)
def show_plan_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("profile_form.html", {"request": request})


@router.post("/plan", response_class=HTMLResponse)
def create_plan_from_form(
    request: Request,
    sex: str = Form(...),
    age: int = Form(...),
    height_cm: float = Form(...),
    weight_kg: float = Form(...),
    activity_factor: float = Form(...),
    budget_per_day: float = Form(...),
    goal: str = Form(...),
    mode: str = Form("day"),
    allergies: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    # 1. Мапінг значень
    sex_map = {
        "male": "male", "female": "female",
        "чоловіча": "male", "чоловік": "male", "жіноча": "female"
    }
    goal_map = {
        "lose": "lose", "maintain": "maintain", "gain": "gain",
        "схуднення": "lose", "утримання": "maintain", "набір": "gain"
    }

    sex_key = sex_map.get(sex.strip().lower(), "male")
    goal_key = goal_map.get(goal.strip().lower(), "maintain")
    
    allergy_list = [a.strip().lower() for a in allergies.split(",") if a.strip()]

    # 2. Розрахунок
    bmr = calc_bmr(sex_key, weight_kg, height_cm, age)
    tdee = calc_tdee(bmr, activity_factor)

    if goal_key == "lose":
        target_raw = tdee * 0.8
        snacks_goal = 0
    elif goal_key == "gain":
        target_raw = tdee * 1.15
        snacks_goal = 2
    else:
        target_raw = tdee
        snacks_goal = 1

    target = max(bmr, target_raw)
    target_rounded = round(target)

    # 3. Збереження профілю
    profile = Profile(
        sex=sex_key, age=age, height_cm=height_cm, weight_kg=weight_kg,
        activity_factor=activity_factor, budget_per_day=budget_per_day,
        allergies=allergy_list, goal=goal_key,
        bmr=float(bmr), tdee=float(tdee), target_kcal=float(target_rounded),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # 4. Генерація плану
    plans_list = []
    stats = {}
    is_week = (mode == "week")

    if is_week:
        payload = WeekPlanIn(
            days=7,
            kcal=target_rounded,
            budget=budget_per_day,
            snacks=snacks_goal,
            diet_tags=["standard"],
            exclude_allergens=allergy_list
        )
        result = make_week_plan(payload, db)
        plans_list = result["плани"]
        
        stats["total_kcal"] = result["загалом ккал"]
        stats["total_price"] = result["загалом ціна грн"]
        stats["target_kcal_period"] = target_rounded * 7
        stats["budget_period"] = budget_per_day * 7
        stats["items_count"] = sum(len(d["елементи"]) for d in plans_list)
        
    else:
        payload = DayPlanIn(
            kcal=target_rounded,
            budget=budget_per_day,
            snacks=snacks_goal,
            diet_tags=["standard"],
            exclude_allergens=allergy_list
        )
        day_result = make_day_plan(payload, db)
        plans_list = [day_result]
        
        stats["total_kcal"] = day_result["підсумок"]["ккал"]
        stats["total_price"] = day_result["підсумок"]["ціна грн"]
        stats["target_kcal_period"] = target_rounded
        stats["budget_period"] = budget_per_day
        stats["items_count"] = len(day_result["елементи"])

    # Сортування та групування (x2)
    meal_order = {"breakfast": 1, "lunch": 2, "dinner": 3, "snack": 4}

    for day in plans_list:
        raw_items = day["елементи"]
        grouped_map = {}

        for item in raw_items:
            m_type = item.get("тип прийому")
            name = item.get("назва")
            key = (m_type, name)

            if key in grouped_map:
                existing = grouped_map[key]
                existing["count"] = existing.get("count", 1) + 1
                existing["ккал"] += item.get("ккал", 0)
                existing["білки г"] += item.get("білки г", 0)
                existing["жири г"] += item.get("жири г", 0)
                existing["вуглеводи г"] += item.get("вуглеводи г", 0)
                existing["ціна грн"] += item.get("ціна грн", 0)
                existing["вага г"] = existing.get("вага г", 0) + item.get("вага г", 0)
            else:
                new_item = item.copy()
                new_item["count"] = 1
                if "вага г" not in new_item: new_item["вага г"] = 0
                if "опис" not in new_item: new_item["опис"] = ""
                grouped_map[key] = new_item
        
        new_list = list(grouped_map.values())
        new_list.sort(key=lambda x: meal_order.get(x.get("тип прийому"), 99))
        day["елементи"] = new_list

    stats["items_count"] = sum(len(d["елементи"]) for d in plans_list)

    goal_label_map = {"lose": "Схуднення", "maintain": "Утримання ваги", "gain": "Набір"}
    goal_label = goal_label_map.get(goal_key, goal_key)
    
    plans_json = json.dumps(plans_list, default=str, ensure_ascii=False)

    return templates.TemplateResponse(
        "plan_result.html",
        {
            "request": request, "profile": profile, "plans_list": plans_list,
            "plans_json": plans_json, "stats": stats, "goal_label": goal_label, "is_week": is_week
        },
    )


# Маршрут CSV 
@router.post("/download")
def download_plan_file(
    plan_json: str = Form(...),
    is_week: bool = Form(...)
):
    """
    Генерує CSV, розбитий на блоки по днях (як на сайті).
    """
    try:
        plans_data = json.loads(plan_json)
    except json.JSONDecodeError:
        return Response(content="Помилка обробки даних", status_code=400)

    output = io.StringIO()
    # BOM для коректного відображення кирилиці в Excel
    output.write('\ufeff')
    
    writer = csv.writer(output)
    
    # Словник для перекладу типів страв
    type_map = {
        "breakfast": "Сніданок", "lunch": "Обід", 
        "dinner": "Вечеря", "snack": "Перекус"
    }

    # Заголовки колонок 
    col_headers = ["Тип", "Назва", "Склад", "Вага (г)", "Ккал", "Білки", "Жири", "Вугл", "Ціна (грн)"]

    total_price_all = 0
    total_kcal_all = 0

    for i, day_plan in enumerate(plans_data, start=1):
        # 1. Заголовок Дня 
        if is_week:
            writer.writerow([f"--- ДЕНЬ {i} ---"])
        else:
            writer.writerow(["--- ПЛАН ХАРЧУВАННЯ ---"])
        
        # 2. Шапка таблиці
        writer.writerow(col_headers)

        items = day_plan.get("елементи", [])
        day_summary = day_plan.get("підсумок", {})
        
        # Підрахунок БЖВ за день 
        sum_p = sum(item.get("білки г", 0) for item in items)
        sum_f = sum(item.get("жири г", 0) for item in items)
        sum_c = sum(item.get("вуглеводи г", 0) for item in items)

        # 3. Рядки зі стравами
        for item in items:
            m_type = type_map.get(item.get("тип прийому"), item.get("тип прийому"))
            
            # Назва + (x2)
            name = item.get("назва", "")
            count = item.get("count", 1)
            if count > 1:
                name += f" (x{count})"
            
            description = item.get("опис", "")
            weight = round(item.get("вага г", 0))
            kcal = round(item.get("ккал", 0), 1)
            p = round(item.get("білки г", 0), 1)
            f = round(item.get("жири г", 0), 1)
            c = round(item.get("вуглеводи г", 0), 1)
            price = round(item.get("ціна грн", 0), 2)

            writer.writerow([m_type, name, description, weight, kcal, p, f, c, price])

        # 4. Підсумок Дня 
        d_kcal = round(day_summary.get("ккал", 0), 1)
        d_price = round(day_summary.get("ціна грн", 0), 2)
        
        writer.writerow([
            "РАЗОМ ЗА ДЕНЬ", "", "", "", 
            d_kcal, 
            round(sum_p, 1), 
            round(sum_f, 1), 
            round(sum_c, 1), 
            d_price
        ])
        
        writer.writerow([])
        
        total_kcal_all += d_kcal
        total_price_all += d_price

    # 6. Загальний підсумок 
    writer.writerow([])
    writer.writerow(["ЗАГАЛОМ ЗА ВЕСЬ ПЕРІОД", "", "", "", round(total_kcal_all), "", "", "", round(total_price_all, 2)])
    writer.writerow(["VitaCode Generator", "", "", "", "", "", "", "", ""])

    filename = "plan_week.csv" if is_week else "plan_day.csv"
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/profiles", response_class=HTMLResponse)
def list_profiles(request: Request, db: Session = Depends(get_db)):
    profiles = db.query(Profile).order_by(Profile.id.desc()).all()
    return templates.TemplateResponse("profiles_list.html", {"request": request, "profiles": profiles})


@router.post("/profile/delete/{profile_id}")
def delete_profile(profile_id: int, origin: str = Query("list"), db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if profile:
        db.delete(profile)
        db.commit()
    return RedirectResponse(url="/ui/plan" if origin == "result" else "/ui/profiles", status_code=303)