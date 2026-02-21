from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import hashlib
import hmac
import json

from app.database import engine, get_db, Base
from app import models

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Destiny Game API")

# Разрешаем запросы от Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для теста, потом ограничим https://t.me
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
    
    # Сортируем данные
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(init_data.items()) if k != "hash"
    )
    
    # Создаем секретный ключ
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    
    # Вычисляем хеш
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return calculated_hash == init_data.get("hash")

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
    
    # Проверяем подпись Telegram
    if not verify_telegram_data(data):
        raise HTTPException(status_code=401, detail="Invalid auth data")
    
    # Получаем данные пользователя
    user_data = json.loads(data.get("user", "{}"))
    telegram_id = user_data.get("id")
    
    if not telegram_id:
        raise HTTPException(status_code=400, detail="No user id")
    
    # Ищем или создаем пользователя
    user = db.query(models.User).filter(
        models.User.telegram_id == telegram_id
    ).first()
    
    if not user:
        # Новый пользователь
        user = models.User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Создаем персонажа
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
        # Существующий пользователь
        return {
            "status": "existing_user",
            "user_id": user.id,
            "character": {
                "name": user.character.name,
                "level": user.character.level,
                "health": user.character.health,
                "max_health": user.character.max_health,
                "destiny_tokens": user.character.destiny_tokens
            } if user.character else None
        }

@app.get("/user/{telegram_id}")
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Получить данные пользователя"""
    user = db.query(models.User).filter(
        models.User.telegram_id == telegram_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "character": {
            "name": user.character.name,
            "level": user.character.level,
            "experience": user.character.experience,
            "health": user.character.health,
            "max_health": user.character.max_health,
            "destiny_tokens": user.character.destiny_tokens,
            "gold": user.character.gold
        } if user.character else None
    }
