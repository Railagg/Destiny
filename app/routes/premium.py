from fastapi import APIRouter

router = APIRouter()

@router.get("/plans")
def get_premium_plans():
    """Получить список премиум тарифов"""
    return {
        "7days": {
            "name": "🟢 Стартовый",
            "price_stars": 50,
            "price_ton": 1,
            "duration": 7,
            "bonuses": {
                "max_energy": 150,
                "gold_multiplier": 1.1,
                "dstn_multiplier": 1.05,
                "chests_per_day": 1
            }
        },
        "28days": {
            "name": "🔵 Базовый",
            "price_stars": 150,
            "price_ton": 3,
            "duration": 28,
            "bonuses": {
                "max_energy": 175,
                "gold_multiplier": 1.15,
                "dstn_multiplier": 1.1,
                "chests_per_day": 2
            }
        },
        "90days": {
            "name": "🟣 Продвинутый",
            "price_stars": 400,
            "price_ton": 8,
            "duration": 90,
            "bonuses": {
                "max_energy": 200,
                "gold_multiplier": 1.2,
                "dstn_multiplier": 1.15,
                "chests_per_day": 3
            }
        },
        "180days": {
            "name": "🟡 Элитный",
            "price_stars": 700,
            "price_ton": 14,
            "duration": 180,
            "bonuses": {
                "max_energy": 225,
                "gold_multiplier": 1.25,
                "dstn_multiplier": 1.2,
                "chests_per_day": 4,
                "rainbow_shard_weekly": 1
            }
        },
        "365days": {
            "name": "🔴 Легендарный",
            "price_stars": 1200,
            "price_ton": 24,
            "duration": 365,
            "bonuses": {
                "max_energy": 250,
                "gold_multiplier": 1.3,
                "dstn_multiplier": 1.25,
                "chests_per_day": 5,
                "rainbow_shard_weekly": 1,
                "rainbow_stone_yearly": 1
            }
        }
    }
