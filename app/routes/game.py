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
    location = locations_data.get("locations", {}).get(location_id)
    
    if not location:
        for biome in biomes_data.get("biomes", {}).values():
            if biome.get("id") == location_id:
                return biome
    
    if not location:
        for island in islands_data.get("islands", {}).values():
            if island.get("id") == location_id:
                return island
    
    if not location:
        for secret in secrets_data.get("secrets", {}).values():
            if secret.get("id") == location_id:
                return secret
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
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
    return {
        "locations": locations_data.get("locations", {}),
        "biomes": biomes_data.get("biomes", {}),
        "islands": islands_data.get("islands", {}),
        "secrets": secrets_data.get("secrets", {})
    }

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
        "login_streak": user.login_streak,
        "max_streak": user.max_streak,
        "premium_from_streak": user.premium_from_streak,
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
            "stars": character.stars,
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
    existing = db.query(User).filter(User.telegram_id == telegram_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    db.add(user)
    db.flush()
    
    character = Character(
        user_id=user.id,
        name=first_name or f"Player_{telegram_id}",
        health=100,
        max_health=100,
        mana=50,
        max_mana=50,
        energy=100,
        max_energy=100,
        gold=20,
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
    
    for item_id in inventory:
        item_counts[item_id] = item_counts.get(item_id, 0) + 1
    
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
    
    inventory = character.inventory or []
    if item_id not in inventory:
        raise HTTPException(status_code=400, detail="Item not in inventory")
    
    item = items_data.get("items", {}).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item_type = item.get("type")
    if slot == "weapon" and item_type != "weapon":
        raise HTTPException(status_code=400, detail="Item is not a weapon")
    if slot == "armor" and item_type != "armor":
        raise HTTPException(status_code=400, detail="Item is not armor")
    
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
    
    if category and "categories" in codex_section:
        return codex_section["categories"].get(category, {})
    
    return codex_section

@router.get("/codex/search")
def search_codex(query: str, limit: int = 10):
    """Поиск по энциклопедии"""
    results = []
    
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
    
    cost = level_data.get("build_cost", {})
    inventory = character.inventory or []
    
    missing = []
    for material, amount in cost.items():
        if inventory.count(material) < amount:
            missing.append(f"{material}: {amount}")
    
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing resources: {', '.join(missing)}")
    
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
    
    elif category == "streak":
        users = db.query(User).order_by(User.login_streak.desc()).limit(limit).all()
        result = []
        for u in users:
            character = db.query(Character).filter(Character.user_id == u.id).first()
            result.append({
                "user_id": u.telegram_id,
                "username": u.username,
                "streak": u.login_streak,
                "max_streak": u.max_streak,
                "level": character.level if character else 1
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
    
    pets_list = character.pets or []
    pets_data_dict = pets_data.get("pets", {})
    
    result = []
    for pet_id in pets_list:
        pet_info = pets_data_dict.get(pet_id)
        if pet_info:
            result.append({
                "id": pet_id,
                "name": pet_info.get("name"),
                "type": pet_info.get("type"),
                "rarity": pet_info.get("rarity"),
                "level": pet_info.get("level", 1),
                "abilities": pet_info.get("abilities", []),
                "stats": pet_info.get("stats", {}),
                "evolution": pet_info.get("evolution")
            })
    
    return {
        "pets": result,
        "count": len(result),
        "max_pets": 5 + (character.house_level or 0),
        "active_pet": character.active_pet
    }

@router.post("/pets/equip")
def equip_pet(telegram_id: int, pet_id: str, db: Session = Depends(get_db)):
    """Экипировать питомца"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    pets_list = character.pets or []
    if pet_id not in pets_list:
        raise HTTPException(status_code=400, detail="Pet not owned")
    
    character.active_pet = pet_id
    db.commit()
    
    return {"status": "success", "active_pet": pet_id}

@router.post("/pets/feed")
def feed_pet(telegram_id: int, pet_id: str, food_item: str, db: Session = Depends(get_db)):
    """Покормить питомца"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    pets_list = character.pets or []
    if pet_id not in pets_list:
        raise HTTPException(status_code=400, detail="Pet not owned")
    
    inventory = character.inventory or []
    if food_item not in inventory:
        raise HTTPException(status_code=400, detail="Food item not in inventory")
    
    # Удаляем еду из инвентаря
    inventory.remove(food_item)
    character.inventory = inventory
    
    # Обновляем сытость питомца
    if not character.pet_happiness:
        character.pet_happiness = {}
    
    character.pet_happiness[pet_id] = min(100, (character.pet_happiness.get(pet_id, 50) + 20))
    
    db.commit()
    
    return {
        "status": "success",
        "happiness": character.pet_happiness.get(pet_id, 70)
    }

# ========== ЭКСПЕДИЦИИ ==========
@router.get("/expeditions")
def get_expeditions():
    """Получить список экспедиций"""
    expeditions_data = events_data.get("expeditions", {})
    return expeditions_data

@router.post("/expedition/start/{expedition_id}")
def start_expedition(telegram_id: int, expedition_id: str, db: Session = Depends(get_db)):
    """Начать экспедицию"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    expeditions = events_data.get("expeditions", {}).get("available", {})
    expedition = expeditions.get(expedition_id)
    
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    if character.energy < expedition.get("energy_cost", 20):
        raise HTTPException(status_code=400, detail="Not enough energy")
    
    duration = expedition.get("duration_hours", 1)
    finish_time = datetime.utcnow() + timedelta(hours=duration)
    
    character.energy -= expedition.get("energy_cost", 20)
    character.current_expedition = expedition_id
    character.expedition_finish = finish_time
    
    db.commit()
    
    return {
        "status": "started",
        "expedition": expedition_id,
        "finish_time": finish_time.isoformat()
    }

@router.get("/expedition/status/{telegram_id}")
def get_expedition_status(telegram_id: int, db: Session = Depends(get_db)):
    """Получить статус текущей экспедиции"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    if not character.current_expedition or not character.expedition_finish:
        return {"status": "no_active_expedition"}
    
    now = datetime.utcnow()
    time_left = (character.expedition_finish - now).total_seconds()
    
    if time_left <= 0:
        # Экспедиция завершена
        return {
            "status": "completed",
            "expedition_id": character.current_expedition,
            "can_claim": True
        }
    
    return {
        "status": "in_progress",
        "expedition_id": character.current_expedition,
        "time_left_seconds": int(time_left),
        "finish_time": character.expedition_finish.isoformat()
    }

@router.post("/expedition/claim/{telegram_id}")
def claim_expedition_rewards(telegram_id: int, db: Session = Depends(get_db)):
    """Забрать награды за экспедицию"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    if not character.current_expedition or not character.expedition_finish:
        raise HTTPException(status_code=400, detail="No active expedition")
    
    now = datetime.utcnow()
    if now < character.expedition_finish:
        time_left = (character.expedition_finish - now).total_seconds()
        raise HTTPException(status_code=400, detail=f"Expedition not finished yet. {int(time_left)} seconds left")
    
    expeditions = events_data.get("expeditions", {}).get("available", {})
    expedition = expeditions.get(character.current_expedition, {})
    
    # Начисляем награды
    rewards = expedition.get("rewards", {})
    
    # Золото
    character.gold += rewards.get("gold", 0)
    
    # Опыт
    experience_gain = rewards.get("experience", 0)
    character.experience += experience_gain
    
    # Предметы
    items = rewards.get("items", [])
    inventory = character.inventory or []
    for item in items:
        for _ in range(item.get("count", 1)):
            inventory.append(item.get("id"))
    character.inventory = inventory
    
    # Сбрасываем экспедицию
    character.current_expedition = None
    character.expedition_finish = None
    
    # Проверка на повышение уровня
    level_up = False
    new_level = character.level
    
    # Простая формула: 1000 * уровень ^ 1.5
    exp_needed = int(1000 * (character.level ** 1.5))
    while character.experience >= exp_needed and character.level < 100:
        character.experience -= exp_needed
        character.level += 1
        level_up = True
        # Увеличиваем характеристики при повышении уровня
        character.max_health += 10
        character.health = character.max_health
        character.max_mana += 5
        character.mana = character.max_mana
        exp_needed = int(1000 * (character.level ** 1.5))
    
    db.commit()
    
    return {
        "status": "success",
        "rewards": rewards,
        "level_up": level_up,
        "new_level": character.level if level_up else None,
        "experience": character.experience,
        "gold": character.gold
    }

# ========== ГИЛЬДИИ ==========
@router.get("/guild/{guild_id}")
def get_guild(guild_id: int, db: Session = Depends(get_db)):
    """Получить информацию о гильдии"""
    from models import Guild
    
    guild = db.query(Guild).filter(Guild.id == guild_id).first()
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    members = db.query(User).filter(User.guild_id == guild_id).all()
    member_list = []
    for m in members:
        character = db.query(Character).filter(Character.user_id == m.id).first()
        member_list.append({
            "telegram_id": m.telegram_id,
            "username": m.username,
            "level": character.level if character else 1,
            "guild_role": m.guild_role
        })
    
    return {
        "id": guild.id,
        "name": guild.name,
        "tag": guild.tag,
        "level": guild.level,
        "experience": guild.experience,
        "members_count": len(member_list),
        "max_members": guild.max_members,
        "members": member_list,
        "description": guild.description,
        "emblem": guild.emblem
    }

# ========== NFT ==========
@router.get("/nft/list")
def get_nft_list():
    """Получить список NFT предметов"""
    return nft_data.get("nft", {})

@router.get("/nft/owned/{telegram_id}")
def get_owned_nft(telegram_id: int, db: Session = Depends(get_db)):
    """Получить NFT предметы игрока"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    nft_items = user.nft_items or []
    nft_data_dict = nft_data.get("nft", {}).get("items", {})
    
    result = []
    for nft_id in nft_items:
        nft_info = nft_data_dict.get(nft_id)
        if nft_info:
            result.append({
                "id": nft_id,
                "name": nft_info.get("name"),
                "type": nft_info.get("type"),
                "rarity": nft_info.get("rarity"),
                "stats": nft_info.get("stats", {}),
                "image_url": nft_info.get("image_url"),
                "token_id": nft_info.get("token_id")
            })
    
    return {"nft_items": result}

# ========== ТОРГОВЛЯ ==========
@router.get("/exchange/rates")
def get_exchange_rates():
    """Получить курсы обмена валют"""
    rates = exchange_data.get("exchange", {}).get("rates", {})
    return rates

@router.post("/exchange/convert")
def convert_currency(telegram_id: int, from_currency: str, to_currency: str, 
                     amount: float, db: Session = Depends(get_db)):
    """Обменять валюту"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    rates = exchange_data.get("exchange", {}).get("rates", {})
    pair = f"{from_currency}/{to_currency}"
    fee = exchange_data.get("exchange", {}).get("fee_percent", 1)
    
    if pair not in rates:
        raise HTTPException(status_code=400, detail="Exchange pair not available")
    
    rate = rates[pair]
    
    if from_currency == "gold":
        if character.gold < amount:
            raise HTTPException(status_code=400, detail="Insufficient gold")
        character.gold -= amount
    elif from_currency == "dstn":
        if character.destiny_tokens < amount:
            raise HTTPException(status_code=400, detail="Insufficient DSTN")
        character.destiny_tokens -= amount
    elif from_currency == "stars":
        if character.stars < amount:
            raise HTTPException(status_code=400, detail="Insufficient stars")
        character.stars -= amount
    else:
        raise HTTPException(status_code=400, detail="Invalid currency")
    
    received = amount * rate * (1 - fee / 100)
    
    if to_currency == "gold":
        character.gold += received
    elif to_currency == "dstn":
        character.destiny_tokens += received
    elif to_currency == "stars":
        character.stars += received
    
    # Запись транзакции
    if not character.exchange_history:
        character.exchange_history = []
    
    transaction = {
        "timestamp": datetime.utcnow().isoformat(),
        "from": from_currency,
        "to": to_currency,
        "amount": amount,
        "received": received,
        "rate": rate,
        "fee": fee
    }
    
    character.exchange_history.append(transaction)
    db.commit()
    
    return {
        "status": "success",
        "received": received,
        "rate": rate,
        "fee_percent": fee
    }

# ========== КВЕСТЫ ==========
@router.get("/quests/daily/{telegram_id}")
def get_daily_quests(telegram_id: int, db: Session = Depends(get_db)):
    """Получить ежедневные квесты"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    today = datetime.now().date()
    daily_quests = quests_data.get("quests", {}).get("daily", {})
    
    # Сброс квестов, если новый день
    if user.last_daily_reset != today:
        # Выбираем 3 случайных квеста
        all_quest_ids = list(daily_quests.keys())
        user.daily_quests = random.sample(all_quest_ids, min(3, len(all_quest_ids)))
        user.daily_quests_progress = {}
        user.last_daily_reset = today
        db.commit()
    
    result = []
    for quest_id in (user.daily_quests or []):
        quest = daily_quests.get(quest_id)
        if quest:
            progress = (user.daily_quests_progress or {}).get(quest_id, 0)
            completed = progress >= quest.get("requirement", 1)
            
            result.append({
                "id": quest_id,
                "name": quest.get("name"),
                "description": quest.get("description"),
                "requirement": quest.get("requirement"),
                "rewards": quest.get("rewards"),
                "progress": progress,
                "completed": completed,
                "expires": today.isoformat()
            })
    
    return {"quests": result}

@router.post("/quests/claim/{quest_id}")
def claim_quest_reward(telegram_id: int, quest_id: str, db: Session = Depends(get_db)):
    """Забрать награду за квест"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    today = datetime.now().date()
    
    # Проверяем, есть ли квест у пользователя
    if quest_id not in (user.daily_quests or []):
        raise HTTPException(status_code=400, detail="Quest not assigned")
    
    # Получаем информацию о квесте
    daily_quests = quests_data.get("quests", {}).get("daily", {})
    quest = daily_quests.get(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    # Проверяем прогресс
    progress = (user.daily_quests_progress or {}).get(quest_id, 0)
    if progress < quest.get("requirement", 1):
        raise HTTPException(status_code=400, detail="Quest not completed")
    
    # Проверяем, не забрали ли уже награду
    if user.claimed_daily_quests and quest_id in user.claimed_daily_quests:
        raise HTTPException(status_code=400, detail="Reward already claimed")
    
    # Начисляем награды
    rewards = quest.get("rewards", {})
    
    # Золото
    character.gold += rewards.get("gold", 0)
    
    # Опыт
    experience_gain = rewards.get("experience", 0)
    character.experience += experience_gain
    
    # DSTN токены
    character.destiny_tokens += rewards.get("dstn", 0)
    
    # Предметы
    items = rewards.get("items", [])
    inventory = character.inventory or []
    for item in items:
        for _ in range(item.get("count", 1)):
            inventory.append(item.get("id"))
    character.inventory = inventory
    
    # Отмечаем квест как выполненный
    if not user.claimed_daily_quests:
        user.claimed_daily_quests = []
    user.claimed_daily_quests.append(quest_id)
    
    # Проверка на повышение уровня
    level_up = False
    new_level = character.level
    
    exp_needed = int(1000 * (character.level ** 1.5))
    while character.experience >= exp_needed and character.level < 100:
        character.experience -= exp_needed
        character.level += 1
        level_up = True
        character.max_health += 10
        character.health = character.max_health
        character.max_mana += 5
        character.mana = character.max_mana
        exp_needed = int(1000 * (character.level ** 1.5))
    
    db.commit()
    
    return {
        "status": "success",
        "rewards": rewards,
        "level_up": level_up,
        "new_level": character.level if level_up else None
    }

# ========== БОЙ ==========
@router.post("/battle/start")
def start_battle(telegram_id: int, enemy_id: str, db: Session = Depends(get_db)):
    """Начать бой с врагом"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Получаем информацию о враге
    enemy = enemies_data.get("enemies", {}).get(enemy_id)
    if not enemy:
        raise HTTPException(status_code=404, detail="Enemy not found")
    
    # Проверяем энергию
    if character.energy < 10:
        raise HTTPException(status_code=400, detail="Not enough energy")
    
    character.energy -= 10
    
    # Симулируем бой (упрощенно)
    player_power = (
        character.strength * 2 +
        character.agility * 1.5 +
        character.intelligence * 1.5 +
        character.level * 5
    )
    
    # Добавляем силу оружия, если экипировано
    if character.equipped_weapon:
        weapon = items_data.get("items", {}).get(character.equipped_weapon, {})
        player_power += weapon.get("damage", 0) * 2
    
    enemy_power = (
        enemy.get("damage", 5) * 3 +
        enemy.get("health", 50) * 0.5 +
        enemy.get("level", 1) * 5
    )
    
    # Шанс победы
    win_chance = player_power / (player_power + enemy_power)
    
    # Определяем исход
    if random.random() < win_chance:
        # Победа
        experience_gain = enemy.get("exp", 50)
        gold_gain = enemy.get("gold", random.randint(5, 20))
        
        character.experience += experience_gain
        character.gold += gold_gain
        character.kills_total += 1
        
        # Шанс на выпадение предмета
        drops = enemy.get("drops", [])
        inventory = character.inventory or []
        
        items_dropped = []
        for drop in drops:
            if random.random() < drop.get("chance", 0.1):
                item_id = drop.get("item")
                inventory.append(item_id)
                items_dropped.append(item_id)
        
        character.inventory = inventory
        
        # Проверка на повышение уровня
        level_up = False
        exp_needed = int(1000 * (character.level ** 1.5))
        while character.experience >= exp_needed and character.level < 100:
            character.experience -= exp_needed
            character.level += 1
            level_up = True
            character.max_health += 10
            character.health = character.max_health
            character.max_mana += 5
            character.mana = character.max_mana
            exp_needed = int(1000 * (character.level ** 1.5))
        
        db.commit()
        
        return {
            "result": "victory",
            "experience_gained": experience_gain,
            "gold_gained": gold_gain,
            "items_dropped": items_dropped,
            "level_up": level_up,
            "new_level": character.level if level_up else None
        }
    else:
        # Поражение
        damage_taken = enemy.get("damage", 5) * random.randint(1, 3)
        character.health = max(0, character.health - damage_taken)
        
        db.commit()
        
        return {
            "result": "defeat",
            "damage_taken": damage_taken,
            "health_left": character.health
        }

# ========== АЧИВКИ ==========
@router.get("/achievements/{telegram_id}")
def get_achievements(telegram_id: int, db: Session = Depends(get_db)):
    """Получить достижения игрока"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    achievements_data = codex_data.get("codex", {}).get("achievements", {})
    user_achievements = user.achievements or []
    
    result = []
    for ach_id, ach_info in achievements_data.items():
        result.append({
            "id": ach_id,
            "name": ach_info.get("name"),
            "description": ach_info.get("description"),
            "reward": ach_info.get("reward"),
            "unlocked": ach_id in user_achievements,
            "hidden": ach_info.get("hidden", False)
        })
    
    return {"achievements": result}

# ========== КЛАССЫ ==========
@router.get("/classes")
def get_classes():
    """Получить информацию о всех классах"""
    return classes_data.get("classes", {})

@router.get("/class/{class_name}")
def get_class_info(class_name: str):
    """Получить информацию о конкретном классе"""
    classes = classes_data.get("classes", {})
    class_info = classes.get(class_name)
    
    if not class_info:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return class_info

@router.post("/class/select")
def select_class(telegram_id: int, class_name: str, db: Session = Depends(get_db)):
    """Выбрать класс для персонажа"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    if character.player_class:
        raise HTTPException(status_code=400, detail="Class already selected")
    
    classes = classes_data.get("classes", {})
    class_info = classes.get(class_name)
    
    if not class_info:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Устанавливаем класс
    character.player_class = class_name
    character.class_level = 1
    
    # Даем стартовые бонусы
    character.strength += class_info.get("base_stats", {}).get("strength", 0)
    character.agility += class_info.get("base_stats", {}).get("agility", 0)
    character.intelligence += class_info.get("base_stats", {}).get("intelligence", 0)
    character.vitality += class_info.get("base_stats", {}).get("vitality", 0)
    character.luck += class_info.get("base_stats", {}).get("luck", 0)
    
    db.commit()
    
    return {"status": "success", "class": class_name}

# ========== РАДУЖНЫЙ РЕЖИМ ==========
@router.get("/rainbow/status/{telegram_id}")
def get_rainbow_status(telegram_id: int, db: Session = Depends(get_db)):
    """Получить статус радужного режима"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    rainbow_info = rainbow_data.get("rainbow", {})
    
    return {
        "active": character.rainbow_mode_active or False,
        "shards": character.rainbow_shards or 0,
        "stones": character.rainbow_stones or 0,
        "current_color": character.rainbow_color,
        "progress": character.rainbow_progress or 0,
        "rewards": rainbow_info.get("rewards", {}),
        "bonuses": rainbow_info.get("bonuses", {})
    }

@router.post("/rainbow/activate")
def activate_rainbow_mode(telegram_id: int, db: Session = Depends(get_db)):
    """Активировать радужный режим"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    if character.rainbow_mode_active:
        raise HTTPException(status_code=400, detail="Rainbow mode already active")
    
    if (character.rainbow_shards or 0) < 100:
        raise HTTPException(status_code=400, detail="Not enough rainbow shards")
    
    character.rainbow_shards -= 100
    character.rainbow_mode_active = True
    character.rainbow_progress = 0
    character.rainbow_color = random.choice(["red", "orange", "yellow", "green", "blue", "indigo", "violet"])
    
    db.commit()
    
    return {
        "status": "activated",
        "color": character.rainbow_color,
        "bonus": rainbow_data.get("rainbow", {}).get("bonuses", {}).get(character.rainbow_color, {})
    }

# ========== ПРЕМИУМ ==========
@router.get("/premium/info")
def get_premium_info():
    """Получить информацию о премиум-подписке"""
    return premium_data.get("premium", {})

@router.post("/premium/buy")
def buy_premium(telegram_id: int, plan: str, db: Session = Depends(get_db)):
    """Купить премиум-подписку"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    premium_plans = premium_data.get("premium", {}).get("plans", {})
    plan_info = premium_plans.get(plan)
    
    if not plan_info:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    cost = plan_info.get("cost_dstn", 0)
    if character.destiny_tokens < cost:
        raise HTTPException(status_code=400, detail="Insufficient DSTN")
    
    character.destiny_tokens -= cost
    
    duration_days = plan_info.get("duration_days", 30)
    user.premium_until = datetime.utcnow() + timedelta(days=duration_days)
    user.premium_plan = plan
    
    db.commit()
    
    return {
        "status": "success",
        "premium_until": user.premium_until,
        "plan": plan
    }
