import telebot
import json
import os
import sys
import logging
import requests
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
from datetime import datetime

# ============================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    stream=sys.stdout,
    force=True
)

sys.stdout.reconfigure(line_buffering=True)

logging.info("🚀 Запуск бота Destiny...")

# ============================================
# ТОКЕН БОТА
# ============================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("❌ НЕТ ТОКЕНА")
    exit(1)

logging.info(f"✅ Токен получен: {BOT_TOKEN[:10]}...")

# ============================================
# ОТКЛЮЧЕНИЕ ВЕБХУКА
# ============================================
try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    logging.info("✅ Webhook отключён")
except:
    logging.warning("⚠️ Не удалось отключить вебхук")

# ============================================
# ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# ============================================
from database import engine, Base, SessionLocal
from models import User, Character

# Создаем таблицы
try:
    Base.metadata.create_all(bind=engine)
    logging.info("✅ Таблицы БД созданы/проверены")
except Exception as e:
    logging.error(f"❌ Ошибка создания таблиц: {e}")

# ============================================
# СОЗДАНИЕ БОТА
# ============================================
bot = telebot.TeleBot(BOT_TOKEN)

try:
    me = bot.get_me()
    logging.info(f"✅ Бот авторизован: @{me.username}")
except Exception as e:
    logging.error(f"❌ Ошибка авторизации: {e}")
    exit(1)

# ============================================
# ПУТЬ К JSON
# ============================================

current_dir = Path(__file__).parent          # /bot
data_dir = current_dir / "data"               # /bot/data

logging.info(f"📁 Текущая папка бота: {current_dir}")
logging.info(f"📁 Папка с данными: {data_dir}")

if data_dir.exists():
    json_files = list(data_dir.glob("*.json"))
    logging.info(f"📄 Найдено JSON: {len(json_files)}")
else:
    logging.error(f"❌ Папка {data_dir} не найдена!")
    data_dir.mkdir(parents=True, exist_ok=True)

# ============================================
# ЗАГРУЗКА JSON
# ============================================

def load_json(filename):
    filepath = data_dir / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.info(f"✅ Загружен {filename}")
            return data
    except FileNotFoundError:
        logging.warning(f"⚠️ Файл не найден: {filename}")
        return {}
    except Exception as e:
        logging.error(f"❌ Ошибка {filename}: {e}")
        return {}

logging.info("🚀 Загрузка JSON файлов...")

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
islands_data = load_json("islands.json")

# ============================================
# ДИАГНОСТИКА PETS.JSON
# ============================================
logging.info("🔍 Диагностика pets.json:")
if pets_data:
    logging.info(f"✅ pets_data загружен, тип: {type(pets_data)}")
    if isinstance(pets_data, dict):
        logging.info(f"📊 Ключи в pets_data: {list(pets_data.keys())}")
        if "pets" in pets_data:
            logging.info(f"📊 Ключи в pets_data['pets']: {list(pets_data['pets'].keys())}")
        else:
            logging.info("❌ В pets_data нет ключа 'pets'")
    else:
        logging.info(f"❌ pets_data не словарь, а {type(pets_data)}")
else:
    logging.error("❌ pets_data пустой или не загружен")

# ============================================
# ИМПОРТ ВСЕХ ХЕНДЛЕРОВ
# ============================================

from handlers import (
    start as start_handler,
    game,
    pets,
    exchange,
    rainbow,
    premium,
    nft,
    guild,
    pvp,
    codex,
    events,
    shop,
    top,
    admin
)

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БД
# ============================================

def get_or_create_player(telegram_id, username=None, first_name=None):
    """Получить игрока из БД или создать нового"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            # Создаём пользователя
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Создаём персонажа
            character = Character(user_id=user.id)
            db.add(character)
            db.commit()
            db.refresh(character)
            logging.info(f"👤 Создан новый пользователь: {telegram_id}")
        else:
            character = db.query(Character).filter(Character.user_id == user.id).first()
            user.last_active = datetime.utcnow()
            db.commit()
        
        return user, character
    finally:
        db.close()

def save_character(character):
    """Сохранить изменения персонажа"""
    db = SessionLocal()
    try:
        db.merge(character)
        db.commit()
    finally:
        db.close()

def refresh_energy(character):
    """Обновить энергию (10 в час)"""
    now = int(time.time())
    if character.last_update == 0:
        character.last_update = now
        return
    
    hours_passed = (now - character.last_update) // 3600
    if hours_passed > 0:
        character.energy = min(character.energy + hours_passed * 10, character.max_energy)
        character.last_update += hours_passed * 3600
        save_character(character)

def refresh_magic(character):
    """Обновить магию (5 в час)"""
    now = int(time.time())
    if character.last_magic_update == 0:
        character.last_magic_update = now
        return
    
    hours_passed = (now - character.last_magic_update) // 3600
    if hours_passed > 0:
        character.magic = min(character.magic + hours_passed * 5, character.max_magic)
        character.last_magic_update += hours_passed * 3600
        save_character(character)

def calculate_damage(character):
    """Посчитать урон"""
    weapon_damage = 0
    inventory = character.get_inventory()
    for item_id in inventory:
        if item_id in items_data.get("items", {}):
            item = items_data["items"][item_id]
            if item.get("type") == "weapon":
                weapon_damage += item.get("damage", 0)
    return character.base_damage + weapon_damage + (character.strength - 1)

def calculate_defense(character):
    """Посчитать защиту"""
    defense = character.defense_bonus
    inventory = character.get_inventory()
    for item_id in inventory:
        if item_id in items_data.get("items", {}):
            item = items_data["items"][item_id]
            if item.get("type") == "armor":
                defense += item.get("defense", 0)
    return defense + (character.vitality - 1)

def check_daily_login(character):
    """Проверить ежедневный вход"""
    now = int(time.time())
    last_login = character.last_login if hasattr(character, 'last_login') else 0
    
    if now - last_login > 86400:
        if now - last_login > 172800:
            character.login_streak = 0
        
        character.login_streak += 1
        if character.login_streak > 7:
            character.login_streak = 1
        
        character.last_login = now
        save_character(character)
        return True, character.login_streak
    return False, 0

def get_daily_reward(streak):
    """Получить награду за ежедневный вход"""
    rewards = {
        1: {"gold": 100, "dstn": 5, "items": ["health_potion"]},
        2: {"gold": 200, "dstn": 10, "items": ["mana_potion"]},
        3: {"gold": 300, "dstn": 15, "items": ["teleport_scroll"]},
        4: {"gold": 400, "dstn": 20, "items": ["rainbow_shard"]},
        5: {"gold": 500, "dstn": 25, "items": ["legendary_chest"]},
        6: {"gold": 600, "dstn": 30, "items": ["epic_chest"]},
        7: {"gold": 1000, "dstn": 50, "items": ["mythril_ingot", 3]}
    }
    return rewards.get(streak, rewards[1])

# ============================================
# БАЗОВЫЕ КОМАНДЫ
# ============================================

@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        start_handler.start_command(message, bot, get_or_create_player, locations_data)
    except Exception as e:
        logging.error(f"Ошибка в /start: {e}")
        bot.send_message(
            message.chat.id,
            f"✅ БОТ РАБОТАЕТ!\n\n"
            f"📍 Локаций: {len(locations_data.get('locations', {})) if locations_data else 0}\n"
            f"⚔️ Врагов: {len(enemies_data.get('enemies', {})) if enemies_data else 0}\n"
            f"📦 Предметов: {len(items_data.get('items', {})) if items_data else 0}\n"
            f"🐾 Питомцев: {len(pets_data.get('pets', {})) if pets_data else 0}"
        )

@bot.message_handler(commands=['help'])
def help_command(message):
    try:
        start_handler.help_command(message, bot)
    except:
        text = "❓ *Доступные команды:*\n\n"
        text += "/start - информация о боте\n"
        text += "/profile - профиль\n"
        text += "/status - статус\n"
        text += "/inventory - инвентарь\n"
        text += "/location - локация\n"
        text += "/map - карта мира\n"
        text += "/class - выбор класса\n"
        text += "/craft - крафт\n"
        text += "/house - домик\n"
        text += "/pets - питомцы\n"
        text += "/exchange - обмен\n"
        text += "/rainbow - радужные камни\n"
        text += "/premium - премиум\n"
        text += "/nft - NFT\n"
        text += "/guild - гильдия\n"
        text += "/pvp - арена\n"
        text += "/codex - энциклопедия\n"
        text += "/events - ивенты\n"
        text += "/shop - магазин\n"
        text += "/top - рейтинги\n"
        text += "/help - это меню"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ============================================
# КОМАНДЫ ИЗ ХЕНДЛЕРОВ
# ============================================

@bot.message_handler(commands=['profile'])
def profile_command(message):
    try:
        game.profile_command(message, bot, get_or_create_player, items_data)
    except Exception as e:
        logging.error(f"Ошибка в /profile: {e}")
        bot.send_message(message.chat.id, "❌ Команда /profile временно недоступна")

@bot.message_handler(commands=['status'])
def status_command(message):
    try:
        game.status_command(message, bot, get_or_create_player, items_data)
    except Exception as e:
        logging.error(f"Ошибка в /status: {e}")
        bot.send_message(message.chat.id, "❌ Команда /status временно недоступна")

@bot.message_handler(commands=['inventory'])
def inventory_command(message):
    try:
        game.inventory_command(message, bot, get_or_create_player, items_data)
    except Exception as e:
        logging.error(f"Ошибка в /inventory: {e}")
        bot.send_message(message.chat.id, "❌ Команда /inventory временно недоступна")

@bot.message_handler(commands=['location'])
def location_command(message):
    try:
        game.location_command(message, bot, get_or_create_player, locations_data)
    except Exception as e:
        logging.error(f"Ошибка в /location: {e}")
        if locations_data and locations_data.get("locations"):
            first_loc = list(locations_data["locations"].values())[0]
            text = f"📍 *{first_loc.get('name', 'Локация')}*\n\n"
            text += first_loc.get('description', 'Описание отсутствует')
            bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['map'])
def map_command(message):
    try:
        game.map_command(message, bot)
    except Exception as e:
        logging.error(f"Ошибка в /map: {e}")
        text = "🗺️ *Карта мира*\n\n"
        text += "🌲 Лесная опушка\n"
        text += "🏘️ Деревня\n"
        text += "🏞️ Берег озера\n"
        text += "⛰️ Горы\n"
        text += "⛏️ Шахта\n"
        text += "🏛️ Руины\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['class'])
def class_command(message):
    try:
        game.class_command(message, bot, get_or_create_player)
    except Exception as e:
        logging.error(f"Ошибка в /class: {e}")
        bot.send_message(message.chat.id, "❌ Команда /class временно недоступна")

@bot.message_handler(commands=['craft'])
def craft_command(message):
    try:
        game.craft_command(message, bot)
    except Exception as e:
        logging.error(f"Ошибка в /craft: {e}")
        bot.send_message(message.chat.id, "❌ Команда /craft временно недоступна")

@bot.message_handler(commands=['house'])
def house_command(message):
    try:
        game.house_command(message, bot, get_or_create_player, house_data)
    except Exception as e:
        logging.error(f"Ошибка в /house: {e}")
        bot.send_message(message.chat.id, "❌ Команда /house временно недоступна")

# ============================================
# PETS - С ДИАГНОСТИКОЙ
# ============================================
@bot.message_handler(commands=['pets'])
def pets_command(message):
    try:
        # Пробуем вызвать функцию из хендлера
        pets.pets_command(message, bot, get_or_create_player, pets_data)
    except Exception as e:
        logging.error(f"Ошибка в /pets: {e}")
        # Диагностика в ответе пользователю
        if pets_data:
            bot.send_message(
                message.chat.id,
                f"🔍 Диагностика:\n"
                f"pets_data загружен: да\n"
                f"Тип: {type(pets_data)}\n"
                f"Ключи: {list(pets_data.keys()) if isinstance(pets_data, dict) else 'не словарь'}"
            )
        else:
            bot.send_message(message.chat.id, "❌ pets_data не загружен")

        # Запасной вариант с отображением питомцев из JSON
        if pets_data and isinstance(pets_data, dict):
            text = "🐾 *Доступные питомцы:*\n\n"
            count = 0
            
            # Проверяем, есть ли ключ "pets" внутри
            pets_dict = pets_data.get("pets", pets_data)
            
            # Общие (common)
            if "common" in pets_dict:
                text += "*Обычные:*\n"
                for pet_id, pet in pets_dict["common"].items():
                    name = pet.get('name', pet_id) if isinstance(pet, dict) else pet_id
                    level_req = pet.get('level_req', '?') if isinstance(pet, dict) else '?'
                    text += f"  • {name} (ур. {level_req})\n"
                    count += 1
                text += "\n"
            
            # Необычные (uncommon)
            if "uncommon" in pets_dict:
                text += "*Необычные:*\n"
                for pet_id, pet in pets_dict["uncommon"].items():
                    name = pet.get('name', pet_id) if isinstance(pet, dict) else pet_id
                    level_req = pet.get('level_req', '?') if isinstance(pet, dict) else '?'
                    text += f"  • {name} (ур. {level_req})\n"
                    count += 1
                text += "\n"
            
            # Редкие (rare)
            if "rare" in pets_dict:
                text += "*Редкие:*\n"
                for pet_id, pet in pets_dict["rare"].items():
                    name = pet.get('name', pet_id) if isinstance(pet, dict) else pet_id
                    level_req = pet.get('level_req', '?') if isinstance(pet, dict) else '?'
                    text += f"  • {name} (ур. {level_req})\n"
                    count += 1
                text += "\n"
            
            # Эпические (epic)
            if "epic" in pets_dict:
                text += "*Эпические:*\n"
                for pet_id, pet in pets_dict["epic"].items():
                    name = pet.get('name', pet_id) if isinstance(pet, dict) else pet_id
                    level_req = pet.get('level_req', '?') if isinstance(pet, dict) else '?'
                    text += f"  • {name} (ур. {level_req})\n"
                    count += 1
                text += "\n"
            
            # Легендарные (legendary)
            if "legendary" in pets_dict:
                text += "*Легендарные:*\n"
                for pet_id, pet in pets_dict["legendary"].items():
                    name = pet.get('name', pet_id) if isinstance(pet, dict) else pet_id
                    level_req = pet.get('level_req', '?') if isinstance(pet, dict) else '?'
                    text += f"  • {name} (ур. {level_req})\n"
                    count += 1
                text += "\n"
            
            # Мифические (mythic)
            if "mythic" in pets_dict:
                text += "*Мифические:*\n"
                for pet_id, pet in pets_dict["mythic"].items():
                    name = pet.get('name', pet_id) if isinstance(pet, dict) else pet_id
                    level_req = pet.get('level_req', '?') if isinstance(pet, dict) else '?'
                    text += f"  • {name} (ур. {level_req})\n"
                    count += 1
            
            if count > 0:
                bot.send_message(message.chat.id, text, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, "❌ В файле pets.json нет питомцев")
        else:
            bot.send_message(message.chat.id, "❌ Питомцы не загружены")

# ============================================
# ОСТАЛЬНЫЕ КОМАНДЫ
# ============================================

@bot.message_handler(commands=['exchange'])
def exchange_command(message):
    try:
        exchange.exchange_command(message, bot, get_or_create_player, exchange_data)
    except Exception as e:
        logging.error(f"Ошибка в /exchange: {e}")
        bot.send_message(message.chat.id, "❌ Команда /exchange временно недоступна")

@bot.message_handler(commands=['rainbow'])
def rainbow_command(message):
    try:
        rainbow.rainbow_command(message, bot, get_or_create_player, rainbow_data)
    except Exception as e:
        logging.error(f"Ошибка в /rainbow: {e}")
        bot.send_message(message.chat.id, "❌ Команда /rainbow временно недоступна")

@bot.message_handler(commands=['premium'])
def premium_command(message):
    try:
        premium.premium_command(message, bot, get_or_create_player, premium_data)
    except Exception as e:
        logging.error(f"Ошибка в /premium: {e}")
        bot.send_message(message.chat.id, "❌ Команда /premium временно недоступна")

@bot.message_handler(commands=['nft'])
def nft_command(message):
    try:
        nft.nft_command(message, bot, get_or_create_player, nft_data)
    except Exception as e:
        logging.error(f"Ошибка в /nft: {e}")
        bot.send_message(message.chat.id, "❌ Команда /nft временно недоступна")

@bot.message_handler(commands=['guild'])
def guild_command(message):
    try:
        guild.guild_command(message, bot, get_or_create_player)
    except Exception as e:
        logging.error(f"Ошибка в /guild: {e}")
        bot.send_message(message.chat.id, "❌ Команда /guild временно недоступна")

@bot.message_handler(commands=['pvp'])
def pvp_command(message):
    try:
        pvp.pvp_command(message, bot, get_or_create_player)
    except Exception as e:
        logging.error(f"Ошибка в /pvp: {e}")
        bot.send_message(message.chat.id, "❌ Команда /pvp временно недоступна")

@bot.message_handler(commands=['codex'])
def codex_command(message):
    try:
        codex.codex_command(message, bot, codex_data)
    except Exception as e:
        logging.error(f"Ошибка в /codex: {e}")
        bot.send_message(message.chat.id, "❌ Команда /codex временно недоступна")

@bot.message_handler(commands=['events'])
def events_command(message):
    try:
        events.events_command(message, bot, events_data)
    except Exception as e:
        logging.error(f"Ошибка в /events: {e}")
        bot.send_message(message.chat.id, "❌ Команда /events временно недоступна")

@bot.message_handler(commands=['shop'])
def shop_command(message):
    try:
        shop.shop_command(message, bot, get_or_create_player, items_data)
    except Exception as e:
        logging.error(f"Ошибка в /shop: {e}")
        bot.send_message(message.chat.id, "❌ Команда /shop временно недоступна")

@bot.message_handler(commands=['top'])
def top_command(message):
    try:
        top.top_command(message, bot, get_or_create_player)
    except Exception as e:
        logging.error(f"Ошибка в /top: {e}")
        bot.send_message(message.chat.id, "❌ Команда /top временно недоступна")

@bot.message_handler(commands=['admin'])
def admin_command(message):
    try:
        admin.admin_command(message, bot, get_or_create_player)
    except Exception as e:
        logging.error(f"Ошибка в /admin: {e}")
        bot.send_message(message.chat.id, "❌ Команда /admin временно недоступна")

# ============================================
# ОБРАБОТКА ВСЕХ ОСТАЛЬНЫХ СООБЩЕНИЙ
# ============================================
@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(
        message.chat.id,
        f"❓ Неизвестная команда. Напиши /help\n\n"
        f"Твоё сообщение: {message.text}"
    )

# ============================================
# HEALTH СЕРВЕР
# ============================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running')
    def log_message(self, *args): pass

def run_health():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logging.info(f"✅ Health server on port {port}")
    server.serve_forever()

threading.Thread(target=run_health, daemon=True).start()

# ============================================
# ЗАПУСК
# ============================================
logging.info("🚀 Бот запущен, ждем команды...")

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logging.error(f"❌ Polling error: {e}")
            time.sleep(5)
