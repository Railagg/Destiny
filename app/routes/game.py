from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json

from database import get_db
from models import User, Character
from utils import locations_data, items_data, enemies_data, quests_data

router = APIRouter()

@router.get("/location/{location_id}")
def get_location(location_id: str):
    """Получить информацию о локации"""
    location = locations_data.get("locations", {}).get(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

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
        "gold": character.gold if character else 0,
        "destiny_tokens": character.destiny_tokens if character else 0,
        "location": character.location if character else "start"
    }

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
    
    return {"items": items}

@router.get("/codex/{section}")
def get_codex(section: str):
    """Получить раздел энциклопедии"""
    from utils import codex_data
    
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
