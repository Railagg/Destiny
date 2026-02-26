from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routes import game, pvp, guild, premium, nft
import json
from pathlib import Path
import os

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

# Подключаем маршруты API
app.include_router(game.router, prefix="/api", tags=["Game"])
app.include_router(pvp.router, prefix="/api/pvp", tags=["PvP"])
app.include_router(guild.router, prefix="/api/guild", tags=["Guild"])
app.include_router(premium.router, prefix="/api/premium", tags=["Premium"])
app.include_router(nft.router, prefix="/api/nft", tags=["NFT"])

# ========== РАЗДАЧА ФРОНТЕНДА ==========

# Исправлено: fronted → frontend
frontend_path = Path(__file__).parent.parent / "frontend"

if frontend_path.exists():
    # Раздаем статические файлы
    app.mount("/frontend", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    print(f"✅ Фронтенд загружен из {frontend_path}")
    
    # Добавляем редирект с корня на фронтенд
    @app.get("/")
    async def root_with_frontend():
        from fastapi.responses import FileResponse
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {
            "message": "Destiny API is working!",
            "status": "ok",
            "database": "connected",
            "version": "2.0"
        }
else:
    print(f"❌ Папка frontend не найдена по пути: {frontend_path}")
    
    @app.get("/")
    def root():
        return {
            "message": "Destiny API is working!",
            "status": "ok",
            "database": "connected",
            "version": "2.0"
        }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/data")
def get_data():
    """Получить все игровые данные"""
    return {
        "locations": locations_data,
        "enemies": enemies_data,
        "items": items_data,
        "crafting": crafting_data,
        "classes": classes_data,
        "quests": quests_data,
        "house": house_data,
        "premium": premium_data,
        "nft": nft_data,
        "rainbow": rainbow_data,
        "events": events_data,
        "codex": codex_data,
        "biomes": biomes_data,
        "pets": pets_data,
        "secrets": secrets_data,
        "exchange": exchange_data
    }

# ========== ЗАГРУЗКА JSON ==========

print("🚀 Загрузка JSON файлов...")
DATA_DIR = Path(__file__).parent.parent / "data"

def load_json(filename):
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Загружен {filename}")
            return data
    except Exception as e:
        print(f"❌ Ошибка загрузки {filename}: {e}")
        return {}

# Загружаем все JSON
locations_data = load_json("locations.json")
enemies_data = load_json("enemies.json")
items_data = load_json("items.json")
crafting_data = load_json("crafting.json")
classes_data = load_json("classes.json")
quests_data = load_json("quests.json")
house_data = load_json("house.json")
premium_data = load_json("premium.json")
nft_data = load_json("nft.json")
rainbow_data = load_json("rainbow.json")
events_data = load_json("events.json")
codex_data = load_json("codex.json")
biomes_data = load_json("biomes.json")
pets_data = load_json("pets.json")
secrets_data = load_json("secrets.json")
exchange_data = load_json("exchange.json")

print("✅ Все JSON загружены")
