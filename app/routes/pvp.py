from fastapi import APIRouter, HTTPException
from typing import List, Optional
import random

router = APIRouter()

# Временное хранилище рейтинга (в реальности будет в БД)
pvp_ratings = {}

@router.get("/arena")
def get_arena_info():
    """Информация об арене"""
    return {
        "arenas": [
            {"name": "Тренировочная", "entry_fee": 0, "rating": False},
            {"name": "Рейтинговая", "entry_fee": 10, "rating": True},
            {"name": "Турнирная", "entry_fee": 100, "rating": True}
        ],
        "active_players": len(pvp_ratings)
    }

@router.get("/rating")
def get_rating(limit: int = 10):
    """Получить рейтинг игроков"""
    sorted_ratings = sorted(pvp_ratings.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"player_id": k, "rating": v} for k, v in sorted_ratings]

@router.post("/fight")
def start_fight(player1_id: int, player2_id: Optional[int] = None):
    """Начать PvP бой"""
    if player2_id:
        # PvP с конкретным игроком
        result = random.choice(["player1_win", "player2_win", "draw"])
    else:
        # Поиск случайного противника
        result = random.choice(["win", "lose", "draw"])
    
    return {
        "result": result,
        "rewards": {
            "exp": random.randint(10, 50),
            "gold": random.randint(5, 20),
            "rating_change": random.randint(-5, 15) if result != "draw" else 0
        }
    }
