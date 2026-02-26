from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time
import random

from database import get_db
from models import User, Character

router = APIRouter(prefix="/daily", tags=["Daily"])

# Награды за стрик
STREAK_REWARDS = {
    1: {"gold": 100, "dstn": 5, "items": []},
    2: {"gold": 200, "dstn": 10, "items": []},
    3: {"gold": 300, "dstn": 15, "items": ["health_potion"]},
    4: {"gold": 400, "dstn": 20, "items": []},
    5: {"gold": 500, "dstn": 25, "items": ["mana_potion"]},
    6: {"gold": 600, "dstn": 30, "items": []},
    7: {"gold": 1000, "dstn": 50, "items": ["legendary_chest_key"], "premium_day": True},
    8: {"gold": 700, "dstn": 35, "items": []},
    9: {"gold": 800, "dstn": 40, "items": ["teleport_scroll"]},
    10: {"gold": 900, "dstn": 45, "items": []},
    11: {"gold": 1000, "dstn": 50, "items": []},
    12: {"gold": 1100, "dstn": 55, "items": ["mythril_ingot"]},
    13: {"gold": 1200, "dstn": 60, "items": []},
    14: {"gold": 1300, "dstn": 65, "items": [], "premium_day": True},
    15: {"gold": 1400, "dstn": 70, "items": ["diamond"]},
    16: {"gold": 1500, "dstn": 75, "items": []},
    17: {"gold": 1600, "dstn": 80, "items": []},
    18: {"gold": 1700, "dstn": 85, "items": ["magic_crystal"]},
    19: {"gold": 1800, "dstn": 90, "items": []},
    20: {"gold": 2000, "dstn": 100, "items": ["epic_chest_key"]},
    21: {"gold": 2200, "dstn": 110, "items": [], "premium_day": True},
    25: {"gold": 2500, "dstn": 125, "items": ["rainbow_shard"]},
    28: {"gold": 2800, "dstn": 140, "items": [], "premium_day": True},
    30: {"gold": 3000, "dstn": 150, "items": ["mythril_ingot", 3, "legendary_chest_key"]},
    35: {"gold": 3500, "dstn": 175, "items": [], "premium_day": True},
    40: {"gold": 4000, "dstn": 200, "items": ["dragon_scale"]},
    42: {"gold": 4200, "dstn": 210, "items": [], "premium_day": True},
    45: {"gold": 4500, "dstn": 225, "items": ["phoenix_feather"]},
    49: {"gold": 4900, "dstn": 245, "items": [], "premium_day": True},
    50: {"gold": 5000, "dstn": 250, "items": ["legendary_chest_key", 2]},
    56: {"gold": 5600, "dstn": 280, "items": [], "premium_day": True},
    60: {"gold": 6000, "dstn": 300, "items": ["divine_essence"]},
    63: {"gold": 6300, "dstn": 315, "items": [], "premium_day": True},
    70: {"gold": 7000, "dstn": 350, "items": ["dragon_heart"]},
    77: {"gold": 7700, "dstn": 385, "items": [], "premium_day": True},
    80: {"gold": 8000, "dstn": 400, "items": ["rainbow_stone"]},
    84: {"gold": 8400, "dstn": 420, "items": [], "premium_day": True},
    90: {"gold": 9000, "dstn": 450, "items": ["mythic_pet_egg"]},
    91: {"gold": 9100, "dstn": 455, "items": [], "premium_day": True},
    98: {"gold": 9800, "dstn": 490, "items": [], "premium_day": True},
    100: {"gold": 10000, "dstn": 500, "items": ["divine_elixir"], "title": "Легендарная преданность"}
}

# Достижения за стрик
STREAK_ACHIEVEMENTS = {
    7: {"title": "Первая неделя", "rainbow_shard": 1},
    30: {"title": "Месячный ветеран", "rainbow_shard": 2},
    100: {"title": "Сотня дней", "rainbow_stone": 1, "frame": "streak_gold"},
    365: {"title": "Год верности", "rainbow_stone": 3, "frame": "streak_platinum", "aura": "streak_glow"},
    1000: {"title": "Бессмертный", "rainbow_stone": 10, "frame": "streak_rainbow", "aura": "immortal_glow"}
}

@router.post("/login")
def daily_login(user_id: int, db: Session = Depends(get_db)):
    """Ежедневный вход - проверка стрика и выдача наград"""
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    now = int(time.time())
    last_login = user.last_login or 0
    today = datetime.now().date()
    
    # Проверяем, заходил ли уже сегодня
    if last_login and datetime.fromtimestamp(last_login).date() == today:
        # Уже сегодня заходил, просто показываем статус
        return {
            "status": "already_logged",
            "streak": user.login_streak,
            "max_streak": user.max_streak,
            "next_reward": get_next_reward_info(user.login_streak + 1)
        }
    
    # Логика стрика
    was_streak_broken = False
    if last_login and (now - last_login) < 172800:  # меньше 48 часов
        user.login_streak += 1
    else:
        if user.login_streak > 0:
            was_streak_broken = True
        user.login_streak = 1  # новый стрик или сброс
    
    # Обновляем максимальный стрик
    if user.login_streak > (user.max_streak or 0):
        user.max_streak = user.login_streak
    
    user.last_login = now
    
    # Получаем награды за текущий стрик
    rewards = get_streak_reward(user.login_streak)
    reward_text = []
    
    # Выдаём золото
    if rewards.get("gold"):
        character.gold += rewards["gold"]
        reward_text.append(f"{rewards['gold']}💰")
    
    # Выдаём DSTN
    if rewards.get("dstn"):
        character.destiny_tokens += rewards["dstn"]
        reward_text.append(f"{rewards['dstn']}🪙")
    
    # Выдаём предметы
    for item in rewards.get("items", []):
        if isinstance(item, list):
            item_id, count = item
            for _ in range(count):
                character.add_item(item_id)
            reward_text.append(f"{item_id} x{count}")
        else:
            character.add_item(item)
            reward_text.append(item)
    
    # Проверка на премиум за стрик
    premium_granted = False
    if rewards.get("premium_day"):
        premium_end = datetime.utcnow() + timedelta(days=1)
        
        if user.premium_from_streak and user.premium_from_streak > datetime.utcnow():
            # Если уже есть, продлеваем
            user.premium_from_streak += timedelta(days=1)
        else:
            user.premium_from_streak = premium_end
        
        user.streak_premium_days = (user.streak_premium_days or 0) + 1
        premium_granted = True
        reward_text.append("👑 Премиум на 1 день")
    
    # Проверка на титулы за стрик
    title_earned = None
    for streak_needed, ach in STREAK_ACHIEVEMENTS.items():
        if user.login_streak == streak_needed:
            if not user.titles:
                user.titles = []
            user.titles.append(ach["title"])
            title_earned = ach["title"]
            reward_text.append(f"🏆 Титул '{ach['title']}'")
            
            # Дополнительные награды
            if ach.get("rainbow_shard"):
                character.rainbow_shards = (character.rainbow_shards or 0) + ach["rainbow_shard"]
                reward_text.append(f"{ach['rainbow_shard']}🌈")
            if ach.get("rainbow_stone"):
                character.rainbow_stones = (character.rainbow_stones or 0) + ach["rainbow_stone"]
                reward_text.append(f"{ach['rainbow_stone']}💎")
            if ach.get("frame"):
                user.profile_frame = ach["frame"]
            if ach.get("aura"):
                user.profile_aura = ach["aura"]
    
    # Сохраняем историю
    streak_history = user.streak_history or []
    streak_history.append({
        "date": datetime.now().isoformat(),
        "streak": user.login_streak,
        "rewards": reward_text
    })
    user.streak_history = streak_history[-30:]  # храним последние 30 записей
    
    db.commit()
    
    return {
        "status": "success",
        "streak": user.login_streak,
        "max_streak": user.max_streak,
        "was_streak_broken": was_streak_broken,
        "rewards": reward_text,
        "premium_granted": premium_granted,
        "title_earned": title_earned,
        "next_reward": get_next_reward_info(user.login_streak + 1),
        "premium_active": user.premium_from_streak and user.premium_from_streak > datetime.utcnow()
    }

@router.get("/streak/{user_id}")
def get_streak_info(user_id: int, db: Session = Depends(get_db)):
    """Получить информацию о стрике игрока"""
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    now = int(time.time())
    last_login = user.last_login or 0
    
    # Проверяем, не сгорел ли стрик
    streak_burned = False
    if last_login and (now - last_login) > 172800:  # больше 48 часов
        streak_burned = True
    
    # Информация о следующей награде
    next_reward = get_next_reward_info(user.login_streak + 1) if not streak_burned else None
    
    # Информация о ближайшем премиуме
    days_to_premium = None
    for i in range(1, 8):
        check_streak = user.login_streak + i
        reward = STREAK_REWARDS.get(check_streak)
        if reward and reward.get("premium_day"):
            days_to_premium = i
            break
    
    return {
        "current_streak": user.login_streak if not streak_burned else 0,
        "max_streak": user.max_streak or 0,
        "streak_burned": streak_burned,
        "last_login": last_login,
        "hours_since_login": (now - last_login) // 3600 if last_login else 0,
        "next_reward": next_reward,
        "days_to_premium": days_to_premium,
        "premium_from_streak": user.premium_from_streak.isoformat() if user.premium_from_streak and user.premium_from_streak > datetime.utcnow() else None,
        "streak_premium_days": user.streak_premium_days or 0,
        "history": user.streak_history[-5:] if user.streak_history else []  # последние 5 записей
    }

@router.get("/calendar")
def get_streak_calendar(user_id: int, month: int = None, year: int = None, db: Session = Depends(get_db)):
    """Получить календарь входов (для визуализации)"""
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Здесь можно реализовать получение истории входов по дням
    # Пока возвращаем заглушку
    return {
        "user_id": user_id,
        "current_streak": user.login_streak,
        "max_streak": user.max_streak
    }

def get_streak_reward(streak: int):
    """Получить награду за конкретный стрик"""
    # Ищем точное совпадение
    if streak in STREAK_REWARDS:
        return STREAK_REWARDS[streak]
    
    # Если нет точного, ищем ближайший меньший
    available = sorted([s for s in STREAK_REWARDS.keys() if s <= streak], reverse=True)
    if available:
        base_reward = STREAK_REWARDS[available[0]].copy()
        # Масштабируем золото и DSTN
        days_diff = streak - available[0]
        if days_diff > 0:
            base_reward["gold"] = base_reward.get("gold", 0) + days_diff * 50
            base_reward["dstn"] = base_reward.get("dstn", 0) + days_diff * 2
        return base_reward
    
    # Базовая награда по умолчанию
    return {
        "gold": streak * 50,
        "dstn": streak * 2,
        "items": []
    }

def get_next_reward_info(next_streak: int):
    """Получить информацию о следующей награде"""
    reward = get_streak_reward(next_streak)
    return {
        "streak": next_streak,
        "gold": reward.get("gold", 0),
        "dstn": reward.get("dstn", 0),
        "items": reward.get("items", []),
        "premium_day": reward.get("premium_day", False)
    }
