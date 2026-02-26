from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import time
from datetime import datetime, timedelta

from database import get_db
from models import User, Character

router = APIRouter()

# Временное хранилище гильдий (в реальности будет в БД)
guilds = {}

# Константы для гильдий
GUILD_LEVELS = {
    1: {"max_members": 10, "exp_needed": 1000, "bonuses": {"exp": 2, "gold": 0, "luck": 0, "defense": 0, "damage": 0}},
    2: {"max_members": 20, "exp_needed": 5000, "bonuses": {"exp": 4, "gold": 2, "luck": 0, "defense": 0, "damage": 0}},
    3: {"max_members": 30, "exp_needed": 15000, "bonuses": {"exp": 6, "gold": 4, "luck": 2, "defense": 0, "damage": 0}},
    4: {"max_members": 40, "exp_needed": 30000, "bonuses": {"exp": 8, "gold": 6, "luck": 4, "defense": 2, "damage": 0}},
    5: {"max_members": 50, "exp_needed": 50000, "bonuses": {"exp": 10, "gold": 8, "luck": 6, "defense": 4, "damage": 2}}
}

GUILD_BUILDINGS = {
    "hall": {
        "name": "🏛️ Зал гильдии",
        "price": 0,
        "price_dstn": 0,
        "description": "Общий чат и банк гильдии",
        "required_level": 1,
        "bonus": None
    },
    "shop": {
        "name": "🏪 Гильдейский магазин",
        "price": 50000,
        "price_dstn": 500,
        "description": "Уникальные предметы для членов гильдии",
        "required_level": 2,
        "bonus": "Скидка 5% в магазине"
    },
    "arena": {
        "name": "⚔️ Гильдейская арена",
        "price": 100000,
        "price_dstn": 1000,
        "description": "Тренировки и турниры между своими",
        "required_level": 3,
        "bonus": "+5% к урону в PvP"
    },
    "altar": {
        "name": "🔮 Алтарь гильдии",
        "price": 200000,
        "price_dstn": 2000,
        "description": "Общие баффы и усиления",
        "required_level": 4,
        "bonus": "Ежедневное благословение"
    },
    "bank": {
        "name": "🏦 Гильдейский банк",
        "price": 150000,
        "price_dstn": 1500,
        "description": "Хранилище ресурсов и процентов",
        "required_level": 3,
        "bonus": "+1% к проценту в день"
    },
    "laboratory": {
        "name": "⚗️ Гильдейская лаборатория",
        "price": 250000,
        "price_dstn": 2500,
        "description": "Исследования и крафт",
        "required_level": 4,
        "bonus": "+10% к крафту"
    },
    "tower": {
        "name": "🗼 Гильдейская башня",
        "price": 500000,
        "price_dstn": 5000,
        "description": "Слежение за врагами и разведка",
        "required_level": 5,
        "bonus": "Видит врагов на карте"
    }
}

GUILD_RANKS = {
    "leader": {"name": "👑 Лидер", "level": 5},
    "officer": {"name": "⚔️ Офицер", "level": 4},
    "veteran": {"name": "🛡️ Ветеран", "level": 3},
    "member": {"name": "🔰 Рядовой", "level": 2},
    "recruit": {"name": "🌱 Рекрут", "level": 1}
}

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========

@router.get("/list")
def get_guilds(page: int = 1, limit: int = 10):
    """Получить список всех гильдий с пагинацией"""
    start = (page - 1) * limit
    end = start + limit
    
    guild_list = list(guilds.values())
    
    # Сортировка по уровню и опыту
    guild_list.sort(key=lambda x: (x["level"], x["exp"]), reverse=True)
    
    return {
        "total": len(guild_list),
        "page": page,
        "limit": limit,
        "guilds": guild_list[start:end]
    }

@router.get("/ranking")
def get_guild_ranking():
    """Получить рейтинг гильдий"""
    guild_list = list(guilds.values())
    
    # По опыту
    by_exp = sorted(guild_list, key=lambda x: x["exp"], reverse=True)[:10]
    
    # По победам в войнах
    by_wins = sorted(guild_list, key=lambda x: x.get("wins", 0), reverse=True)[:10]
    
    # По количеству членов
    by_members = sorted(guild_list, key=lambda x: len(x["members"]), reverse=True)[:10]
    
    return {
        "by_exp": [{"name": g["name"], "exp": g["exp"], "level": g["level"]} for g in by_exp],
        "by_wins": [{"name": g["name"], "wins": g.get("wins", 0)} for g in by_wins],
        "by_members": [{"name": g["name"], "members": len(g["members"])} for g in by_members]
    }

@router.post("/create")
def create_guild(
    name: str, 
    leader_id: int, 
    description: str = "", 
    tag: str = "⚔️",
    db: Session = Depends(get_db)
):
    """Создать гильдию"""
    # Проверка существования
    for g in guilds.values():
        if g["name"].lower() == name.lower():
            raise HTTPException(status_code=400, detail="Guild already exists")
    
    # Проверяем игрока
    user = db.query(User).filter(User.telegram_id == leader_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Проверяем, не в гильдии ли уже
    if character.user.guild_id:
        raise HTTPException(status_code=400, detail="Already in a guild")
    
    # Проверяем ресурсы
    if character.gold < 5000 and character.destiny_tokens < 500:
        raise HTTPException(
            status_code=400, 
            detail="Need 5000 gold or 500 DSTN to create guild"
        )
    
    # Тратим ресурсы (DSTN в приоритете)
    if character.destiny_tokens >= 500:
        character.destiny_tokens -= 500
    else:
        character.gold -= 5000
    
    # Создаём гильдию
    guild_id = str(int(time.time()))  # временный ID
    guilds[guild_id] = {
        "id": guild_id,
        "name": name,
        "tag": tag,
        "description": description,
        "leader": leader_id,
        "leader_name": user.first_name or f"Player_{leader_id}",
        "members": [leader_id],
        "officers": [],
        "veterans": [],
        "applications": [],
        "level": 1,
        "exp": 0,
        "gold": 0,
        "dstn": 0,
        "buildings": ["hall"],
        "wins": 0,
        "losses": 0,
        "war_rating": 1000,
        "announcement": "",
        "created_at": datetime.now().isoformat(),
        "last_war": None
    }
    
    # Обновляем игрока
    character.user.guild_id = guild_id
    character.guild_join_time = int(time.time())
    character.guild_rank = "leader"
    db.commit()
    
    return {
        "status": "created", 
        "guild": guilds[guild_id]
    }

@router.get("/{guild_id}")
def get_guild(guild_id: str):
    """Информация о гильдии"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id].copy()
    
    # Добавляем информацию об уровне
    level_info = GUILD_LEVELS[guild["level"]]
    guild["max_members"] = level_info["max_members"]
    guild["exp_needed"] = level_info["exp_needed"]
    guild["bonuses"] = level_info["bonuses"]
    
    # Добавляем информацию о зданиях
    guild["buildings_info"] = []
    for building_id in guild["buildings"]:
        if building_id in GUILD_BUILDINGS:
            guild["buildings_info"].append(GUILD_BUILDINGS[building_id])
    
    return guild

@router.get("/{guild_id}/members")
def get_guild_members(guild_id: str, db: Session = Depends(get_db)):
    """Получить список участников гильдии с деталями"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    members = []
    
    for member_id in guild["members"]:
        user = db.query(User).filter(User.telegram_id == member_id).first()
        if user:
            character = db.query(Character).filter(Character.user_id == user.id).first()
            
            # Определяем ранг
            if member_id == guild["leader"]:
                rank = "leader"
            elif member_id in guild.get("officers", []):
                rank = "officer"
            elif member_id in guild.get("veterans", []):
                rank = "veteran"
            else:
                rank = "member"
            
            members.append({
                "id": member_id,
                "username": user.username,
                "first_name": user.first_name,
                "level": character.level if character else 1,
                "class": character.player_class if character else None,
                "rank": rank,
                "rank_name": GUILD_RANKS[rank]["name"],
                "contribution": getattr(character, 'guild_contribution', 0),
                "join_time": getattr(character, 'guild_join_time', 0)
            })
    
    # Сортируем по рангу и вкладу
    rank_order = {"leader": 0, "officer": 1, "veteran": 2, "member": 3}
    members.sort(key=lambda x: (rank_order[x["rank"]], -x["contribution"]))
    
    return {
        "guild": guild["name"],
        "total": len(members),
        "members": members
    }

# ========== УПРАВЛЕНИЕ УЧАСТНИКАМИ ==========

@router.post("/{guild_id}/join")
def join_guild(guild_id: str, player_id: int, db: Session = Depends(get_db)):
    """Вступить в гильдию"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    level_info = GUILD_LEVELS[guild["level"]]
    
    # Проверка на максимум
    if len(guild["members"]) >= level_info["max_members"]:
        raise HTTPException(status_code=400, detail="Guild is full")
    
    if player_id in guild["members"]:
        raise HTTPException(status_code=400, detail="Already in guild")
    
    # Проверяем игрока
    user = db.query(User).filter(User.telegram_id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.guild_id:
        raise HTTPException(status_code=400, detail="Already in a guild")
    
    # Добавляем в гильдию
    guild["members"].append(player_id)
    user.guild_id = guild_id
    user.guild_join_time = int(time.time())
    user.guild_rank = "member"
    db.commit()
    
    return {
        "status": "joined", 
        "guild": guild["name"],
        "members": len(guild["members"])
    }

@router.post("/{guild_id}/apply")
def apply_to_guild(guild_id: str, player_id: int):
    """Подать заявку на вступление"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if player_id in guild["members"]:
        raise HTTPException(status_code=400, detail="Already in guild")
    
    if player_id in guild.get("applications", []):
        raise HTTPException(status_code=400, detail="Already applied")
    
    guild.setdefault("applications", []).append(player_id)
    
    return {
        "status": "applied",
        "guild": guild["name"]
    }

@router.post("/{guild_id}/accept")
def accept_application(guild_id: str, leader_id: int, applicant_id: int):
    """Принять заявку"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if leader_id != guild["leader"] and leader_id not in guild.get("officers", []):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if applicant_id not in guild.get("applications", []):
        raise HTTPException(status_code=400, detail="Application not found")
    
    level_info = GUILD_LEVELS[guild["level"]]
    if len(guild["members"]) >= level_info["max_members"]:
        raise HTTPException(status_code=400, detail="Guild is full")
    
    guild["applications"].remove(applicant_id)
    guild["members"].append(applicant_id)
    
    return {
        "status": "accepted",
        "member": applicant_id
    }

@router.post("/{guild_id}/reject")
def reject_application(guild_id: str, leader_id: int, applicant_id: int):
    """Отклонить заявку"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if leader_id != guild["leader"] and leader_id not in guild.get("officers", []):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if applicant_id not in guild.get("applications", []):
        raise HTTPException(status_code=400, detail="Application not found")
    
    guild["applications"].remove(applicant_id)
    
    return {
        "status": "rejected",
        "applicant": applicant_id
    }

@router.post("/{guild_id}/leave")
def leave_guild(guild_id: str, player_id: int, db: Session = Depends(get_db)):
    """Покинуть гильдию"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if player_id not in guild["members"]:
        raise HTTPException(status_code=400, detail="Not in guild")
    
    if player_id == guild["leader"]:
        raise HTTPException(status_code=400, detail="Leader cannot leave. Transfer leadership first.")
    
    guild["members"].remove(player_id)
    
    # Убираем из офицеров/ветеранов если были
    if player_id in guild.get("officers", []):
        guild["officers"].remove(player_id)
    if player_id in guild.get("veterans", []):
        guild["veterans"].remove(player_id)
    
    # Обновляем игрока
    user = db.query(User).filter(User.telegram_id == player_id).first()
    if user:
        user.guild_id = None
        user.guild_leave_time = int(time.time())
        db.commit()
    
    return {
        "status": "left", 
        "guild": guild["name"],
        "members": len(guild["members"])
    }

@router.post("/{guild_id}/kick")
def kick_member(guild_id: str, leader_id: int, member_id: int, db: Session = Depends(get_db)):
    """Исключить участника"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if leader_id != guild["leader"] and leader_id not in guild.get("officers", []):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if member_id == guild["leader"]:
        raise HTTPException(status_code=400, detail="Cannot kick leader")
    
    if member_id not in guild["members"]:
        raise HTTPException(status_code=400, detail="Member not found")
    
    guild["members"].remove(member_id)
    
    # Убираем из офицеров/ветеранов если были
    if member_id in guild.get("officers", []):
        guild["officers"].remove(member_id)
    if member_id in guild.get("veterans", []):
        guild["veterans"].remove(member_id)
    
    # Обновляем игрока
    user = db.query(User).filter(User.telegram_id == member_id).first()
    if user:
        user.guild_id = None
        user.guild_leave_time = int(time.time())
        db.commit()
    
    return {
        "status": "kicked",
        "member": member_id
    }

@router.post("/{guild_id}/promote")
def promote_member(guild_id: str, leader_id: int, member_id: int, rank: str):
    """Повысить участника"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if leader_id != guild["leader"]:
        raise HTTPException(status_code=403, detail="Only leader can promote")
    
    if member_id not in guild["members"]:
        raise HTTPException(status_code=400, detail="Member not found")
    
    if rank not in ["officer", "veteran"]:
        raise HTTPException(status_code=400, detail="Invalid rank")
    
    # Убираем из других рангов
    if member_id in guild.get("officers", []):
        guild["officers"].remove(member_id)
    if member_id in guild.get("veterans", []):
        guild["veterans"].remove(member_id)
    
    # Добавляем в новый ранг
    if rank == "officer":
        guild.setdefault("officers", []).append(member_id)
    elif rank == "veteran":
        guild.setdefault("veterans", []).append(member_id)
    
    return {
        "status": "promoted",
        "member": member_id,
        "new_rank": rank
    }

@router.post("/{guild_id}/demote")
def demote_member(guild_id: str, leader_id: int, member_id: int):
    """Понизить участника"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if leader_id != guild["leader"]:
        raise HTTPException(status_code=403, detail="Only leader can demote")
    
    if member_id not in guild["members"]:
        raise HTTPException(status_code=400, detail="Member not found")
    
    # Убираем из рангов
    if member_id in guild.get("officers", []):
        guild["officers"].remove(member_id)
    if member_id in guild.get("veterans", []):
        guild["veterans"].remove(member_id)
    
    return {
        "status": "demoted",
        "member": member_id,
        "new_rank": "member"
    }

@router.post("/{guild_id}/transfer")
def transfer_leadership(guild_id: str, leader_id: int, new_leader_id: int):
    """Передать лидерство"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if leader_id != guild["leader"]:
        raise HTTPException(status_code=403, detail="Only leader can transfer leadership")
    
    if new_leader_id not in guild["members"]:
        raise HTTPException(status_code=400, detail="New leader not in guild")
    
    # Старый лидер становится офицером
    guild["officers"].append(leader_id)
    
    # Новый лидер
    guild["leader"] = new_leader_id
    if new_leader_id in guild["officers"]:
        guild["officers"].remove(new_leader_id)
    if new_leader_id in guild["veterans"]:
        guild["veterans"].remove(new_leader_id)
    
    return {
        "status": "transferred",
        "new_leader": new_leader_id
    }

# ========== УПРАВЛЕНИЕ ГИЛЬДИЕЙ ==========

@router.post("/{guild_id}/announcement")
def set_announcement(guild_id: str, leader_id: int, announcement: str):
    """Установить объявление гильдии"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if leader_id != guild["leader"] and leader_id not in guild.get("officers", []):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    guild["announcement"] = announcement
    
    return {
        "status": "updated",
        "announcement": announcement
    }

@router.post("/{guild_id}/donate")
def donate_to_guild(
    guild_id: str, 
    player_id: int, 
    amount: int, 
    currency: str = "gold",
    db: Session = Depends(get_db)
):
    """Пожертвовать ресурсы гильдии"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if player_id not in guild["members"]:
        raise HTTPException(status_code=400, detail="Not in guild")
    
    # Проверяем игрока
    user = db.query(User).filter(User.telegram_id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Проверяем ресурсы
    if currency == "gold":
        if character.gold < amount:
            raise HTTPException(status_code=400, detail="Not enough gold")
        character.gold -= amount
        guild["gold"] = guild.get("gold", 0) + amount
        exp_gain = amount // 100
    elif currency == "dstn":
        if character.destiny_tokens < amount:
            raise HTTPException(status_code=400, detail="Not enough DSTN")
        character.destiny_tokens -= amount
        guild["dstn"] = guild.get("dstn", 0) + amount
        exp_gain = amount * 2
    else:
        raise HTTPException(status_code=400, detail="Invalid currency")
    
    # Добавляем опыт гильдии
    guild["exp"] = guild.get("exp", 0) + exp_gain
    
    # Обновляем вклад игрока
    if not hasattr(character, 'guild_contribution'):
        character.guild_contribution = 0
    character.guild_contribution += exp_gain
    
    if currency == "gold":
        character.guild_donated_gold = getattr(character, 'guild_donated_gold', 0) + amount
    else:
        character.guild_donated_dstn = getattr(character, 'guild_donated_dstn', 0) + amount
    
    # Проверка на повышение уровня
    level_up_guild(guild)
    
    db.commit()
    
    return {
        "status": "donated",
        "amount": amount,
        "currency": currency,
        "exp_gained": exp_gain,
        "guild_exp": guild["exp"],
        "guild_level": guild["level"]
    }

def level_up_guild(guild):
    """Повысить уровень гильдии"""
    current_level = guild["level"]
    exp = guild["exp"]
    
    while current_level < 5 and exp >= GUILD_LEVELS[current_level]["exp_needed"]:
        exp -= GUILD_LEVELS[current_level]["exp_needed"]
        current_level += 1
    
    guild["level"] = current_level
    guild["exp"] = exp

@router.post("/{guild_id}/build")
def build_building(
    guild_id: str, 
    leader_id: int, 
    building_id: str
):
    """Построить здание в гильдии"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if leader_id != guild["leader"]:
        raise HTTPException(status_code=403, detail="Only leader can build")
    
    if building_id not in GUILD_BUILDINGS:
        raise HTTPException(status_code=400, detail="Invalid building")
    
    building = GUILD_BUILDINGS[building_id]
    
    if guild["level"] < building["required_level"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Need guild level {building['required_level']}"
        )
    
    if building_id in guild.get("buildings", []):
        raise HTTPException(status_code=400, detail="Building already exists")
    
    # Проверяем ресурсы
    if guild.get("gold", 0) < building["price"]:
        raise HTTPException(status_code=400, detail="Not enough gold")
    
    if building.get("price_dstn", 0) > 0 and guild.get("dstn", 0) < building["price_dstn"]:
        raise HTTPException(status_code=400, detail="Not enough DSTN")
    
    # Тратим ресурсы
    guild["gold"] -= building["price"]
    if building.get("price_dstn", 0) > 0:
        guild["dstn"] -= building["price_dstn"]
    
    # Строим
    guild.setdefault("buildings", []).append(building_id)
    
    return {
        "status": "built",
        "building": building["name"],
        "guild_gold": guild["gold"],
        "guild_dstn": guild["dstn"]
    }

# ========== ГИЛЬДЕЙСКИЕ ВОЙНЫ ==========

@router.get("/wars/status")
def get_war_status():
    """Получить статус гильдейских войн"""
    next_saturday = get_next_saturday()
    now = datetime.now()
    days_left = (next_saturday - now).days
    hours_left = ((next_saturday - now).seconds // 3600)
    
    return {
        "next_war": next_saturday.isoformat(),
        "days_left": days_left,
        "hours_left": hours_left,
        "registered_guilds": len([g for g in guilds.values() if g.get("registered_for_war")]),
        "total_guilds": len(guilds)
    }

@router.post("/{guild_id}/war/register")
def register_for_war(guild_id: str, leader_id: int):
    """Зарегистрировать гильдию на войну"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if leader_id != guild["leader"]:
        raise HTTPException(status_code=403, detail="Only leader can register")
    
    if guild["level"] < 2:
        raise HTTPException(status_code=400, detail="Need guild level 2")
    
    if len(guild["members"]) < 5:
        raise HTTPException(status_code=400, detail="Need at least 5 members")
    
    guild["registered_for_war"] = True
    
    return {
        "status": "registered",
        "guild": guild["name"]
    }

def get_next_saturday():
    today = datetime.now()
    days_ahead = 5 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)

# ========== ГИЛЬДЕЙСКИЙ МАГАЗИН ==========

@router.get("/{guild_id}/shop")
def get_guild_shop(guild_id: str):
    """Получить товары гильдейского магазина"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if "shop" not in guild.get("buildings", []):
        raise HTTPException(status_code=400, detail="Guild shop not built")
    
    # Товары гильдейского магазина
    items = [
        {
            "id": "teleport_scroll_5",
            "name": "📜 Свиток телепортации (5 шт)",
            "price_gold": 5000,
            "price_dstn": 50,
            "description": "5 свитков телепортации"
        },
        {
            "id": "magic_crystal_3",
            "name": "🔮 Магический кристалл (3 шт)",
            "price_gold": 10000,
            "price_dstn": 100,
            "description": "3 магических кристалла"
        },
        {
            "id": "dragon_scale",
            "name": "🐉 Чешуя дракона",
            "price_gold": 25000,
            "price_dstn": 250,
            "description": "Редкий материал для крафта"
        },
        {
            "id": "phoenix_feather",
            "name": "🔥 Перо феникса",
            "price_gold": 50000,
            "price_dstn": 500,
            "description": "Легендарный материал"
        },
        {
            "id": "rainbow_shard",
            "name": "🌈 Радужный осколок",
            "price_gold": 100000,
            "price_dstn": 1000,
            "description": "Редкий ресурс для крафта"
        },
        {
            "id": "guild_cloak",
            "name": "👑 Гильдейский плащ",
            "price_gold": 200000,
            "price_dstn": 2000,
            "description": "Особый предмет гильдии",
            "special": True
        }
    ]
    
    return {
        "guild": guild["name"],
        "items": items,
        "discount": 5 if guild["level"] >= 3 else 0
    }

@router.post("/{guild_id}/shop/buy")
def buy_from_guild_shop(
    guild_id: str,
    player_id: int,
    item_id: str,
    currency: str = "gold",
    db: Session = Depends(get_db)
):
    """Купить предмет из гильдейского магазина"""
    if guild_id not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    guild = guilds[guild_id]
    
    if player_id not in guild["members"]:
        raise HTTPException(status_code=400, detail="Not in guild")
    
    if "shop" not in guild.get("buildings", []):
        raise HTTPException(status_code=400, detail="Guild shop not built")
    
    # Товары (упрощённо)
    items = {
        "teleport_scroll_5": {"name": "📜 Свиток телепортации (5 шт)", "price_gold": 5000, "price_dstn": 50},
        "magic_crystal_3": {"name": "🔮 Магический кристалл (3 шт)", "price_gold": 10000, "price_dstn": 100},
        "dragon_scale": {"name": "🐉 Чешуя дракона", "price_gold": 25000, "price_dstn": 250},
        "phoenix_feather": {"name": "🔥 Перо феникса", "price_gold": 50000, "price_dstn": 500},
        "rainbow_shard": {"name": "🌈 Радужный осколок", "price_gold": 100000, "price_dstn": 1000},
        "guild_cloak": {"name": "👑 Гильдейский плащ", "price_gold": 200000, "price_dstn": 2000}
    }
    
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = items[item_id]
    
    # Проверяем игрока
    user = db.query(User).filter(User.telegram_id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(Character).filter(Character.user_id == user.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Применяем скидку
    discount = 5 if guild["level"] >= 3 else 0
    
    if currency == "gold":
        price = item["price_gold"] * (100 - discount) // 100
        if character.gold < price:
            raise HTTPException(status_code=400, detail="Not enough gold")
        character.gold -= price
    elif currency == "dstn":
        price = item["price_dstn"] * (100 - discount) // 100
        if character.destiny_tokens < price:
            raise HTTPException(status_code=400, detail="Not enough DSTN")
        character.destiny_tokens -= price
    else:
        raise HTTPException(status_code=400, detail="Invalid currency")
    
    # Добавляем предмет (упрощённо)
    inventory = character.inventory or []
    base_item = item_id.replace("_5", "").replace("_3", "")
    for _ in range(5 if "_5" in item_id else 3 if "_3" in item_id else 1):
        inventory.append(base_item)
    character.inventory = inventory
    
    db.commit()
    
    return {
        "status": "bought",
        "item": item["name"],
        "price": price,
        "currency": currency,
        "discount": discount
    }
