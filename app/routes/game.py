from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json

from database import get_db
from models import User, Character
from utils import (
    locations_data, items_data, enemies_data, 
    quests_data, codex_data, crafting_data,
    classes_data, house_data, premium_data,
    nft_data, rainbow_data, events_data,
    biomes_data, islands_data, secrets_data
)

router = APIRouter()

# ========== ЛОКАЦИИ ==========
@router.get("/location/{location_id}")
def get_location(location_id: str):
    """Получить информацию о локации"""
    # Проверяем в основных локациях
    location = locations_data.get("locations", {}).get(location_id)
    
    # Если не нашли, проверяем в биомах
    if not location:
        for biome in biomes_data.get("biomes", {}).values():
            if biome.get("id") == location_id:
                return biome
    
    # Проверяем в островах
    if not location:
        for island in islands_data.get("islands", {}).values():
            if island.get("id") == location_id:
                return island
    
    # Проверяем в секретных локациях
    if not location:
        for secret in secrets_data.get("secrets", {}).values():
            if secret.get("id") == location_id:
                return secret
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

# ========== ПОЛЬЗОВАТЕЛИ ==========
@router.get("/user/{telegram_id}")
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Получить данные пользователя"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "level": character.level if character else 1,
        "class": character.player_class if character else None,
        "gold": character.gold if character else 0,
        "destiny_tokens": character.destiny_tokens if character else 0,
        "location": character.location if character else "start"
    }

# ========== ИНВЕНТАРЬ ==========
@router.get("/inventory/{telegram_id}")
def get_inventory(telegram_id: int, db: Session = Depends(get_db)):
    """Получить инвентарь игрока"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    inventory = character.get_inventory()
    items = []
    for item_id in inventory:
        item = items_data.get("items", {}).get(item_id)
        if item:
            items.append(item)
    
    return {
        "items": items,
        "count": len(items),
        "max_size": 100
    }

# ========== ЭНЦИКЛОПЕДИЯ ==========
@router.get("/codex/{section}")
def get_codex(section: str):
    """Получить раздел энциклопедии"""
    sections = {
        "bestiary": "bestiary",
        "items": "items",
        "locations": "locations",
        "achievements": "achievements",
        "crafting": "crafting",
        "classes": "classes"
    }
    
    if section not in sections:
        raise HTTPException(status_code=404, detail="Section not found")
    
    return codex_data.get("codex", {}).get(sections[section], {})

# ========== КРАФТ ==========
@router.get("/craft/{item_id}")
def get_craft_recipe(item_id: str):
    """Получить рецепт крафта предмета"""
    recipes = crafting_data.get("crafting", {})
    
    # Ищем во всех категориях
    for category in recipes.values():
        if item_id in category.get("items", {}):
            return category["items"][item_id]
    
    raise HTTPException(status_code=404, detail="Recipe not found")

# ========== ДОМИК ==========
@router.get("/house/{telegram_id}")
def get_house_info(telegram_id: int, db: Session = Depends(get_db)):
    """Получить информацию о домике игрока"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    
    return {
        "level": character.house_level if character else 0,
        "features": house_data.get("house", {}).get("levels", {}).get(str(character.house_level), {})
    }

# ========== ИВЕНТЫ ==========
@router.get("/events/today")
def get_today_event():
    """Получить ивент на сегодня"""
    import datetime
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    today = days[datetime.datetime.today().weekday()]
    
    return events_data.get("weekly_events", {}).get(today, {})

# ========== РЕЙТИНГИ ==========
@router.get("/top/{category}")
def get_top(category: str, limit: int = 10, db: Session = Depends(get_db)):
    """Получить топ игроков по категории"""
    if category == "level":
        characters = db.query(Character).order_by(Character.level.desc()).limit(limit).all()
        return [{"user_id": c.user_id, "level": c.level} for c in characters]
    
    elif category == "gold":
        characters = db.query(Character).order_by(Character.gold.desc()).limit(limit).all()
        return [{"user_id": c.user_id, "gold": c.gold} for c in characters]
    
    else:
        raise HTTPException(status_code=400, detail="Invalid category")
