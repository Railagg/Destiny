from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json

from database import get_db
from models import User, Character
from utils import locations_data, items_data

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
