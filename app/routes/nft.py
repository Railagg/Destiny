from fastapi import APIRouter, HTTPException
from typing import List, Optional

router = APIRouter()

# Данные NFT (из nft.json)
NFT_SHARDS = {
    "red": {
        "name": "🔴 Красный осколок силы",
        "total": 10,
        "price_stars": 100,
        "price_dstn": 5000,
        "bonuses": ["+5% урона", "+5% огненного урона", "+2 силы"],
        "ability": "Ярость (+25% урона на 1 минуту)"
    },
    "blue": {
        "name": "🔵 Синий осколок защиты",
        "total": 10,
        "price_stars": 100,
        "price_dstn": 5000,
        "bonuses": ["+5% защиты", "+5% магической защиты", "+50 HP"],
        "ability": "Щит (+50% защиты на 1 минуту)"
    },
    "green": {
        "name": "🟢 Зелёный осколок ловкости",
        "total": 10,
        "price_stars": 100,
        "price_dstn": 5000,
        "bonuses": ["+5% уклонения", "+5% скорости"],
        "ability": "Ветер (+50% скорости на 1 минуту)"
    },
    "yellow": {
        "name": "🟡 Жёлтый осколок магии",
        "total": 10,
        "price_stars": 100,
        "price_dstn": 5000,
        "bonuses": ["+5% магического урона", "+50 маны"],
        "ability": "Молния (300% маг. урона)"
    },
    "purple": {
        "name": "🟣 Фиолетовый осколок удачи",
        "total": 10,
        "price_stars": 200,
        "price_dstn": 10000,
        "bonuses": ["+7% удачи", "+5% редких находок"],
        "ability": "Удача (+50% удачи на 30 минут)"
    }
}

@router.get("/list")
def get_nft_list():
    """Список всех NFT"""
    return NFT_SHARDS

@router.get("/{color}")
def get_nft_info(color: str):
    """Информация о конкретном NFT"""
    if color not in NFT_SHARDS:
        raise HTTPException(status_code=404, detail="NFT not found")
    return NFT_SHARDS[color]

@router.post("/buy/{color}")
def buy_nft(color: str, player_id: int, payment_method: str):
    """Купить NFT"""
    if color not in NFT_SHARDS:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    nft = NFT_SHARDS[color]
    
    # Проверка остатков
    if nft.get("sold", 0) >= nft["total"]:
        raise HTTPException(status_code=400, detail="Sold out")
    
    # Здесь будет интеграция с платежами
    
    return {
        "status": "success",
        "nft": nft["name"],
        "price": nft["price_stars"] if payment_method == "stars" else nft["price_dstn"],
        "remaining": nft["total"] - nft.get("sold", 0) - 1
    }
