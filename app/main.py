from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base, check_connection, init_db
from routes import game, pvp, guild, premium, nft, daily
import json
from pathlib import Path
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Проверяем подключение к БД
if check_connection():
    logger.info("✅ База данных подключена")
else:
    logger.error("❌ Ошибка подключения к БД")
    init_db()

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
app.include_router(daily.router, prefix="/api/daily", tags=["Daily"])

# ========== РАЗДАЧА ФРОНТЕНДА ==========

frontend_path = Path(__file__).parent.parent / "frontend"
static_path = Path(__file__).parent.parent / "static"

# Создаём папки если их нет
frontend_path.mkdir(exist_ok=True)
static_path.mkdir(exist_ok=True)

# Раздаём статику
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    logger.info(f"✅ Фронтенд загружен из {frontend_path}")
    
    @app.get("/")
    async def root():
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
    logger.error(f"❌ Папка frontend не найдена по пути: {frontend_path}")
    
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

logger.info("🚀 Загрузка JSON файлов...")
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

def load_json(filename):
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"✅ Загружен {filename}")
            return data
    except FileNotFoundError:
        logger.warning(f"⚠️ Файл не найден: {filename}")
        return {}
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки {filename}: {e}")
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

logger.info("✅ Все JSON загружены")
