import telebot
import json
import time
import random
import os
import sys
import logging
import requests
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pathlib import Path

# ============================================
# НАСТРОЙКА ЛОГИРОВАНИЯ ДЛЯ RENDER
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

# Принудительно сбрасываем буфер вывода
sys.stdout.reconfigure(line_buffering=True)

logging.info("🚀 Запуск бота Destiny...")
logging.info("=" * 50)

from database import engine, Base, get_db, SessionLocal
from models import User, Character
from sqlalchemy.orm import Session

# Импортируем все обработчики
from handlers import game, pets, exchange, rainbow, premium, nft, guild, pvp, codex, events, shop, top, admin
from handlers.start import start_command, help_command, handle_webapp_data

# ============================================
# ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# ============================================
try:
    Base.metadata.create_all(bind=engine)
    logging.info("✅ База данных подключена")
except Exception as e:
    logging.error(f"❌ Ошибка подключения к БД: {e}")
    logging.error("👉 Проверь переменную DATABASE_URL в настройках Render")

# ============================================
# ТОКЕН БОТА
# ============================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("❌ ОШИБКА: BOT_TOKEN не задан!")
    logging.error("👉 Добавь переменную окружения BOT_TOKEN в настройках Render")
    exit(1)

logging.info(f"✅ BOT_TOKEN получен (первые 10 символов: {BOT_TOKEN[:10]}...)")

# ============================================
# ПРИНУДИТЕЛЬНОЕ ОТКЛЮЧЕНИЕ ВЕБХУКА
# ============================================
try:
    webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    response = requests.get(webhook_url)
    if response.status_code == 200:
        logging.info("✅ Webhook успешно отключён")
    else:
        logging.warning(f"⚠️ Ошибка отключения вебхука: {response.text}")
except Exception as e:
    logging.warning(f"⚠️ Не удалось отключить вебхук: {e}")

# ============================================
# СОЗДАНИЕ БОТА И ПРОВЕРКА ТОКЕНА
# ============================================
try:
    bot = telebot.TeleBot(BOT_TOKEN)
    logging.info("✅ Экземпляр бота создан")
    
    me = bot.get_me()
    logging.info(f"✅ Бот авторизован как: @{me.username} (ID: {me.id})")
    logging.info(f"📝 Имя бота: {me.first_name}")
except Exception as e:
    logging.error(f"❌ Ошибка авторизации бота: {e}")
    logging.error("👉 Проверь, что BOT_TOKEN правильный и бот существует")
    exit(1)

# ============================================
# ЗАГРУЗКА ВСЕХ JSON ФАЙЛОВ - ИСПРАВЛЕННЫЙ ПУТЬ
# ============================================

# Определяем правильный путь для Render
if os.path.exists("/opt/render/project/src"):
    BASE_DIR = Path("/opt/render/project/src")
    logging.info("✅ Render: используем /opt/render/project/src")
else:
    BASE_DIR = Path(__file__).parent.parent
    logging.info("✅ Локально: используем родительскую папку")

DATA_DIR = BASE_DIR / "data"
logging.info(f"📁 Путь к данным: {DATA_DIR}")

def load_json(filename):
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.info(f"✅ Загружен {filename}")
            return data
    except FileNotFoundError:
        logging.warning(f"⚠️ Файл не найден: {filename}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"❌ Ошибка в JSON {filename}: {e}")
        return {}
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки {filename}: {e}")
        return {}

logging.info("🚀 Загрузка JSON файлов...")

# Основные JSON
locations_data = load_json("locations.json")
enemies_data = load_json("enemies.json")
items_data = load_json("items.json")
crafting_data = load_json("crafting.json")
classes_data = load_json("classes.json")
quests_data = load_json("quests.json")
house_data = load_json("house.json")

# Премиум и NFT
premium_data = load_json("premium.json")
nft_data = load_json("nft.json")

# Специальные системы
rainbow_data = load_json("rainbow.json")
events_data = load_json("events.json")
codex_data = load_json("codex.json")
biomes_data = load_json("biomes.json")
pets_data = load_json("pets.json")
secrets_data = load_json("secrets.json")
exchange_data = load_json("exchange.json")
islands_data = load_json("islands.json")

logging.info("✅ Все JSON загружены")

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def get_or_create_player(telegram_id, username=None, first_name=None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            character = Character(user_id=user.id)
            db.add(character)
            db.commit()
            db.refresh(character)
            logging.info(f"👤 Создан новый пользователь: {telegram_id}")
        else:
            character = db.query(Character).filter(Character.user_id == user.id).first()
            user.last_active = datetime.utcnow()
            db.commit()
        
        db.expunge_all()
        return user, character
    finally:
        db.close()

def save_character(character):
    db = SessionLocal()
    try:
        db.merge(character)
        db.commit()
    finally:
        db.close()

def refresh_energy(character):
    now = int(time.time())
    if character.last_update == 0:
        character.last_update = now
        return
    
    hours_passed = (now - character.last_update) // 3600
    if hours_passed > 0:
        character.energy = min(character.energy + hours_passed * 10, character.max_energy)
        character.last_update += hours_passed * 3600

def refresh_magic(character):
    now = int(time.time())
    if character.last_magic_update == 0:
        character.last_magic_update = now
        return
    
    hours_passed = (now - character.last_magic_update) // 3600
    if hours_passed > 0:
        character.magic = min(character.magic + hours_passed * 5, character.max_magic)
        character.last_magic_update += hours_passed * 3600

def calculate_damage(character):
    weapon_damage = 0
    inventory = character.get_inventory()
    for item_id in inventory:
        if item_id in items_data.get("items", {}):
            item = items_data["items"][item_id]
            if item.get("type") == "weapon":
                weapon_damage += item.get("damage", 0)
    return character.base_damage + weapon_damage + (character.strength - 1)

def calculate_defense(character):
    defense = character.defense_bonus
    inventory = character.get_inventory()
    for item_id in inventory:
        if item_id in items_data.get("items", {}):
            item = items_data["items"][item_id]
            if item.get("type") == "armor":
                defense += item.get("defense", 0)
    return defense + (character.vitality - 1)

def check_daily_login(character):
    now = int(time.time())
    last_login = character.last_login if hasattr(character, 'last_login') else 0
    
    if now - last_login > 86400:
        if now - last_login > 172800:
            character.login_streak = 0
        
        character.login_streak += 1
        if character.login_streak > 7:
            character.login_streak = 1
        
        character.last_login = now
        return True, character.login_streak
    return False, 0

def get_daily_reward(streak):
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

logging.info("📝 Регистрация обработчиков команд...")

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================
@bot.message_handler(commands=['start'])
def start_handler(message):
    start_command(message, bot)

@bot.message_handler(commands=['help'])
def help_handler(message):
    help_command(message, bot)

@bot.message_handler(commands=['profile'])
def profile_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    text = f"👤 *Профиль игрока*\n\n"
    text += f"🆔 ID: {user.telegram_id}\n"
    text += f"📛 Имя: {user.first_name}\n"
    if user.username:
        text += f"📧 Username: @{user.username}\n"
    text += f"\n📊 *Характеристики:*\n"
    text += f"📈 Уровень: {character.level}\n"
    text += f"✨ Опыт: {character.experience}\n"
    if character.player_class:
        text += f"🎭 Класс: {character.player_class} (ур. {character.class_level})\n"
    text += f"📅 В игре с: {user.created_at.strftime('%d.%m.%Y')}\n"
    text += f"📅 Стрик входа: {character.login_streak or 0} дней"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')
    
    save_character(character)

@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    damage = calculate_damage(character)
    defense = calculate_defense(character)
    
    text = f"⚔️ *Статус персонажа*\n\n"
    text += f"❤️ Здоровье: {character.health}/{character.max_health}\n"
    text += f"⚡ Энергия: {character.energy}/{character.max_energy}\n"
    text += f"🔮 Магия: {character.magic}/{character.max_magic}\n"
    text += f"💰 Золото: {character.gold}\n"
    text += f"🪙 DSTN: {character.destiny_tokens}\n"
    text += f"\n⚔️ Урон: {damage}\n"
    text += f"🛡️ Защита: {defense}\n"
    text += f"🎯 Удача: {character.luck or 0}%\n"
    text += f"⚡ Крит: {character.crit_chance or 0}% (x{character.crit_multiplier or 2})\n"
    text += f"💨 Уклонение: {character.dodge_chance or 0}%\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')
    
    save_character(character)

@bot.message_handler(commands=['inventory'])
def inventory_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    inventory = character.get_inventory()
    
    if not inventory:
        text = "🎒 *Инвентарь пуст*"
    else:
        text = "🎒 *Твой инвентарь:*\n\n"
        items_count = {}
        for item_id in inventory:
            items_count[item_id] = items_count.get(item_id, 0) + 1
        
        for item_id, count in items_count.items():
            if item_id in items_data.get("items", {}):
                item = items_data["items"][item_id]
                text += f"• {item.get('name', item_id)}"
                if count > 1:
                    text += f" x{count}"
                if item.get('rarity'):
                    text += f" ({item['rarity']})"
                text += "\n"
        text += f"\n📦 Всего предметов: {len(inventory)}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')
    
    save_character(character)

@bot.message_handler(commands=['location'])
def location_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    location_id = character.location
    location = locations_data.get("locations", {}).get(location_id, {})
    
    if not location:
        location = {"name": "Неизвестная локация", "description": "Ты в неизвестном месте."}
    
    text = f"📍 *{location.get('name', 'Локация')}*\n\n{location.get('description', '')}"
    text += f"\n\n⚡ Энергия: {character.energy}/{character.max_energy}"
    
    if location.get('mobs'):
        text += f"\n\n👾 Враги: {', '.join(location['mobs'])}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🗺️ Карта", callback_data="game:map"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')
    
    save_character(character)

@bot.message_handler(commands=['map'])
def map_command(message):
    text = "🗺️ *Карта мира*\n\n"
    text += "🌲 *Начальные (1-10)*\n├ Лесная опушка\n├ Деревня\n└ Берег озера\n\n"
    text += "⛰️ *Средние (10-20)*\n├ Горная тропа\n├ Шахта\n└ Руины\n\n"
    text += "🔥 *Сложные (20-30)*\n├ Вулкан\n├ Логово дракона\n└ Лабиринт\n\n"
    text += "🏜️ *Биомы (30-50)*\n├ Пустыня\n├ Болото\n└ Ледяные равнины"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📍 Текущая", callback_data="game:location"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['class'])
def class_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    if character.player_class:
        bot.reply_to(message, f"❌ Ты уже выбрал класс: {character.player_class}")
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Мечник", callback_data="game:class:warrior"),
        InlineKeyboardButton("🏹 Лучник", callback_data="game:class:archer"),
        InlineKeyboardButton("🔮 Маг", callback_data="game:class:mage"),
        InlineKeyboardButton("🛡️ Страж", callback_data="game:class:guardian")
    )
    
    bot.send_message(
        message.chat.id,
        "🌟 *Выбери класс:*\n\n"
        "⚔️ Мечник - урон, криты\n"
        "🏹 Лучник - дальний бой, уклонение\n"
        "🔮 Маг - магия, мана\n"
        "🛡️ Страж - защита, здоровье",
        reply_markup=markup, parse_mode='Markdown'
    )

@bot.message_handler(commands=['craft'])
def craft_command(message):
    text = "🔨 *Крафт*\n\nВыбери категорию:"
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Оружие", callback_data="game:craft:weapons"),
        InlineKeyboardButton("🛡️ Броня", callback_data="game:craft:armor"),
        InlineKeyboardButton("🛠️ Инструменты", callback_data="game:craft:tools"),
        InlineKeyboardButton("⚗️ Зелья", callback_data="game:craft:potions"),
        InlineKeyboardButton("🍲 Еда", callback_data="game:craft:food"),
        InlineKeyboardButton("🪱 Наживки", callback_data="game:craft:bait")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['house'])
def house_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    house_level = character.house_level or 0
    
    if house_level == 0:
        text = "🏗️ *Нет домика*\nПострой на берегу озера:\n100🪵 100🪨 20🔩 10🪟"
    else:
        house_info = house_data.get("house", {}).get("levels", {}).get(str(house_level), {})
        text = f"🏠 *Домик {house_level} ур.*\n{house_info.get('description', '')}\n\n"
        text += "⚡ Отдых +энергия\n📦 Сундук\n"
        if house_level >= 2: text += "🔥 Мангал\n"
        if house_level >= 3: text += "🪟 Печь для стекла\n"
        if house_level >= 4: text += "✨ Телепорт\n"
        if house_level >= 5: text += "🏠 Баня и теплица\n"
    
    markup = InlineKeyboardMarkup()
    if house_level == 0:
        markup.add(InlineKeyboardButton("🏗️ Построить", callback_data="game:house:build"))
    else:
        markup.add(InlineKeyboardButton("🚪 Войти", callback_data="game:house:enter"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')
    
    save_character(character)

# ============================================
# ОБРАБОТКА КОЛБЭКОВ
# ============================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        parts = call.data.split(':')
        handler = parts[0]
        
        if handler == "game":
            if len(parts) > 1:
                action = parts[1]
                
                if action == "back_to_start":
                    start_command(call.message, bot)
                elif action == "status":
                    status_command(call.message)
                elif action == "inventory":
                    inventory_command(call.message)
                elif action == "map":
                    map_command(call.message)
                elif action == "location":
                    location_command(call.message)
                elif action == "house":
                    house_command(call.message)
                elif action.startswith("class:"):
                    class_name = action.split(':')[1]
                    user_id = call.from_user.id
                    user, character = get_or_create_player(user_id)
                    
                    if character.player_class:
                        bot.answer_callback_query(call.id, "❌ Класс уже выбран")
                        return
                    
                    character.player_class = class_name
                    if class_name == "warrior":
                        character.strength = 3
                        character.base_damage += 2
                    elif class_name == "archer":
                        character.dexterity = 3
                        character.dodge_chance += 5
                    elif class_name == "mage":
                        character.intelligence = 3
                        character.max_magic += 30
                        character.magic += 30
                    elif class_name == "guardian":
                        character.vitality = 3
                        character.max_health += 30
                        character.health += 30
                        character.defense_bonus += 5
                    
                    save_character(character)
                    bot.answer_callback_query(call.id, f"✅ Ты стал {class_name}!")
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    start_command(call.message, bot)
                else:
                    bot.answer_callback_query(call.id, "⏳ В разработке")
        
        elif handler == "pets" and hasattr(pets, 'handle_callback'):
            pets.handle_callback(call, bot, get_or_create_player, pets_data)
        elif handler == "exchange" and hasattr(exchange, 'handle_callback'):
            exchange.handle_callback(call, bot, get_or_create_player, exchange_data)
        elif handler == "rainbow" and hasattr(rainbow, 'handle_callback'):
            rainbow.handle_callback(call, bot, get_or_create_player, rainbow_data)
        elif handler == "premium" and hasattr(premium, 'handle_callback'):
            premium.handle_callback(call, bot, get_or_create_player, premium_data)
        elif handler == "nft" and hasattr(nft, 'handle_callback'):
            nft.handle_callback(call, bot, get_or_create_player, nft_data)
        elif handler == "guild" and hasattr(guild, 'handle_callback'):
            guild.handle_callback(call, bot, get_or_create_player)
        elif handler == "pvp" and hasattr(pvp, 'handle_callback'):
            pvp.handle_callback(call, bot, get_or_create_player)
        elif handler == "codex" and hasattr(codex, 'handle_callback'):
            codex.handle_callback(call, bot, codex_data)
        elif handler == "events" and hasattr(events, 'handle_callback'):
            events.handle_callback(call, bot, events_data)
        elif handler == "shop" and hasattr(shop, 'handle_callback'):
            shop.handle_callback(call, bot, get_or_create_player, items_data)
        elif handler == "top" and hasattr(top, 'handle_callback'):
            top.handle_callback(call, bot, get_or_create_player)
        elif handler == "admin" and hasattr(admin, 'handle_callback'):
            admin.handle_callback(call, bot, get_or_create_player)
        else:
            bot.answer_callback_query(call.id, "⏳ Модуль в разработке")
    
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_callback: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка")

# ============================================
# WEBAPP DATA
# ============================================
@bot.message_handler(content_types=['web_app_data'])
def webapp_data_handler(message):
    handle_webapp_data(message, bot)

# ============================================
# HTTP СЕРВЕР ДЛЯ RENDER
# ============================================
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running')
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    try:
        port = int(os.getenv("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        logging.info(f"✅ Health server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logging.error(f"❌ Health server error: {e}")

health_thread = threading.Thread(target=run_health_server, daemon=True)
health_thread.start()

# ============================================
# ЗАПУСК БОТА
# ============================================
logging.info("=" * 50)
logging.info("🤖 Destiny Bot v2.0 - ГОТОВ К РАБОТЕ")
logging.info("=" * 50)
logging.info("✅ Все системы запущены")
logging.info("🟢 Ожидание команд...")
logging.info("=" * 50)

if __name__ == "__main__":
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"❌ Ошибка бота: {e}")
        time.sleep(5)
