from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

# Тарифы премиума
PREMIUM_PLANS = {
    "7days": {"price": 50, "duration": 7, "name": "🟢 Стартовый"},
    "28days": {"price": 150, "duration": 28, "name": "🔵 Базовый"},
    "90days": {"price": 400, "duration": 90, "name": "🟣 Продвинутый"},
    "180days": {"price": 700, "duration": 180, "name": "🟡 Элитный"},
    "365days": {"price": 1200, "duration": 365, "name": "🔴 Легендарный"}
}

@router.get("/plans")
def get_premium_plans():
    """Список премиум тарифов"""
    return PREMIUM_PLANS

@router.post("/buy")
def buy_premium(player_id: int, plan: str, payment_method: str):
    """Купить премиум"""
    if plan not in PREMIUM_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan_data = PREMIUM_PLANS[plan]
    
    # Здесь будет интеграция с Telegram Stars / TON
    
    return {
        "status": "success",
        "plan": plan_data["name"],
        "expires": (datetime.now() + timedelta(days=plan_data["duration"])).isoformat(),
        "bonuses": {
            "max_energy": 150 if plan == "7days" else 250,
            "gold_multiplier": 1.1 if plan == "7days" else 1.3
        }
    }

@router.get("/status/{player_id}")
def get_premium_status(player_id: int):
    """Статус премиума"""
    # В реальности проверять в БД
    return {
        "active": False,
        "plan": None,
        "days_left": 0
    }
