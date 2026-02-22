from fastapi import APIRouter

router = APIRouter()

# Данные из nft.json (5 видов, по 10 шт каждого)
NFT_SHARDS = {
    "red": {
        "name": "🔴 Красный осколок силы",
        "total_supply": 10,
        "price_stars": 100,
        "price_dstn": 5000,
        "bonuses": ["+5% урона", "+5% огненного урона", "+2 силы"],
        "ability": {
            "name": "Ярость",
            "effect": "+25% урона на 1 минуту",
            "cooldown": "1 день"
        }
    },
    "blue": {
        "name": "🔵 Синий осколок защиты",
        "total_supply": 10,
        "price_stars": 100,
        "price_dstn": 5000,
        "bonuses": ["+5% защиты", "+5% магической защиты", "+50 HP"],
        "ability": {
            "name": "Щит",
            "effect": "+50% защиты на 1 минуту",
            "cooldown": "1 день"
        }
    },
    "green": {
        "name": "🟢 Зелёный осколок ловкости",
        "total_supply": 10,
        "price_stars": 100,
        "price_dstn": 5000,
        "bonuses": ["+5% уклонения", "+5% скорости"],
        "ability": {
            "name": "Ветер",
            "effect": "+50% скорости на 1 минуту",
            "cooldown": "1 день"
        }
    },
    "yellow": {
        "name": "🟡 Жёлтый осколок магии",
        "total_supply": 10,
        "price_stars": 100,
        "price_dstn": 5000,
        "bonuses": ["+5% магического урона", "+50 маны"],
        "ability": {
            "name": "Молния",
            "effect": "300% магического урона по 5 целям",
            "cooldown": "1 день"
        }
    },
    "purple": {
        "name": "🟣 Фиолетовый осколок удачи",
        "total_supply": 10,
        "price_stars": 200,
        "price_dstn": 10000,
        "bonuses": ["+7% удачи", "+5% редких находок"],
        "ability": {
            "name": "Удача",
            "effect": "+50% удачи на 30 минут",
            "cooldown": "1 день"
        }
    }
}

@router.get("/list")
def get_nft_list():
    """Получить список всех NFT"""
    return NFT_SHARDS

@router.get("/{color}")
def get_nft_info(color: str):
    """Получить информацию о конкретном NFT"""
    if color not in NFT_SHARDS:
        return {"error": "NFT not found"}
    return NFT_SHARDS[color]

@router.get("/collection/set_bonuses")
def get_set_bonuses():
    """Получить бонусы за коллекцию NFT"""
    return {
        "2_pieces": {"name": "Коллекционер", "bonus": "+2% ко всем характеристикам"},
        "3_pieces": {"name": "Хранитель стихий", "bonus": "+3% ко всем характеристикам"},
        "4_pieces": {"name": "Повелитель стихий", "bonus": "+4% ко всем характеристикам"},
        "5_pieces": {"name": "Бог стихий", "bonus": "+5% ко всем характеристикам, радужный ник"}
    }
