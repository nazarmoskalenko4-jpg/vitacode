# VitaCode API

**VitaCode** — це бекенд-платформа для планування харчування на основі FastAPI + MySQL.

Функціонал:
- зберігання **рецептів** (калорійність, БЖВ, ціна, дієт-теги, алергени);
- створення **профілю користувача** з розрахунком BMR/TDEE та цільових калорій;
- генерація **денного** та **тижневого** плану харчування в межах бюджету;
- збереження згенерованих планів у базу (`plans` + `plan_meals`);
- фільтри за дієт-тегами та алергенами, підтримка українських ключів у відповідях.

---

## Технологічний стек

- **Python** 3.13
- **FastAPI**
- **Uvicorn**
- **SQLAlchemy 2.x (ORM)**
- **Pydantic v2**
- **MySQL 8.x** + драйвер **pymysql**
- JSON-поля в MySQL (`diet_tags`, `allergens`) + `JSON_CONTAINS` у фільтрах

---

## Структура проєкту

```text
vitacode/
├─ main.py            # точка входу FastAPI
├─ db.py              # engine, SessionLocal, Base
├─ models.py          # ORM-моделі: Recipe, Profile, Plan, PlanMeal
├─ schemas.py         # Pydantic-схеми (UA-аліаси для відповідей)
├─ routes/
│  ├─ __init__.py
│  ├─ recipes.py      # /recipes, /plan/day, /plan/week, /plan/*/by-user
│  ├─ users.py        # /users (профілі, BMR/TDEE)
│  └─ plans.py        # /plans (збереження/читання планів)
├─ seed_data.py       # наповнення таблиці recipes
├─ requirements.txt   # залежності Python
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example       # приклад налаштувань середовища
└─ README.md
