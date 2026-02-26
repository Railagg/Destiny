from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import json
import time

from database import get_db
from models import User, Character

router = APIRouter()

# Данные из nft.json (5 видов, по 10 шт каждого)
NFT_SHARDS = {
    "red": {
        "id": "red",
        "name": "🔴 Красный осколок силы",
        "element": "🔥 Огонь",
        "color": "red",
        "total_supply": 10,
        "sold": 0,
        "price_stars": 100,
        "price_ton": 1.8,
        "price_dstn": 5000,
        "bonuses": [
            "+5% к урону",
            "+5% к огненному урону",
            "+2 к силе"
        ],
        "ability": {
            "name": "Ярость",
            "description": "+25% к урону на 1 минуту",
            "cooldown": 86400,  # 24 часа в секундах
            "cooldown_text": "1 день"
        },
        "house_item": "🔴 Алтарь огня",
        "image": "nft_red.jpeg"
    },
    "blue": {
        "id": "blue",
        "name": "🔵 Синий осколок защиты",
        "element": "❄️ Лёд",
        "color": "blue",
        "total_supply": 10,
        "sold": 0,
        "price_stars": 100,
        "price_ton": 1.8,
        "price_dstn": 5000,
        "bonuses": [
            "+5% к защите",
            "+5% к магической защите",
            "+50 к здоровью"
        ],
        "ability": {
            "name": "Щит",
            "description": "+50% к защите на 1 минуту",
            "cooldown": 86400,
            "cooldown_text": "1 день"
        },
        "house_item": "🔵 Алтарь льда",
        "image": "nft_blue.jpeg"
    },
    "green": {
        "id": "green",
        "name": "🟢 Зелёный осколок ловкости",
        "element": "🌿 Природа",
        "color": "green",
        "total_supply": 10,
        "sold": 0,
        "price_stars": 100,
        "price_ton": 1.8,
        "price_dstn": 5000,
        "bonuses": [
            "+5% к уклонению",
            "+5% к скорости атаки",
            "+2 к ловкости"
        ],
        "ability": {
            "name": "Ветер",
            "description": "+50% к скорости на 1 минуту",
            "cooldown": 86400,
            "cooldown_text": "1 день"
        },
        "house_item": "🟢 Алтарь природы",
        "image": "nft_green.jpeg"
    },
    "yellow": {
        "id": "yellow",
        "name": "🟡 Жёлтый осколок магии",
        "element": "⚡ Молния",
        "color": "yellow",
        "total_supply": 10,
        "sold": 0,
        "price_stars": 100,
        "price_ton": 1.8,
        "price_dstn": 5000,
        "bonuses": [
            "+5% к магическому урону",
            "+50 к мане",
            "+2 к интеллекту"
        ],
        "ability": {
            "name": "Молния",
            "description": "300% магического урона по 5 целям",
            "cooldown": 86400,
            "cooldown_text": "1 день"
        },
        "house_item": "🟡 Алтарь молний",
        "image": "nft_yellow.jpeg"
    },
    "purple": {
        "id": "purple",
        "name": "🟣 Фиолетовый осколок удачи",
        "element": "🌑 Тьма",
        "color": "purple",
        "total_supply": 10,
        "sold": 0,
        "price_stars": 200,
        "price_ton": 3.6,
        "price_dstn": 10000,
        "bonuses": [
            "+7% к удаче",
            "+5% к шансу редких находок",
            "+1 ко всем характеристикам"
        ],
        "ability": {
            "name": "Удача",
            "description": "+50% к удаче на 30 минут",
            "cooldown": 86400,
            "cooldown_text": "1 день"
        },
        "house_item": "🟣 Алтарь тьмы",
        "image": "nft_purple.jpeg"
    }
}

SET_BONUSES = {
    2: {
        "name": "Коллекционер",
        "description": "+2% ко всем характеристикам",
        "effect": {"all_stats": 2}
    },
    3: {
        "name": "Хранитель стихий",
        "description": "+3% ко всем характеристикам, +1% к шансу крита",
        "effect": {"all_stats": 3, "crit_chance": 1}
    },
    4: {
        "name": "Повелитель стихий",
        "description": "+4% ко всем характеристикам, +2% к шансу крита, +50 здоровья",
        "effect": {"all_stats": 4, "crit_chance": 2, "health": 50}
    },
    5: {
        "name": "Бог стихий",
        "description": "+5% ко всем характеристикам, +3% к шансу крита, +100 здоровья, +50 маны, радужный ник, аура",
        "effect": {"all_stats": 5, "crit_chance": 3, "health": 100, "mana": 50, "rainbow_nick": True, "aura": True}
    }
}

# ========== ОСНОВНЫЕ МАРШРУТЫ ==========

@router.get("/list")
def get_nft_list():
    """Получить список всех NFT"""
    nft_list = []
    for color, data in NFT_SHARDS.items():
        nft_list.append({
            "id": color,
            "name": data["name"],
            "element": data["element"],
            "total_supply": data["total_supply"],
            "sold": data["sold"],
            "available": data["total_supply"] - data["sold"],
            "price_stars": data["price_stars"],
            "price_ton": data["price_ton"],
            "price_dstn": data["price_dstn"],
            "bonuses": data["bonuses"][:2],  # Только первые 2 для превью
            "image": data["image"]
        })
    
    return {
        "total": len(nft_list),
        "nfts": nft_list
    }

@router.get("/{color}")
def get_nft_info(color: str):
    """Получить информацию о конкретном NFT"""
    if color not in NFT_SHARDS:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    shard = NFT_SHARDS[color].copy()
    shard["available"] = shard["total_supply"] - shard["sold"]
    
    return shard

@router.get("/collection/set_bonuses")
def get_set_bonuses():
    """Получить бонусы за коллекцию NFT"""
    return SET_BONUSES

# ========== ПОКУПКА NFT ==========

@router.post("/buy/{color}")
def buy_nft(
    color: str, 
    user_id: int, 
    payment_method: str = "dstn",
    db: Session = Depends(get_db)
):
    """Купить NFT осколок"""
    if color not in NFT_SHARDS:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    shard = NFT_SHARDS[color]
    
    # Проверяем наличие
    if shard["sold"] >= shard["total_supply"]:
        raise HTTPException(status_code=400, detail="NFT sold out")
    
    # Проверяем пользователя
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Проверяем, есть ли уже такой осколок
    nft_collection = character.nft_collection or []
    if color in nft_collection:
        raise HTTPException(status_code=400, detail="Already own this NFT")
    
    # Проверяем платёж
    if payment_method == "dstn":
        price = shard["price_dstn"]
        if character.destiny_tokens < price:
            raise HTTPException(status_code=400, detail="Not enough DSTN")
        character.destiny_tokens -= price
    elif payment_method == "stars":
        price = shard["price_stars"]
        if getattr(character, 'stars', 0) < price:
            raise HTTPException(status_code=400, detail="Not enough Stars")
        character.stars = getattr(character, 'stars', 0) - price
    elif payment_method == "ton":
        price = shard["price_ton"]
        if getattr(character, 'ton', 0) < price:
            raise HTTPException(status_code=400, detail="Not enough TON")
        character.ton = getattr(character, 'ton', 0) - price
    else:
        raise HTTPException(status_code=400, detail="Invalid payment method")
    
    # Добавляем NFT
    nft_collection.append(color)
    character.nft_collection = nft_collection
    shard["sold"] += 1
    
    # Добавляем предмет для дома
    house_items = character.house_furniture or []
    house_items.append(f"nft_altar_{color}")
    character.house_furniture = house_items
    
    # Применяем бонусы
    apply_nft_bonuses(character)
    
    db.commit()
    
    return {
        "status": "success",
        "nft": shard["name"],
        "collection_size": len(nft_collection),
        "set_bonus": SET_BONUSES.get(len(nft_collection), {}).get("name")
    }

# ========== КОЛЛЕКЦИЯ ИГРОКА ==========

@router.get("/user/{user_id}")
def get_user_nft_collection(user_id: int, db: Session = Depends(get_db)):
    """Получить NFT коллекцию игрока"""
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    nft_collection = character.nft_collection or []
    
    # Детальная информация о каждом NFT
    nfts = []
    for nft_id in nft_collection:
        if nft_id in NFT_SHARDS:
            shard = NFT_SHARDS[nft_id]
            nfts.append({
                "id": nft_id,
                "name": shard["name"],
                "element": shard["element"],
                "bonuses": shard["bonuses"],
                "ability": shard["ability"],
                "house_item": shard["house_item"],
                "image": shard["image"]
            })
    
    # Активный сетовый бонус
    set_bonus = None
    collection_size = len(nft_collection)
    if collection_size in SET_BONUSES:
        set_bonus = SET_BONUSES[collection_size]
    
    return {
        "user_id": user_id,
        "collection_size": collection_size,
        "nfts": nfts,
        "set_bonus": set_bonus
    }

# ========== АКТИВАЦИЯ СПОСОБНОСТЕЙ ==========

@router.post("/use/{color}")
def use_nft_ability(color: str, user_id: int, db: Session = Depends(get_db)):
    """Использовать способность NFT"""
    if color not in NFT_SHARDS:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    nft_collection = character.nft_collection or []
    if color not in nft_collection:
        raise HTTPException(status_code=400, detail="You don't own this NFT")
    
    # Проверяем кулдаун
    now = int(time.time())
    last_use_key = f"nft_last_use_{color}"
    last_use = getattr(character, last_use_key, 0)
    
    cooldown = NFT_SHARDS[color]["ability"]["cooldown"]
    if now - last_use < cooldown:
        remaining = cooldown - (now - last_use)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        raise HTTPException(
            status_code=400, 
            detail=f"Ability on cooldown. Time left: {hours}h {minutes}m"
        )
    
    # Активируем способность
    setattr(character, last_use_key, now)
    
    # Применяем эффект (упрощённо)
    effect = NFT_SHARDS[color]["ability"]["name"]
    
    db.commit()
    
    return {
        "status": "activated",
        "ability": NFT_SHARDS[color]["ability"]["name"],
        "effect": NFT_SHARDS[color]["ability"]["description"],
        "cooldown": NFT_SHARDS[color]["ability"]["cooldown_text"]
    }

# ========== СТАТИСТИКА ==========

@router.get("/stats/global")
def get_global_stats():
    """Получить глобальную статистику NFT"""
    total_supply = sum(s["total_supply"] for s in NFT_SHARDS.values())
    total_sold = sum(s["sold"] for s in NFT_SHARDS.values())
    
    return {
        "total_supply": total_supply,
        "total_sold": total_sold,
        "percentage_sold": round(total_sold / total_supply * 100, 2) if total_supply > 0 else 0,
        "by_color": {
            color: {
                "total": data["total_supply"],
                "sold": data["sold"],
                "available": data["total_supply"] - data["sold"]
            }
            for color, data in NFT_SHARDS.items()
        }
    }

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def apply_nft_bonuses(character):
    """Применить бонусы от NFT к персонажу"""
    nft_collection = character.nft_collection or []
    collection_size = len(nft_collection)
    
    # Сбрасываем старые бонусы
    character.fire_damage_bonus = 0
    character.ice_damage_bonus = 0
    character.nature_bonus = 0
    character.lightning_bonus = 0
    character.shadow_bonus = 0
    
    # Применяем индивидуальные бонусы
    for nft_id in nft_collection:
        if nft_id == "red":
            character.fire_damage_bonus = 5
        elif nft_id == "blue":
            character.defense_bonus = (character.defense_bonus or 0) + 5
        elif nft_id == "green":
            character.agility = (character.agility or 10) + 2
        elif nft_id == "yellow":
            character.magic_damage_bonus = 5
        elif nft_id == "purple":
            character.luck = (character.luck or 0) + 7
    
    # Применяем сетовые бонусы
    if collection_size >= 2:
        character.all_stats_bonus = 2
    if collection_size >= 3:
        character.all_stats_bonus = 3
        character.crit_chance = (character.crit_chance or 0) + 1
    if collection_size >= 4:
        character.all_stats_bonus = 4
        character.crit_chance = (character.crit_chance or 0) + 2
        character.max_health += 50
    if collection_size >= 5:
        character.all_stats_bonus = 5
        character.crit_chance = (character.crit_chance or 0) + 3
        character.max_health += 100
        character.max_mana += 50
        character.rainbow_nick = True
        character.rainbow_aura = True

# ========== АДМИН-ФУНКЦИИ (опционально) ==========

@router.post("/admin/reset")
def reset_nft_sales(admin_key: str):
    """Сбросить продажи NFT (только для разработки)"""
    # Простая защита
    if admin_key != "destiny_admin_2024":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    for color in NFT_SHARDS:
        NFT_SHARDS[color]["sold"] = 0
    
    return {"status": "reset", "message": "All NFT sales reset"}
