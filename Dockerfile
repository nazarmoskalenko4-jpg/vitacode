FROM python:3.13-slim

# Системні залежності для pymysql/SQLAlchemy (мінімум)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Встановлюємо залежності
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копіюємо код
COPY . /app

# Експонуємо порт
EXPOSE 8000

# Команда за замовчуванням (uvicorn)
CMD ["bash", "-lc", "python seed_data.py && uvicorn main:app --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000} ${APP_RELOAD:+--reload}"]
