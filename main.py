from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import json

from app.database import engine, get_db, Base
from app import models

# Создаем таблицы в базе данных (если их нет)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Destiny Game API")

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

@app.get("/")
def root():
    # Проверяем подключение к базе
    db_connected = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_connected = True
    except:
        db_connected = False
    
    return {
        "message": "Destiny API is working!",
        "status": "ok",
        "database": "connected" if db_connected else "disconnected",
        "version": "2.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/auth/telegram")
def auth_telegram(data: dict, db: Session = Depends(get_db)):
    """Авторизация через Telegram WebApp"""
    
    # Проверка отключена для теста
    # if not verify_telegram_data(data):
    #     raise HTTPException(status_code=401, detail="Invalid Telegram auth data")
    
    # Получаем данные пользователя
    user_data = {}
    if "user" in data:
        if isinstance(data["user"], str):
            try:
                user_data = json.loads(data["user"])
            except:
                user_data = {}
        else:
            user_data = data["user"]
    
    telegram_id = user_data.get("id")
    
    # Если нет ID, используем тестовый
    if not telegram_id:
        telegram_id = 999999999
    
    # Ищем пользователя в базе
    user = db.query(models.User).filter(
        models.User.telegram_id == telegram_id
    ).first()
    
    if not user:
        # Создаем нового пользователя
        user = models.User(
            telegram_id=telegram_id,
            first_name=user_data.get("first_name", "Test"),
            last_name=user_data.get("last_name", "Player")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Создаем персонажа для нового пользователя
        character = models.Character(
            user_id=user.id,
            name=f"Player_{telegram_id % 10000}"
        )
        db.add(character)
        db.commit()
        
        return {
            "status": "new_user",
            "user_id": user.id,
            "character": {
                "name": character.name,
                "level": character.level,
                "health": character.health,
                "max_health": character.max_health
            }
        }
    else:
        # Возвращаем данные существующего пользователя
        return {
            "status": "existing_user",
            "user_id": user.id,
            "character": {
                "name": user.character.name if user.character else None,
                "level": user.character.level if user.character else 1,
                "health": user.character.health if user.character else 100,
                "max_health": user.character.max_health if user.character else 100,
                "destiny_tokens": user.character.destiny_tokens if user.character else 0
            } if user.character else None
        }

@app.get("/user/{telegram_id}")
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Получить данные пользователя по Telegram ID"""
    
    user = db.query(models.User).filter(
        models.User.telegram_id == telegram_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "character": {
            "name": user.character.name if user.character else None,
            "level": user.character.level if user.character else 1,
            "experience": user.character.experience if user.character else 0,
            "health": user.character.health if user.character else 100,
            "max_health": user.character.max_health if user.character else 100,
            "destiny_tokens": user.character.destiny_tokens if user.character else 0,
            "gold": user.character.gold if user.character else 0
        } if user.character else None
    }

# ТЕСТОВЫЙ ЭНДПОИНТ: создать максимального персонажа
@app.post("/dev/max")
def create_max_character(db: Session = Depends(get_db)):
    """Создает тестового персонажа 30 уровня"""
    
    test_id = 999999999
    
    user = db.query(models.User).filter(
        models.User.telegram_id == test_id
    ).first()
    
    if not user:
        user = models.User(
            telegram_id=test_id,
            first_name="Max",
            last_name="Player"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    if not user.character:
        character = models.Character(
            user_id=user.id,
            name="MaxLevel",
            level=30,
            experience=30000,
            health=1000,
            max_health=1000,
            gold=10000,
            destiny_tokens=5000
        )
        db.add(character)
        db.commit()
        
        return {"status": "created", "telegram_id": test_id, "level": 30}
    else:
        # Обновляем существующего
        user.character.level = 30
        user.character.experience = 30000
        user.character.gold = 10000
        user.character.destiny_tokens = 5000
        db.commit()
        
        return {"status": "updated", "telegram_id": test_id, "level": 30}
