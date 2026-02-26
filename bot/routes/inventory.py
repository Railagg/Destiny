from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
import json
import random
from datetime import datetime, timedelta

from database import get_db
from models import User, Character
from utils import (
    locations_data, items_data, enemies_data, 
    quests_data, codex_data, crafting_data,
    classes_data, house_data, premium_data,
    nft_data, rainbow_data, events_data,
    biomes_data, islands_data, secrets_data,
    pets_data, exchange_data
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
    
    # Добавляем информацию о монстрах
    if "enemies" in location:
        enemies = []
        for enemy_id in location["enemies"]:
            enemy = enemies_data.get("enemies", {}).get(enemy_id)
            if enemy:
                enemies.append({
                    "id": enemy_id,
                    "name": enemy.get("name"),
                    "level": enemy.get("level", 1),
                    "health": enemy.get("health", 50),
                    "damage": enemy.get("damage", 5),
                    "exp": enemy.get("exp", 50)
                })
        location["enemies_info"] = enemies
    
    return location

@router.get("/locations/all")
def get_all_locations():
    """Получить все локации"""
    all_locations = {}
    
    # Добавляем основные локации
    all_locations["locations"] = locations_data.get("locations", {})
    
    # Добавляем биомы
    all_locations["biomes"] = biomes_data.get("biomes", {})
    
    # Добавляем острова
    all_locations["islands"] = islands_data.get("islands", {})
    
    # Добавляем секретные локации
    all_locations["secrets"] = secrets_data.get("secrets", {})
    
    return all_locations

# ========== ПОЛЬЗОВАТЕЛИ ==========
@router.get("/user/{telegram_id}")
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Получить данные пользователя"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "auth_date": user.auth_date,
        "ton_wallet": user.ton_wallet,
        "premium_until": user.premium_until,
        "premium_plan": user.premium_plan,
        "titles": user.titles,
        "profile_frame": user.profile_frame,
        "profile_aura": user.profile_aura,
        "guild_id": user.guild_id,
        "character": {
            "name": character.name,
            "level": character.level,
            "experience": character.experience,
            "health": character.health,
            "max_health": character.max_health,
            "mana": character.mana,
            "max_mana": character.max_mana,
            "energy": character.energy,
            "max_energy": character.max_energy,
            "strength": character.strength,
            "agility": character.agility,
            "intelligence": character.intelligence,
            "vitality": character.vitality,
            "luck": character.luck,
            "gold": character.gold,
            "dstn": character.destiny_tokens,
            "player_class": character.player_class,
            "class_level": character.class_level,
            "location": character.location,
            "house_level": character.house_level,
            "rainbow_shards": character.rainbow_shards,
            "rainbow_stones": character.rainbow_stones,
            "kills_total": character.kills_total,
            "pvp_wins": character.pvp_wins,
            "items_crafted": character.items_crafted,
            "resources_gathered": character.resources_gathered
        }
    }

@router.post("/user/create")
def create_user(telegram_id: int, username: str = None, first_name: str = None, 
                last_name: str = None, db: Session = Depends(get_db)):
    """Создать нового пользователя"""
    # Проверяем, существует ли уже
    existing = db.query(User).filter(User.telegram_id == telegram_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Создаём пользователя
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    db.add(user)
    db.flush()
    
    # Создаём персонажа
    character = Character(
        user_id=user.id,
        name=first_name or f"Player_{telegram_id}",
        health=100,
        max_health=100,
        mana=50,
        max_mana=50,
        energy=100,
        max_energy=100,
        gold=20,  # стартовое золото
        destiny_tokens=0,
        inventory=[]
    )
    db.add(character)
    db.commit()
    
    return {"status": "success", "user_id": user.id}

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
    
    inventory = character.inventory or []
    items = []
    item_counts = {}
    
    # Группируем по ID и считаем количество
    for item_id in inventory:
        item_counts[item_id] = item_counts.get(item_id, 0) + 1
    
    # Получаем информацию о каждом предмете
    for item_id, count in item_counts.items():
        item = items_data.get("items", {}).get(item_id)
        if item:
            items.append({
                "id": item_id,
                "name": item.get("name"),
                "icon": item.get("icon", "📦"),
                "rarity": item.get("rarity", "common"),
                "type": item.get("type", "unknown"),
                "description": item.get("description", ""),
                "stats": {k: v for k, v in item.items() if k in ["damage", "defense", "heal", "mana", "durability"]},
                "value": item.get("value", 0),
                "count": count,
                "equipped": item_id == character.equipped_weapon or item_id == character.equipped_armor
            })
    
    # Добавляем экипировку отдельно
    equipped = {
        "weapon": character.equipped_weapon,
        "armor": character.equipped_armor,
        "accessory": character.equipped_accessory
    }
    
    return {
        "items": items,
        "count": len(inventory),
        "max_size": 100 + (character.inventory_slots_bonus or 0),
        "equipped": equipped
    }

@router.post("/inventory/add")
def add_item(telegram_id: int, item_id: str, count: int = 1, db: Session = Depends(get_db)):
    """Добавить предмет в инвентарь"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    inventory = character.inventory or []
    for _ in range(count):
        inventory.append(item_id)
    
    character.inventory = inventory
    db.commit()
    
    return {"status": "success", "new_count": len(inventory)}

@router.post("/inventory/remove")
def remove_item(telegram_id: int, item_id: str, count: int = 1, db: Session = Depends(get_db)):
    """Удалить предмет из инвентаря"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    inventory = character.inventory or []
    removed = 0
    new_inventory = []
    
    for item in inventory:
        if item == item_id and removed < count:
            removed += 1
        else:
            new_inventory.append(item)
    
    character.inventory = new_inventory
    db.commit()
    
    return {"status": "success", "removed": removed}

@router.post("/inventory/equip")
def equip_item(telegram_id: int, item_id: str, slot: str = "weapon", db: Session = Depends(get_db)):
    """Надеть предмет"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Проверяем, есть ли предмет
    inventory = character.inventory or []
    if item_id not in inventory:
        raise HTTPException(status_code=400, detail="Item not in inventory")
    
    # Проверяем тип предмета
    item = items_data.get("items", {}).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item_type = item.get("type")
    if slot == "weapon" and item_type != "weapon":
        raise HTTPException(status_code=400, detail="Item is not a weapon")
    if slot == "armor" and item_type != "armor":
        raise HTTPException(status_code=400, detail="Item is not armor")
    
    # Снимаем предыдущий предмет
    if slot == "weapon" and character.equipped_weapon:
        old_weapon = character.equipped_weapon
        # Ничего не делаем, просто заменяем
    elif slot == "armor" and character.equipped_armor:
        old_armor = character.equipped_armor
    
    # Надеваем новый
    if slot == "weapon":
        character.equipped_weapon = item_id
    elif slot == "armor":
        character.equipped_armor = item_id
    
    db.commit()
    
    return {"status": "success", "equipped": item_id}

# ========== ЭНЦИКЛОПЕДИЯ ==========
@router.get("/codex/{section}")
def get_codex(section: str, category: Optional[str] = None):
    """Получить раздел энциклопедии"""
    sections = {
        "bestiary": "bestiary",
        "items": "items",
        "locations": "locations",
        "achievements": "achievements",
        "crafting": "crafting",
        "classes": "classes",
        "pets": "pets",
        "rainbow": "rainbow",
        "guilds": "guilds"
    }
    
    if section not in sections:
        raise HTTPException(status_code=404, detail="Section not found")
    
    codex_section = codex_data.get("codex", {}).get(sections[section], {})
    
    # Если указана категория, возвращаем только её
    if category and "categories" in codex_section:
        return codex_section["categories"].get(category, {})
    
    return codex_section

@router.get("/codex/search")
def search_codex(query: str, limit: int = 10):
    """Поиск по энциклопедии"""
    results = []
    
    # Поиск в бестиарии
    bestiary = codex_data.get("codex", {}).get("bestiary", {})
    for cat in bestiary.get("categories", {}).values():
        for creature in cat.get("creatures", []):
            if query.lower() in creature.get("name", "").lower():
                results.append({
                    "type": "creature",
                    "name": creature["name"],
                    "category": cat["name"],
                    "data": creature
                })
    
    # Поиск в предметах
    items_section = codex_data.get("codex", {}).get("items", {})
    for cat in items_section.get("categories", {}).values():
        for item in cat.get("items", []):
            if query.lower() in item.get("name", "").lower():
                results.append({
                    "type": "item",
                    "name": item["name"],
                    "category": cat["name"],
                    "data": item
                })
    
    return {"results": results[:limit]}

# ========== КРАФТ ==========
@router.get("/craft/{item_id}")
def get_craft_recipe(item_id: str):
    """Получить рецепт крафта предмета"""
    recipes = crafting_data.get("crafting", {})
    
    # Ищем во всех категориях
    for category, cat_data in recipes.items():
        if isinstance(cat_data, dict):
            for subcat, items in cat_data.items():
                if item_id in items:
                    return {
                        "category": category,
                        "subcategory": subcat,
                        "recipe": items[item_id]
                    }
    
    raise HTTPException(status_code=404, detail="Recipe not found")

@router.get("/craft/category/{category}")
def get_category_recipes(category: str):
    """Получить все рецепты категории"""
    recipes = crafting_data.get("crafting", {}).get(category, {})
    if not recipes:
        raise HTTPException(status_code=404, detail="Category not found")
    return recipes

# ========== ДОМИК ==========
@router.get("/house/{telegram_id}")
def get_house_info(telegram_id: int, db: Session = Depends(get_db)):
    """Получить информацию о домике игрока"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    house_level = character.house_level or 0
    house_data_level = house_data.get("house", {}).get("levels", {}).get(str(house_level), {})
    
    return {
        "level": house_level,
        "features": house_data_level,
        "furniture": character.house_furniture,
        "pets": character.house_pets,
        "garden": character.house_garden,
        "buildings": character.house_buildings,
        "can_upgrade": house_level < 5
    }

@router.post("/house/upgrade")
def upgrade_house(telegram_id: int, db: Session = Depends(get_db)):
    """Улучшить домик"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    current_level = character.house_level or 0
    if current_level >= 5:
        raise HTTPException(status_code=400, detail="Maximum level reached")
    
    next_level = str(current_level + 1)
    level_data = house_data.get("house", {}).get("levels", {}).get(next_level, {})
    
    # Проверяем ресурсы
    cost = level_data.get("build_cost", {})
    inventory = character.inventory or []
    
    missing = []
    for material, amount in cost.items():
        if inventory.count(material) < amount:
            missing.append(f"{material}: {amount}")
    
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing resources: {', '.join(missing)}")
    
    # Тратим ресурсы
    for material, amount in cost.items():
        for _ in range(amount):
            inventory.remove(material)
    
    character.inventory = inventory
    character.house_level = current_level + 1
    db.commit()
    
    return {"status": "success", "new_level": character.house_level}

# ========== ИВЕНТЫ ==========
@router.get("/events/today")
def get_today_event():
    """Получить ивент на сегодня"""
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    today = days[datetime.today().weekday()]
    
    weekly = events_data.get("events", {}).get("weekly", {})
    event = weekly.get(today, {})
    
    if event:
        return {
            "day": today,
            "name": event.get("name"),
            "description": event.get("description"),
            "bonuses": event.get("bonuses", {}),
            "quest": event.get("quest"),
            "competition": event.get("competition")
        }
    
    return {"message": "No event today"}

@router.get("/events/active")
def get_active_events():
    """Получить все активные ивенты"""
    active = []
    
    # Проверяем сезонные
    seasonal = events_data.get("events", {}).get("seasonal", {})
    current_month = datetime.now().strftime("%B").lower()
    
    for event_id, event in seasonal.items():
        season = event.get("season", "").lower()
        if season == get_current_season(current_month):
            active.append({
                "id": event_id,
                "name": event.get("name"),
                "type": "seasonal",
                "duration": event.get("duration", 7),
                "bonuses": event.get("bonuses", {})
            })
    
    # Проверяем ежемесячные
    monthly = events_data.get("events", {}).get("monthly", {})
    for event_id, event in monthly.items():
        if event.get("frequency") == "monthly":
            active.append({
                "id": event_id,
                "name": event.get("name"),
                "type": "monthly",
                "bonuses": event.get("bonuses", {})
            })
    
    return {"active": active}

def get_current_season(month):
    spring = ["march", "april", "may"]
    summer = ["june", "july", "august"]
    autumn = ["september", "october", "november"]
    winter = ["december", "january", "february"]
    
    if month in spring:
        return "spring"
    elif month in summer:
        return "summer"
    elif month in autumn:
        return "autumn"
    else:
        return "winter"

# ========== РЕЙТИНГИ ==========
@router.get("/top/{category}")
def get_top(category: str, limit: int = 10, db: Session = Depends(get_db)):
    """Получить топ игроков по категории"""
    if category == "level":
        characters = db.query(Character).order_by(Character.level.desc()).limit(limit).all()
        result = []
        for c in characters:
            user = db.query(User).filter(User.id == c.user_id).first()
            result.append({
                "user_id": c.user_id,
                "username": user.username if user else f"Player_{c.user_id}",
                "level": c.level,
                "experience": c.experience
            })
        return result
    
    elif category == "gold":
        characters = db.query(Character).order_by(Character.gold.desc()).limit(limit).all()
        result = []
        for c in characters:
            user = db.query(User).filter(User.id == c.user_id).first()
            result.append({
                "user_id": c.user_id,
                "username": user.username if user else f"Player_{c.user_id}",
                "gold": c.gold,
                "level": c.level
            })
        return result
    
    elif category == "pvp":
        characters = db.query(Character).order_by(Character.pvp_wins.desc()).limit(limit).all()
        result = []
        for c in characters:
            user = db.query(User).filter(User.id == c.user_id).first()
            result.append({
                "user_id": c.user_id,
                "username": user.username if user else f"Player_{c.user_id}",
                "pvp_wins": c.pvp_wins,
                "level": c.level
            })
        return result
    
    elif category == "kills":
        characters = db.query(Character).order_by(Character.kills_total.desc()).limit(limit).all()
        result = []
        for c in characters:
            user = db.query(User).filter(User.id == c.user_id).first()
            result.append({
                "user_id": c.user_id,
                "username": user.username if user else f"Player_{c.user_id}",
                "kills": c.kills_total,
                "level": c.level
            })
        return result
    
    else:
        raise HTTPException(status_code=400, detail="Invalid category")

# ========== ПИТОМЦЫ ==========
@router.get("/pets/{telegram_id}")
def get_pets(telegram_id: int, db: Session = Depends(get_db)):
    """Получить питомцев игрока"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    pets = character.pets or []
    active_pet = character.active_pet
    
    # Обогащаем данными из pets.json
    enriched_pets = []
    for pet in pets:
        pet_id = pet.get("id")
        pet_data = pets_data.get("pets", {}).get(pet_id, {})
        enriched_pets.append({
            **pet,
            "name": pet_data.get("name", pet_id),
            "rarity": pet_data.get("rarity", "common"),
            "bonus": pet_data.get("bonus", {}),
            "image": pet_data.get("image")
        })
    
    return {
        "pets": enriched_pets,
        "active": active_pet,
        "house_level": character.pet_house_level
    }

# ========== РАДУЖНЫЕ РЕСУРСЫ ==========
@router.get("/rainbow/{telegram_id}")
def get_rainbow_resources(telegram_id: int, db: Session = Depends(get_db)):
    """Получить радужные ресурсы игрока"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return {
        "shards": character.rainbow_shards,
        "stones": character.rainbow_stones,
        "craft_end": character.rainbow_craft_end,
        "history": character.rainbow_history[-10:] if character.rainbow_history else []
    }

@router.post("/rainbow/craft")
def craft_rainbow_stone(telegram_id: int, db: Session = Depends(get_db)):
    """Начать крафт радужного камня"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Проверка
    if character.house_level < 5:
        raise HTTPException(status_code=400, detail="Need house level 5")
    
    if character.rainbow_shards < 9:
        raise HTTPException(status_code=400, detail="Need 9 rainbow shards")
    
    now = int(datetime.now().timestamp())
    if character.rainbow_craft_end and character.rainbow_craft_end > now:
        remaining = character.rainbow_craft_end - now
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        raise HTTPException(status_code=400, detail=f"Already crafting! Time left: {hours}h {minutes}m")
    
    # Тратим осколки
    character.rainbow_shards -= 9
    character.rainbow_craft_end = now + 86400  # 24 часа
    
    # История
    if not character.rainbow_history:
        character.rainbow_history = []
    character.rainbow_history.append({
        "date": datetime.now().isoformat(),
        "action": "start_craft",
        "amount": 9
    })
    
    db.commit()
    
    return {"status": "success", "craft_end": character.rainbow_craft_end}
