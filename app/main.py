from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from database import engine, Base
from routes import game, pvp, guild, premium, nft
from utils import get_all_data

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Destiny Game API",
    description="API для игры Destiny",
    version="2.0.0"
)

# Разрешаем запросы от Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты
app.include_router(game.router, prefix="/api", tags=["Game"])
app.include_router(pvp.router, prefix="/api/pvp", tags=["PvP"])
app.include_router(guild.router, prefix="/api/guild", tags=["Guild"])
app.include_router(premium.router, prefix="/api/premium", tags=["Premium"])
app.include_router(nft.router, prefix="/api/nft", tags=["NFT"])

@app.get("/")
def root():
    """Корневой эндпоинт"""
    return {
        "message": "Destiny API is working!",
        "status": "ok",
        "database": "connected",
        "version": "2.0"
    }

@app.get("/health")
def health():
    """Проверка здоровья"""
    return {"status": "healthy"}

@app.get("/api/data")
def get_data():
    """Получить все игровые данные"""
    return get_all_data()
