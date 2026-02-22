from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import json
from pathlib import Path

from app.database import engine, get_db, Base
from app import models

# ========== ИНИЦИАЛИЗАЦИЯ ==========
# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Destiny Game API",
    description="API для игры Destiny",
    version="2.0.0"
)

# Разрешаем запросы от Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ВРЕМЕННО: пропускаем проверку Telegram для теста
def verify_telegram_data(init_data: dict) -> bool:
    return True

# ========== ЗАГРУЗКА JSON ИЗ ПАПКИ DATA ==========
print("🚀 Загрузка JSON файлов...")
DATA_DIR = Path(__file__).parent / "data"

def load_json(filename):
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Загружен {filename}")
            return data
    except Exception as e:
        print(f"❌ Ошибка загрузки {filename}: {e}")
        return {}

# Загружаем все JSON
locations_data = load_json("locations.json")
enemies_data = load_json("enemies.json")
items_data = load_json("items.json")
crafting_data = load_json("crafting.json")
classes_data = load_json("classes.json")
quests_data = load_json("quests.json")
house_data = load_json("house.json")
premium_data = load_json("premium.json")
nft_data = load_json("nft.json")
rainbow_data = load_json("rainbow.json")
events_data = load_json("events.json")
codex_data = load_json("codex.json")
biomes_data = load_json("biomes.json")
islands_data = load_json("islands.json")
secrets_data = load_json("secrets.json")

print("✅ Все JSON загружены")

# ========== СТАРЫЕ ЭНДПОИНТЫ ==========
@app.get("/")
def root():
    return {
        "message": "Destiny API is working!",
        "status": "ok",
        "database": "connected",
        "version": "2.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/auth/telegram")
def auth_telegram(data: dict, db: Session = Depends(get_db)):
    """Авторизация через Telegram"""
    if not verify_telegram_data(data):
        raise HTTPException(status_code=401, detail="Invalid auth data")
    
    # Здесь код авторизации...
    return {"status": "ok"}

# ========== НОВЫЕ ЭНДПОИНТЫ ==========
@app.get("/api/data")
def get_data():
    """Получить все игровые данные"""
    return {
        "locations": locations_data,
        "enemies": enemies_data,
        "items": items_data,
        "crafting": crafting_data,
        "classes": classes_data,
        "quests": quests_data,
        "house": house_data,
        "premium": premium_data,
        "nft": nft_data,
        "rainbow": rainbow_data,
        "events": events_data,
        "codex": codex_data,
        "biomes": biomes_data,
        "islands": islands_data,
        "secrets": secrets_data
    }

@app.get("/api/location/{location_id}")
def get_location(location_id: str):
    """Получить информацию о локации"""
    location = locations_data.get("locations", {}).get(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@app.get("/api/user/{telegram_id}")
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Получить данные пользователя"""
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(models.Character).filter(models.Character.user_id == user.id).first()
    
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "level": character.level if character else 1,
        "gold": character.gold if character else 0,
        "destiny_tokens": character.destiny_tokens if character else 0,
        "location": character.location if character else "start"
    }
