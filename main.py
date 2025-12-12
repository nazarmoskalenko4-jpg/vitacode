from fastapi import FastAPI
from sqlalchemy import text

from db import engine, Base

# підключаємо модульні роутери
from routes.recipes import router as recipes_router
from routes.users import router as users_router
from routes.plans import router as plans_router
from routes.web_ui import router as web_ui_router

app = FastAPI(
    title="VitaCode API",
    description="Веб-платформа VitaCode: рецепти, профіль користувача, генерація денного/тижневого плану.",
    version="1.0.0",
)

@app.on_event("startup")
def on_startup() -> None:
    # створюємо таблиці (якщо їх ще немає)
    Base.metadata.create_all(bind=engine)

@app.get("/", tags=["Сервіс"])
def root():
    return {"message": "VitaCode API працює"}

@app.get("/health/db", tags=["Сервіс"])
def db_health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"db": "ok"}

# реєструємо роутери
app.include_router(recipes_router)
app.include_router(users_router)
app.include_router(plans_router)
app.include_router(web_ui_router)