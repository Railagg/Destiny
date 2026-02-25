from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import json
from pathlib import Path

from app.database import engine, get_db, Base
from app import models

# ============================================
# ПЕРЕСОЗДАНИЕ ТАБЛИЦ (для пустой базы)
# ============================================
print("=" * 40)
print("🔄 ПРОВЕРКА БАЗЫ ДАННЫХ")
print("=" * 40)

try:
    # Удаляем старые таблицы
    print("🗑️ Удаляем старые таблицы...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Старые таблицы удалены")
    
    # Создаём новые таблицы
    print("🆕 Создаём новые таблицы...")
    Base.metadata.create_all(bind=engine)
    print("✅ Новые таблицы созданы успешно")
    print("=" * 40)
except Exception as e:
    print(f"❌ Ошибка при обновлении БД: {e}")
    print("=" * 40)

# ========== ИНИЦИАЛИЗАЦИЯ ==========
# Создаем таблицы в базе данных (на всякий случай, если код выше не сработал)
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

# ВРЕМЕННО: пропускаем проверку Telegram для теста
def verify_telegram_data(init_data: dict) -> bool:
    return True

# ========== ЗАГРУЗКА JSON ИЗ ПАПКИ DATA ==========
print("🚀 Загрузка JSON файлов...")

# Определяем корень проекта
BASE_DIR = Path(__file__).parent
print(f"📁 Корень проекта: {BASE_DIR}")

# JSON лежат в bot/data/
DATA_DIR = BASE_DIR / "bot" / "data"
print(f"📁 Путь к данным: {DATA_DIR}")

def load_json(filename, root_key=None):
    """
    Загружает JSON и возвращает данные.
    Если root_key указан и существует в файле, возвращает data[root_key].
    Иначе возвращает весь загруженный объект.
    """
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Если указан ключ и он есть в данных
        if root_key and root_key in data:
            print(f"✅ Загружен {filename} -> ключ '{root_key}' ({len(data[root_key])} элементов)")
            return data[root_key]
        
        print(f"✅ Загружен {filename} (без корневого ключа)")
        return data
    except FileNotFoundError:
        print(f"⚠️ Файл не найден: {filename}")
        return {}
    except Exception as e:
        print(f"❌ Ошибка загрузки {filename}: {e}")
        return {}

# Загружаем все JSON с указанием корневых ключей
print("\n📂 Загрузка игровых данных:")
locations_data = load_json("locations.json", "locations")
enemies_data = load_json("enemies.json", "enemies")
items_data = load_json("items.json", "items")
crafting_data = load_json("crafting.json", "crafting")
classes_data = load_json("classes.json", "classes")
quests_data = load_json("quests.json", "quests")
house_data = load_json("house.json", "house")
premium_data = load_json("premium.json", "premium")
nft_data = load_json("nft.json", "nft")
rainbow_data = load_json("rainbow.json", "rainbow")
events_data = load_json("events.json", "events")
codex_data = load_json("codex.json", "codex")
biomes_data = load_json("biomes.json", "biomes")
islands_data = load_json("islands.json", "islands")
secrets_data = load_json("secrets.json", "secrets")
pets_data = load_json("pets.json", "pets")
exchange_data = load_json("exchange.json", "exchange")

print("\n✅ Все JSON загружены")
print(f"📍 Локаций: {len(locations_data)}")
print(f"⚔️ Врагов: {len(enemies_data)}")
print(f"📦 Предметов: {len(items_data)}")
print("=" * 40)

# ========== РАЗДАЧА ФРОНТЕНДА ==========
frontend_path = BASE_DIR / "frontend"
print(f"📁 Путь к фронтенду: {frontend_path}")

if frontend_path.exists():
    # Монтируем папку frontend
    app.mount("/frontend", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    print(f"✅ Фронтенд загружен из {frontend_path}")
    
    # Корневой маршрут - отдаём index.html
    @app.get("/")
    async def root():
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        else:
            return {
                "message": "Destiny API is working!",
                "status": "ok",
                "database": "connected",
                "version": "2.0",
                "note": "index.html не найден в папке frontend"
            }
else:
    print(f"❌ Папка frontend НЕ найдена по пути: {frontend_path}")
    
    @app.get("/")
    def root():
        return {
            "message": "Destiny API is working!",
            "status": "ok",
            "database": "connected",
            "version": "2.0"
        }

# ========== API ЭНДПОИНТЫ ==========
@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/auth/telegram")
def auth_telegram(data: dict, db: Session = Depends(get_db)):
    """Авторизация через Telegram"""
    if not verify_telegram_data(data):
        raise HTTPException(status_code=401, detail="Invalid auth data")
    
    return {"status": "ok"}

@app.get("/api/data")
def get_data():
    """Получить все игровые данные (без двойной вложенности)"""
    return {
        "locations": locations_data,      # ← теперь это чистый объект локаций
        "enemies": enemies_data,          # ← чистый объект врагов
        "items": items_data,              # ← чистый объект предметов
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
        "islands": islands_data,
        "secrets": secrets_data,
        "pets": pets_data,
        "exchange": exchange_data
    }

@app.get("/api/data/{data_type}")
def get_data_by_type(data_type: str):
    """Получить данные конкретного типа"""
    data_map = {
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
        "islands": islands_data,
        "secrets": secrets_data,
        "pets": pets_data,
        "exchange": exchange_data
    }
    
    if data_type not in data_map:
        raise HTTPException(status_code=404, detail=f"Data type '{data_type}' not found")
    
    return data_map[data_type]

@app.get("/api/location/{location_id}")
def get_location(location_id: str):
    """Получить информацию о локации"""
    location = locations_data.get(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@app.get("/api/user/{telegram_id}")
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Получить данные пользователя"""
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    character = db.query(models.Character).filter(models.Character.user_id == user.id).first()
    
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "level": character.level if character else 1,
        "gold": character.gold if character else 0,
        "destiny_tokens": character.destiny_tokens if character else 0,
        "health": character.current_health if character else 100,
        "max_health": character.max_health if character else 100,
        "energy": character.energy if character else 100,
        "max_energy": character.max_energy if character else 100,
        "location": character.location if character else "start"
    }

# ========== ДОПОЛНИТЕЛЬНЫЙ РЕДИРЕКТ ==========
@app.get("/frontend")
async def frontend_root():
    index_path = frontend_path / "index.html"
    if frontend_path.exists() and index_path.exists():
        return FileResponse(index_path)
    return {"error": "Frontend not available"}

# Для отладки
@app.get("/debug/locations")
def debug_locations():
    """Отладка: показать структуру локаций"""
    return {
        "count": len(locations_data),
        "keys": list(locations_data.keys())[:10],
        "sample": locations_data.get("start", {})
    }
