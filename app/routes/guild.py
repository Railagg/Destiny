from fastapi import APIRouter, HTTPException
from typing import Optional, List
import json

router = APIRouter()

# Временное хранилище гильдий (в реальности будет в БД)
guilds = {}

@router.get("/list")
def get_guilds():
    """Получить список всех гильдий"""
    return list(guilds.values())

@router.post("/create")
def create_guild(name: str, leader_id: int):
    """Создать гильдию"""
    if name in guilds:
        raise HTTPException(status_code=400, detail="Guild already exists")

    guilds[name] = {
        "name": name,
        "leader": leader_id,
        "members": [leader_id],
        "level": 1,
        "exp": 0,
        "created_at": "2024-01-01"
    }

    return {"status": "created", "guild": guilds[name]}

@router.get("/{name}")
def get_guild(name: str):
    """Информация о гильдии"""
    if name not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    return guilds[name]

@router.post("/{name}/join")
def join_guild(name: str, player_id: int):
    """Вступить в гильдию"""
    if name not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    if player_id in guilds[name]["members"]:
        raise HTTPException(status_code=400, detail="Already in guild")

    guilds[name]["members"].append(player_id)
    
    return {
        "status": "joined", 
        "guild": name,
        "members": len(guilds[name]["members"])
    }

@router.post("/{name}/leave")
def leave_guild(name: str, player_id: int):
    """Покинуть гильдию"""
    if name not in guilds:
        raise HTTPException(status_code=404, detail="Guild not found")

    if player_id not in guilds[name]["members"]:
        raise HTTPException(status_code=400, detail="Not in guild")

    guilds[name]["members"].remove(player_id)
    
    return {
        "status": "left", 
        "guild": name,
        "members": len(guilds[name]["members"])
    }
