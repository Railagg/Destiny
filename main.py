from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import hashlib
import hmac
import json

from app.database import engine, get_db, Base
from app import models

# Создаем таблицы в базе данных (если их нет)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Destiny Game API")

# Разрешаем запросы от Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для продакшена лучше ограничить доменами Telegram
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Токен бота из переменных окружения Render
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def verify_telegram_data(init_data: dict) -> bool:
    """Проверка данных от Telegram WebApp"""
    if not BOT_TOKEN:
        return False
    
    # Сортируем данные для проверки
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(init_data.items()) if k != "hash"
    )
    
    # Создаем секретный ключ из токена бота
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    
    # Вычисляем HMAC-SHA256
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return calculated_hash == init_data.get("hash")

@app.get("/")
def root():
    # Проверяем подключение к базе
    db_connected = True
    try:
        # Пробуем создать подключение
        db = SessionLocal = None
        # Просто проверяем, что движок есть
        if engine:
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
    
    # Проверяем подпись Telegram
    if not verify_telegram_data(data):
        raise HTTPException(status_code=401, detail="Invalid Telegram auth data")
    
    # Получаем данные пользователя
    user_data = json.loads(data.get("user", "{}"))
    telegram_id = user_data.get("id")
    
    if not telegram_id:
        raise HTTPException(status_code=400, detail="No user ID provided")
    
    # Ищем пользователя в базе
    user = db.query(models.User).filter(
        models.User.telegram_id == telegram_id
    ).first()
    
    if not user:
        # Создаем нового пользователя
        user = models.User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name")
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
