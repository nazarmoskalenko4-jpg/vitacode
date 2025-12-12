from typing import List, Dict, Any
from sqlalchemy.orm import Session

from db import Base, engine, SessionLocal
from models import Recipe


def ensure_schema() -> None:
    """Створюємо таблиці, якщо ще нема."""
    Base.metadata.create_all(bind=engine)


def recipes_payload() -> List[Dict[str, Any]]:
    """Набір демонстраційних страв (UA) з детальним грамуванням."""
    return [
        # ---------- Сніданки ----------
        {
            "id": 1, "name": "Омлет з овочами", "meal_type": "breakfast",
            "kcal": 420.0, "protein_g": 25.0, "fat_g": 28.0, "carbs_g": 14.0, "price": 60.0,
            "weight_g": 250.0, 
            "description": "Яйця курячі 3 шт (150г), Овочевий мікс (перець, томати, цибуля) 100г, Олія 5г",
            "diet_tags": ["standard"], "allergens": ["eggs", "milk"],
        },
        {
            "id": 2, "name": "Вівсянка з бананом", "meal_type": "breakfast",
            "kcal": 380.0, "protein_g": 11.0, "fat_g": 8.0, "carbs_g": 66.0, "price": 35.0,
            "weight_g": 300.0, 
            "description": "Вівсяна каша на воді/молоці 200г, Банан свіжий 100г, Мед 5г",
            "diet_tags": ["standard", "vegetarian"], "allergens": ["gluten"],
        },
        {
            "id": 3, "name": "Сирники з ягодами", "meal_type": "breakfast",
            "kcal": 450.0, "protein_g": 22.0, "fat_g": 20.0, "carbs_g": 45.0, "price": 55.0,
            "weight_g": 220.0, 
            "description": "Сирники (сир 5%, борошно, яйце) 170г, Ягідний соус (вишня/смородина) 50г",
            "diet_tags": ["standard", "vegetarian"], "allergens": ["milk", "eggs", "gluten"],
        },
        {
            "id": 4, "name": "Тости з авокадо та яйцем", "meal_type": "breakfast",
            "kcal": 430.0, "protein_g": 17.0, "fat_g": 24.0, "carbs_g": 38.0, "price": 65.0,
            "weight_g": 200.0, 
            "description": "Хліб цільнозерновий 2 шм (60г), Авокадо стигле 80г, Яйце пашот 1 шт (50г), Кунжут",
            "diet_tags": ["standard", "vegetarian"], "allergens": ["eggs", "gluten"],
        },
        {
            "id": 5, "name": "Йогурт з мюслі та фруктами", "meal_type": "breakfast",
            "kcal": 360.0, "protein_g": 14.0, "fat_g": 9.0, "carbs_g": 55.0, "price": 40.0,
            "weight_g": 300.0, 
            "description": "Йогурт натуральний 2.5% 200г, Гранола медова 50г, Яблуко/Груша 50г",
            "diet_tags": ["standard", "vegetarian"], "allergens": ["milk", "gluten"],
        },

        # ---------- Обіди ----------
        {
            "id": 8, "name": "Курка з рисом та овочами", "meal_type": "lunch",
            "kcal": 650.0, "protein_g": 42.0, "fat_g": 18.0, "carbs_g": 78.0, "price": 85.0,
            "weight_g": 400.0, 
            "description": "Рис басматі відварний 200г, Філе куряче запечене 120г, Овочева суміш (горошок, кукурудза) 80г",
            "diet_tags": ["standard"], "allergens": [],
        },
        {
            "id": 9, "name": "Гречка з індичкою", "meal_type": "lunch",
            "kcal": 600.0, "protein_g": 40.0, "fat_g": 16.0, "carbs_g": 74.0, "price": 80.0,
            "weight_g": 380.0, 
            "description": "Гречка відварна 200г, Філе індички тушковане 120г, Підлива овочева 60г",
            "diet_tags": ["standard"], "allergens": [],
        },
        {
            "id": 10, "name": "Відбивна зі свинини з пюре", "meal_type": "lunch",
            "kcal": 750.0, "protein_g": 36.0, "fat_g": 40.0, "carbs_g": 55.0, "price": 95.0,
            "weight_g": 420.0, 
            "description": "Картопляне пюре з маслом та молоком 270г, Відбивна свиняча смажена 150г",
            "diet_tags": ["standard"], "allergens": ["milk", "gluten"],
        },
        {
            "id": 11, "name": "Паста з куркою та грибами", "meal_type": "lunch",
            "kcal": 700.0, "protein_g": 34.0, "fat_g": 24.0, "carbs_g": 90.0, "price": 90.0,
            "weight_g": 350.0, 
            "description": "Спагетті відварні 180г, Курка філе 100г, Печериці смажені 40г, Вершковий соус 30г",
            "diet_tags": ["standard"], "allergens": ["gluten", "milk"],
        },
        # --- Легкі обіди ---
        {
            "id": 31, "name": "Легкий крем-суп з гарбуза", "meal_type": "lunch",
            "kcal": 320.0, "protein_g": 8.0, "fat_g": 12.0, "carbs_g": 45.0, "price": 50.0,
            "weight_g": 300.0, 
            "description": "Суп (гарбуз, морква, картопля) 280г, Вершки 10% 20г, Гарбузове насіння",
            "diet_tags": ["standard", "vegetarian"], "allergens": ["milk"],
        },
        {
            "id": 32, "name": "Куряче філе на пару з броколі", "meal_type": "lunch",
            "kcal": 350.0, "protein_g": 45.0, "fat_g": 5.0, "carbs_g": 10.0, "price": 75.0,
            "weight_g": 280.0, 
            "description": "Філе куряче (су-від або пар) 150г, Броколі відварне 130г, Лимонний сік",
            "diet_tags": ["standard"], "allergens": [],
        },
        {
            "id": 33, "name": "Овочевий салат з кіноа", "meal_type": "lunch",
            "kcal": 380.0, "protein_g": 12.0, "fat_g": 14.0, "carbs_g": 48.0, "price": 65.0,
            "weight_g": 250.0, 
            "description": "Кіноа відварна 100г, Томати чері 50г, Огірок 50г, Рукола, Оливкова олія 10г",
            "diet_tags": ["standard", "vegetarian", "vegan"], "allergens": [],
        },

        # ---------- Вечері ----------
        {
            "id": 16, "name": "Запечена риба з овочами", "meal_type": "dinner",
            "kcal": 520.0, "protein_g": 35.0, "fat_g": 20.0, "carbs_g": 40.0, "price": 95.0,
            "weight_g": 320.0, 
            "description": "Хек/Минтай запечений 160г, Овочевий гарнір (кабачок, морква, перець) 160г",
            "diet_tags": ["standard"], "allergens": ["fish"],
        },
        {
            "id": 17, "name": "Салат Цезар з куркою", "meal_type": "dinner",
            "kcal": 480.0, "protein_g": 32.0, "fat_g": 26.0, "carbs_g": 24.0, "price": 85.0,
            "weight_g": 280.0, 
            "description": "Салат Айсберг 100г, Курка гриль 100г, Томати чері 30г, Соус Цезар 30г, Пармезан 10г, Сухарики 10г",
            "diet_tags": ["standard"], "allergens": ["milk", "eggs", "gluten"],
        },
        {
            "id": 22, "name": "Паста болоньєзе", "meal_type": "dinner",
            "kcal": 720.0, "protein_g": 32.0, "fat_g": 28.0, "carbs_g": 95.0, "price": 90.0,
            "weight_g": 350.0, 
            "description": "Спагетті твердих сортів 200г, Соус Болоньєзе (фарш ялов., томати) 130г, Пармезан 20г",
            "diet_tags": ["standard"], "allergens": ["gluten", "milk"],
        },
        # --- Легкі вечері ---
        {
            "id": 34, "name": "Салат з тунцем (без майонезу)", "meal_type": "dinner",
            "kcal": 310.0, "protein_g": 28.0, "fat_g": 10.0, "carbs_g": 15.0, "price": 80.0,
            "weight_g": 240.0, 
            "description": "Тунець у вл. соку 80г, Яйце варене 1 шт (50г), Листя салату 50г, Огірок 50г, Олія 5г",
            "diet_tags": ["standard"], "allergens": ["fish", "eggs"],
        },
        {
            "id": 35, "name": "Сир кисломолочний з зеленню", "meal_type": "dinner",
            "kcal": 250.0, "protein_g": 36.0, "fat_g": 5.0, "carbs_g": 8.0, "price": 45.0,
            "weight_g": 200.0, 
            "description": "Сир кисломолочний 5% 180г, Зелень (кріп/петрушка) 10г, Сметана 10% 10г",
            "diet_tags": ["standard", "vegetarian"], "allergens": ["milk"],
        },

        # ---------- Перекуси ----------
        {
            "id": 23, "name": "Грецький йогурт з горіхами", "meal_type": "snack",
            "kcal": 250.0, "protein_g": 16.0, "fat_g": 12.0, "carbs_g": 16.0, "price": 35.0,
            "weight_g": 150.0, 
            "description": "Йогурт грецький 10% 135г, Волоський горіх 15г",
            "diet_tags": ["standard"], "allergens": ["milk", "nuts"],
        },
        {
            "id": 28, "name": "Банан", "meal_type": "snack",
            "kcal": 120.0, "protein_g": 1.5, "fat_g": 0.5, "carbs_g": 27.0, "price": 15.0,
            "weight_g": 120.0, 
            "description": "Банан середній стиглий 1 шт (120г)",
            "diet_tags": ["standard", "vegetarian", "vegan"], "allergens": [],
        },
        {
            "id": 29, "name": "Морква з хумусом", "meal_type": "snack",
            "kcal": 170.0, "protein_g": 6.0, "fat_g": 9.0, "carbs_g": 18.0, "price": 25.0,
            "weight_g": 150.0, 
            "description": "Морква свіжа нарізана 100г, Хумус класичний 50г",
            "diet_tags": ["standard", "vegetarian", "vegan"], "allergens": [],
        },
    ]


def upsert_recipes(db: Session, items: List[Dict[str, Any]]) -> None:
    """Ідемпотентна вставка: якщо id існує — оновлюємо, інакше додаємо."""
    for it in items:
        row = db.get(Recipe, it["id"])
        if row is None:
            row = Recipe(**it)
            db.add(row)
        else:
            for k, v in it.items():
                setattr(row, k, v)
    db.commit()


def main() -> None:
    ensure_schema()
    with SessionLocal() as db:
        upsert_recipes(db, recipes_payload())
    print("✅ Seed OK: demo-страви записані/оновлені.")


if __name__ == "__main__":
    main()