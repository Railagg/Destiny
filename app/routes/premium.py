from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import time

from database import get_db
from models import User, Character

router = APIRouter()

# Премиум планы
PREMIUM_PLANS = {
    "7days": {
        "id": "7days",
        "name": "🟢 Стартовый",
        "price_stars": 50,
        "price_ton": 1,
        "price_dstn": 2500,
        "duration": 7,
        "discount": 0,
        "first_purchase_discount_stars": 50,
        "first_purchase_discount_ton": 25,
        "ton_regular_discount": 10,
        "bonuses": {
            "max_energy": 150,
            "gold_multiplier": 1.1,
            "dstn_multiplier": 1.05,
            "exp_multiplier": 1.1,
            "luck": 5,
            "chests_per_day": 1,
            "house_rest_multiplier": 1.5,
            "daily_quests": 3,
            "inventory_slots": 50,
            "pet_exp_gain": 1.1,
            "exchange_bonus": {
                "ton_to_dstn": 2550,
                "fee_discount": 50,
                "daily_limit_multiplier": 1.5
            }
        },
        "gift": {
            "legendary_chest": 1,
            "dstn": 100,
            "gold": 5000,
            "items": ["teleport_scroll", 3]
        },
        "nick_color": "green",
        "frame": "premium_green"
    },
    "28days": {
        "id": "28days",
        "name": "🔵 Базовый",
        "price_stars": 150,
        "price_ton": 3,
        "price_dstn": 7500,
        "duration": 28,
        "discount": 25,
        "first_purchase_discount_stars": 50,
        "first_purchase_discount_ton": 25,
        "ton_regular_discount": 10,
        "bonuses": {
            "max_energy": 175,
            "gold_multiplier": 1.15,
            "dstn_multiplier": 1.1,
            "exp_multiplier": 1.15,
            "luck": 8,
            "chests_per_day": 2,
            "house_rest_multiplier": 1.7,
            "daily_quests": 4,
            "inventory_slots": 75,
            "pet_exp_gain": 1.15,
            "shop_discount": 5,
            "exchange_bonus": {
                "ton_to_dstn": 2600,
                "fee_discount": 75,
                "daily_limit_multiplier": 2.0
            }
        },
        "gift": {
            "legendary_chest": 3,
            "dstn": 500,
            "gold": 20000,
            "items": ["teleport_scroll", 10, "health_potion", 5, "mana_potion", 5]
        },
        "nick_color": "blue",
        "frame": "premium_blue"
    },
    "90days": {
        "id": "90days",
        "name": "🟣 Продвинутый",
        "price_stars": 400,
        "price_ton": 8,
        "price_dstn": 20000,
        "duration": 90,
        "discount": 40,
        "first_purchase_discount_stars": 50,
        "first_purchase_discount_ton": 25,
        "ton_regular_discount": 10,
        "bonuses": {
            "max_energy": 200,
            "gold_multiplier": 1.2,
            "dstn_multiplier": 1.15,
            "exp_multiplier": 1.2,
            "luck": 12,
            "chests_per_day": 3,
            "house_rest_multiplier": 2.0,
            "daily_quests": 5,
            "inventory_slots": 100,
            "pet_exp_gain": 1.2,
            "pet_happiness": 10,
            "shop_discount": 10,
            "extra_slot_auction": 1,
            "premium_chest_daily": True,
            "exchange_bonus": {
                "ton_to_dstn": 2650,
                "fee_discount": 90,
                "daily_limit_multiplier": 2.5
            }
        },
        "gift": {
            "legendary_chest": 10,
            "dstn": 2000,
            "gold": 100000,
            "items": ["teleport_scroll", 20, "health_potion", 10, "mana_potion", 10, "rainbow_shard", 1]
        },
        "nick_color": "purple",
        "frame": "premium_purple",
        "chat_access": "vip"
    },
    "180days": {
        "id": "180days",
        "name": "🟡 Элитный",
        "price_stars": 700,
        "price_ton": 14,
        "price_dstn": 35000,
        "duration": 180,
        "discount": 50,
        "first_purchase_discount_stars": 50,
        "first_purchase_discount_ton": 25,
        "ton_regular_discount": 10,
        "bonuses": {
            "max_energy": 225,
            "gold_multiplier": 1.25,
            "dstn_multiplier": 1.2,
            "exp_multiplier": 1.25,
            "luck": 15,
            "chests_per_day": 4,
            "house_rest_multiplier": 2.2,
            "daily_quests": 6,
            "inventory_slots": 125,
            "pet_exp_gain": 1.25,
            "pet_happiness": 15,
            "shop_discount": 15,
            "extra_slot_auction": 2,
            "premium_chest_daily": True,
            "rainbow_shard_weekly": 1,
            "teleport_cooldown_reduction": 50,
            "house_upgrade_discount": 10,
            "exchange_bonus": {
                "ton_to_dstn": 2700,
                "fee_free": True,
                "daily_limit_multiplier": 3.0
            }
        },
        "gift": {
            "legendary_chest": 20,
            "dstn": 5000,
            "gold": 250000,
            "items": ["teleport_scroll", 50, "health_potion", 20, "mana_potion", 20, "rainbow_shard", 3],
            "pet": "golden_pet"
        },
        "nick_color": "gold",
        "frame": "premium_gold",
        "chat_access": "elite"
    },
    "365days": {
        "id": "365days",
        "name": "🔴 Легендарный",
        "price_stars": 1200,
        "price_ton": 24,
        "price_dstn": 60000,
        "duration": 365,
        "discount": 65,
        "first_purchase_discount_stars": 50,
        "first_purchase_discount_ton": 25,
        "ton_regular_discount": 10,
        "bonuses": {
            "max_energy": 250,
            "gold_multiplier": 1.3,
            "dstn_multiplier": 1.25,
            "exp_multiplier": 1.3,
            "luck": 20,
            "chests_per_day": 5,
            "house_rest_multiplier": 2.5,
            "daily_quests": 8,
            "inventory_slots": 150,
            "pet_exp_gain": 1.3,
            "pet_happiness": 20,
            "shop_discount": 25,
            "extra_slot_auction": 3,
            "premium_chest_daily": True,
            "rainbow_shard_weekly": 1,
            "rainbow_stone_yearly": 1,
            "teleport_cooldown_reduction": 75,
            "house_upgrade_discount": 20,
            "crafting_discount": 10,
            "early_access": True,
            "voting_rights": True,
            "exchange_bonus": {
                "ton_to_dstn": 2800,
                "fee_free": True,
                "priority": True,
                "daily_limit_multiplier": 5.0
            }
        },
        "gift": {
            "legendary_chest": 50,
            "dstn": 15000,
            "gold": 1000000,
            "items": ["teleport_scroll", 100, "health_potion", 50, "mana_potion", 50, "rainbow_shard", 10, "rainbow_stone", 1],
            "pet": "dragon_pet",
            "skin": "legendary_skin",
            "title": "Легенда"
        },
        "nick_color": "red",
        "frame": "premium_legendary",
        "aura": "legendary_glow",
        "chat_access": "developer"
    }
}

# Награды за верность
RENEWAL_BONUSES = {
    "3months": {
        "name": "Верность 3 месяца",
        "requirement": "3 месяца подряд",
        "reward": {
            "rainbow_shard": 1,
            "legendary_chest": 5,
            "title": "Верный"
        }
    },
    "6months": {
        "name": "Верность 6 месяцев",
        "requirement": "6 месяцев подряд",
        "reward": {
            "rainbow_shard": 3,
            "legendary_chest": 15,
            "title": "Преданный",
            "frame": "loyalty_silver"
        }
    },
    "1year": {
        "name": "Верность 1 год",
        "requirement": "1 год подряд",
        "reward": {
            "rainbow_stone": 1,
            "legendary_chest": 30,
            "title": "Легендарный",
            "frame": "loyalty_gold",
            "aura": "loyalty_glow"
        }
    },
    "2years": {
        "name": "Верность 2 года",
        "requirement": "2 года подряд",
        "reward": {
            "rainbow_stone": 3,
            "legendary_chest": 60,
            "title": "Бессмертный",
            "frame": "loyalty_platinum",
            "aura": "immortal_glow"
        }
    },
    "3years": {
        "name": "Верность 3 года",
        "requirement": "3 года подряд",
        "reward": {
            "rainbow_stone": 5,
            "legendary_chest": 100,
            "title": "Бог",
            "frame": "loyalty_rainbow",
            "aura": "god_glow"
        }
    }
}

# ========== ОСНОВНЫЕ МАРШРУТЫ ==========

@router.get("/plans")
def get_premium_plans():
    """Получить список премиум тарифов"""
    return PREMIUM_PLANS

@router.get("/plan/{plan_id}")
def get_plan_details(plan_id: str):
    """Получить детали конкретного плана"""
    if plan_id not in PREMIUM_PLANS:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return PREMIUM_PLANS[plan_id]

@router.get("/renewal")
def get_renewal_bonuses():
    """Получить награды за верность"""
    return RENEWAL_BONUSES

# ========== ПОКУПКА ПРЕМИУМА ==========

@router.post("/buy/{plan_id}")
def buy_premium(
    plan_id: str, 
    user_id: int, 
    payment_method: str = "stars",
    db: Session = Depends(get_db)
):
    """Купить премиум подписку"""
    if plan_id not in PREMIUM_PLANS:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan = PREMIUM_PLANS[plan_id]
    
    # Проверяем пользователя
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Проверяем, первая ли покупка
    is_first = not user.premium_first_purchase
    
    # Рассчитываем цену
    price = 0
    if payment_method == "stars":
        price = plan["price_stars"]
        if is_first:
            price = int(price * (100 - plan["first_purchase_discount_stars"]) / 100)
        
        # Проверяем баланс (упрощённо)
        if getattr(character, 'stars', 0) < price:
            raise HTTPException(status_code=400, detail="Not enough Stars")
        
    elif payment_method == "ton":
        price = plan["price_ton"]
        # Постоянная скидка 10% на TON
        price = int(price * 90 / 100)
        if is_first:
            price = int(price * (100 - plan["first_purchase_discount_ton"]) / 100)
        
        if getattr(character, 'ton', 0) < price:
            raise HTTPException(status_code=400, detail="Not enough TON")
        
    elif payment_method == "dstn":
        price = plan["price_dstn"]
        if getattr(character, 'destiny_tokens', 0) < price:
            raise HTTPException(status_code=400, detail="Not enough DSTN")
        
    else:
        raise HTTPException(status_code=400, detail="Invalid payment method")
    
    # Списываем средства
    if payment_method == "stars":
        character.stars = getattr(character, 'stars', 0) - price
    elif payment_method == "ton":
        character.ton = getattr(character, 'ton', 0) - price
    elif payment_method == "dstn":
        character.destiny_tokens -= price
    
    # Активируем премиум
    now = datetime.utcnow()
    
    if user.premium_until and user.premium_until > now:
        # Продлеваем существующий
        user.premium_until += timedelta(days=plan["duration"])
        user.premium_total_days = (user.premium_total_days or 0) + plan["duration"]
    else:
        # Новый
        user.premium_until = now + timedelta(days=plan["duration"])
        user.premium_total_days = plan["duration"]
    
    user.premium_plan = plan_id
    user.premium_first_purchase = True
    
    # Выдаём подарок
    gift = plan["gift"]
    if gift.get("legendary_chest"):
        for _ in range(gift["legendary_chest"]):
            character.add_item("legendary_chest_key")
    
    if gift.get("dstn"):
        character.destiny_tokens += gift["dstn"]
    
    if gift.get("gold"):
        character.gold += gift["gold"]
    
    if gift.get("items"):
        items = gift["items"]
        if isinstance(items, list):
            if len(items) == 2 and isinstance(items[1], int):
                item_id, count = items
                for _ in range(count):
                    character.add_item(item_id)
            else:
                character.add_item(items[0])
    
    if gift.get("pet"):
        character.add_item(gift["pet"])
    
    if gift.get("skin"):
        character.profile_skin = gift["skin"]
    
    if gift.get("title"):
        if not user.titles:
            user.titles = []
        user.titles.append(gift["title"])
    
    # Применяем бонусы
    apply_premium_bonuses(character, plan)
    
    # Проверяем награды за верность
    check_renewal_bonuses(user, character)
    
    db.commit()
    
    return {
        "status": "success",
        "plan": plan["name"],
        "expires": user.premium_until.isoformat(),
        "total_days": user.premium_total_days
    }

# ========== СТАТУС ПРЕМИУМА ==========

@router.get("/status/{user_id}")
def get_premium_status(user_id: int, db: Session = Depends(get_db)):
    """Получить статус премиума игрока"""
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    now = datetime.utcnow()
    is_active = user.premium_until and user.premium_until > now
    
    if is_active:
        days_left = (user.premium_until - now).days
        hours_left = ((user.premium_until - now).seconds // 3600)
        
        # Получаем план
        plan = PREMIUM_PLANS.get(user.premium_plan, {})
        
        # Проверяем награды за верность
        renewal_earned = []
        if user.renewal_3months:
            renewal_earned.append("3 месяца")
        if user.renewal_6months:
            renewal_earned.append("6 месяцев")
        if user.renewal_1year:
            renewal_earned.append("1 год")
        if user.renewal_2years:
            renewal_earned.append("2 года")
        if user.renewal_3years:
            renewal_earned.append("3 года")
        
        return {
            "active": True,
            "plan": plan.get("name"),
            "plan_id": user.premium_plan,
            "expires": user.premium_until.isoformat(),
            "days_left": days_left,
            "hours_left": hours_left,
            "total_days": user.premium_total_days,
            "renewal_earned": renewal_earned,
            "bonuses": plan.get("bonuses", {})
        }
    else:
        return {
            "active": False,
            "total_days": user.premium_total_days or 0
        }

# ========== ЕЖЕДНЕВНЫЕ НАГРАДЫ ==========

@router.post("/daily/{user_id}")
def claim_daily_premium(user_id: int, db: Session = Depends(get_db)):
    """Получить ежедневную награду премиума"""
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    now = datetime.utcnow()
    
    # Проверяем, активен ли премиум
    if not user.premium_until or user.premium_until <= now:
        raise HTTPException(status_code=400, detail="Premium not active")
    
    # Проверяем, не получал ли уже сегодня
    last_claim = getattr(character, 'premium_last_daily', None)
    if last_claim:
        last = datetime.fromisoformat(last_claim) if isinstance(last_claim, str) else last_claim
        if last.date() == now.date():
            raise HTTPException(status_code=400, detail="Already claimed today")
    
    # Определяем награду по плану
    plan = PREMIUM_PLANS.get(user.premium_plan, {})
    daily = plan.get("daily_rewards", {})
    
    rewards = []
    
    if daily.get("gold"):
        character.gold += daily["gold"]
        rewards.append(f"{daily['gold']}💰")
    
    if daily.get("dstn"):
        character.destiny_tokens += daily["dstn"]
        rewards.append(f"{daily['dstn']}🪙")
    
    if daily.get("items"):
        for item in daily["items"]:
            if isinstance(item, list):
                item_id, count = item
                for _ in range(count):
                    character.add_item(item_id)
                rewards.append(f"{item_id} x{count}")
            else:
                character.add_item(item)
                rewards.append(item)
    
    # Особые награды для высоких планов
    if plan.get("premium_chest_daily"):
        character.add_item("premium_chest_key")
        rewards.append("premium_chest_key")
    
    if plan.get("rainbow_shard_weekly"):
        # Проверяем, не получил ли уже на этой неделе
        last_weekly = getattr(character, 'premium_last_weekly', None)
        if last_weekly:
            last = datetime.fromisoformat(last_weekly) if isinstance(last_weekly, str) else last_weekly
            week_number = now.isocalendar()[1]
            last_week = last.isocalendar()[1]
            if week_number != last_week:
                character.rainbow_shards = (character.rainbow_shards or 0) + 1
                character.premium_last_weekly = now.isoformat()
                rewards.append("1🌈")
        else:
            character.rainbow_shards = (character.rainbow_shards or 0) + 1
            character.premium_last_weekly = now.isoformat()
            rewards.append("1🌈")
    
    character.premium_last_daily = now.isoformat()
    db.commit()
    
    return {
        "status": "claimed",
        "rewards": rewards
    }

# ========== НАГРАДЫ ЗА ВЕРНОСТЬ ==========

@router.get("/renewal/{user_id}")
def get_renewal_status(user_id: int, db: Session = Depends(get_db)):
    """Получить статус наград за верность"""
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_days = user.premium_total_days or 0
    
    earned = []
    if user.renewal_3months:
        earned.append("3months")
    if user.renewal_6months:
        earned.append("6months")
    if user.renewal_1year:
        earned.append("1year")
    if user.renewal_2years:
        earned.append("2years")
    if user.renewal_3years:
        earned.append("3years")
    
    available = []
    if total_days >= 90 and not user.renewal_3months:
        available.append("3months")
    if total_days >= 180 and not user.renewal_6months:
        available.append("6months")
    if total_days >= 365 and not user.renewal_1year:
        available.append("1year")
    if total_days >= 730 and not user.renewal_2years:
        available.append("2years")
    if total_days >= 1095 and not user.renewal_3years:
        available.append("3years")
    
    return {
        "total_days": total_days,
        "earned": earned,
        "available": available,
        "next_milestone": get_next_milestone(total_days)
    }

@router.post("/renewal/claim/{milestone}")
def claim_renewal_reward(
    user_id: int, 
    milestone: str, 
    db: Session = Depends(get_db)
):
    """Забрать награду за верность"""
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    total_days = user.premium_total_days or 0
    
    # Проверяем, доступна ли награда
    if milestone == "3months" and total_days >= 90 and not user.renewal_3months:
        user.renewal_3months = True
        reward = RENEWAL_BONUSES["3months"]["reward"]
    elif milestone == "6months" and total_days >= 180 and not user.renewal_6months:
        user.renewal_6months = True
        reward = RENEWAL_BONUSES["6months"]["reward"]
    elif milestone == "1year" and total_days >= 365 and not user.renewal_1year:
        user.renewal_1year = True
        reward = RENEWAL_BONUSES["1year"]["reward"]
    elif milestone == "2years" and total_days >= 730 and not user.renewal_2years:
        user.renewal_2years = True
        reward = RENEWAL_BONUSES["2years"]["reward"]
    elif milestone == "3years" and total_days >= 1095 and not user.renewal_3years:
        user.renewal_3years = True
        reward = RENEWAL_BONUSES["3years"]["reward"]
    else:
        raise HTTPException(status_code=400, detail="Reward not available")
    
    # Выдаём награду
    claimed = []
    
    if reward.get("rainbow_shard"):
        character.rainbow_shards = (character.rainbow_shards or 0) + reward["rainbow_shard"]
        claimed.append(f"{reward['rainbow_shard']}🌈")
    
    if reward.get("rainbow_stone"):
        character.rainbow_stones = (character.rainbow_stones or 0) + reward["rainbow_stone"]
        claimed.append(f"{reward['rainbow_stone']}💎")
    
    if reward.get("legendary_chest"):
        for _ in range(reward["legendary_chest"]):
            character.add_item("legendary_chest_key")
        claimed.append(f"{reward['legendary_chest']} легендарных сундуков")
    
    if reward.get("title"):
        if not user.titles:
            user.titles = []
        user.titles.append(reward["title"])
        claimed.append(f"титул '{reward['title']}'")
    
    if reward.get("frame"):
        user.profile_frame = reward["frame"]
        claimed.append("особая рамка")
    
    if reward.get("aura"):
        user.profile_aura = reward["aura"]
        claimed.append("особая аура")
    
    db.commit()
    
    return {
        "status": "claimed",
        "milestone": milestone,
        "rewards": claimed
    }

# ========== СРАВНЕНИЕ ПЛАНОВ ==========

@router.get("/compare")
def compare_plans():
    """Сравнить все планы"""
    comparison = []
    
    for plan_id, plan in PREMIUM_PLANS.items():
        comparison.append({
            "id": plan_id,
            "name": plan["name"],
            "price_stars": plan["price_stars"],
            "price_ton": plan["price_ton"],
            "duration": plan["duration"],
            "price_per_day": round(plan["price_stars"] / plan["duration"], 2),
            "bonuses": {
                "max_energy": plan["bonuses"]["max_energy"],
                "gold_multiplier": plan["bonuses"]["gold_multiplier"],
                "exp_multiplier": plan["bonuses"]["exp_multiplier"],
                "chests_per_day": plan["bonuses"]["chests_per_day"],
                "inventory_slots": plan["bonuses"].get("inventory_slots", 0),
                "rainbow_shard_weekly": plan["bonuses"].get("rainbow_shard_weekly", 0)
            }
        })
    
    return comparison

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def apply_premium_bonuses(character, plan):
    """Применить бонусы премиума к персонажу"""
    bonuses = plan.get("bonuses", {})
    
    character.max_energy = bonuses.get("max_energy", character.max_energy)
    character.gold_multiplier = bonuses.get("gold_multiplier", 1.0)
    character.exp_multiplier = bonuses.get("exp_multiplier", 1.0)
    character.luck_bonus = bonuses.get("luck", 0)
    character.chests_per_day = bonuses.get("chests_per_day", 0)
    character.inventory_slots_bonus = bonuses.get("inventory_slots", 0)
    character.house_rest_multiplier = bonuses.get("house_rest_multiplier", 1.0)
    character.pet_exp_gain = bonuses.get("pet_exp_gain", 1.0)
    
    if bonuses.get("rainbow_shard_weekly"):
        character.rainbow_shard_weekly = bonuses["rainbow_shard_weekly"]
    
    if bonuses.get("exchange_bonus"):
        character.exchange_bonus = bonuses["exchange_bonus"]

def check_renewal_bonuses(user, character):
    """Проверить и выдать награды за верность"""
    total_days = user.premium_total_days or 0
    
    if total_days >= 90 and not user.renewal_3months:
        user.renewal_3months = True
        character.rainbow_shards = (character.rainbow_shards or 0) + 1
        if not user.titles:
            user.titles = []
        user.titles.append("Верный")
    
    if total_days >= 180 and not user.renewal_6months:
        user.renewal_6months = True
        character.rainbow_shards = (character.rainbow_shards or 0) + 3
        user.profile_frame = "loyalty_silver"
        if not user.titles:
            user.titles = []
        user.titles.append("Преданный")
    
    if total_days >= 365 and not user.renewal_1year:
        user.renewal_1year = True
        character.rainbow_stones = (character.rainbow_stones or 0) + 1
        user.profile_frame = "loyalty_gold"
        user.profile_aura = "loyalty_glow"
        if not user.titles:
            user.titles = []
        user.titles.append("Легендарный")
    
    if total_days >= 730 and not user.renewal_2years:
        user.renewal_2years = True
        character.rainbow_stones = (character.rainbow_stones or 0) + 3
        user.profile_frame = "loyalty_platinum"
        user.profile_aura = "immortal_glow"
        if not user.titles:
            user.titles = []
        user.titles.append("Бессмертный")
    
    if total_days >= 1095 and not user.renewal_3years:
        user.renewal_3years = True
        character.rainbow_stones = (character.rainbow_stones or 0) + 5
        user.profile_frame = "loyalty_rainbow"
        user.profile_aura = "god_glow"
        if not user.titles:
            user.titles = []
        user.titles.append("Бог")

def get_next_milestone(total_days):
    """Получить следующий рубеж для наград"""
    if total_days < 90:
        return {"milestone": "3months", "days_needed": 90 - total_days}
    elif total_days < 180:
        return {"milestone": "6months", "days_needed": 180 - total_days}
    elif total_days < 365:
        return {"milestone": "1year", "days_needed": 365 - total_days}
    elif total_days < 730:
        return {"milestone": "2years", "days_needed": 730 - total_days}
    elif total_days < 1095:
        return {"milestone": "3years", "days_needed": 1095 - total_days}
    else:
        return None
