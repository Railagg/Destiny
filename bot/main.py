import telebot
import json
import time
import random
import os
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pathlib import Path

from database import engine, Base, get_db
from models import User, Character

# Импортируем все обработчики
from handlers import start, game, pets, exchange, rainbow, premium, nft, guild, pvp, codex, events, shop, top, admin

print("🚀 Запуск бота Destiny...")
print("=" * 50)

# ============================================
# ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# ============================================
try:
    # Создаем таблицы в базе данных
    Base.metadata.create_all(bind=engine)
    print("✅ База данных подключена")
except Exception as e:
    print(f"❌ Ошибка подключения к БД: {e}")

# ============================================
# ТОКЕН БОТА
# ============================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не задан!")
    print("👉 Добавь переменную окружения BOT_TOKEN в настройках Render")
    exit(1)

print(f"✅ BOT_TOKEN получен (первые 10 символов: {BOT_TOKEN[:10]}...)")

# ============================================
# СОЗДАНИЕ БОТА И ПРОВЕРКА ТОКЕНА
# ============================================
try:
    bot = telebot.TeleBot(BOT_TOKEN)
    print("✅ Экземпляр бота создан")
    
    # Проверяем, что токен рабочий
    me = bot.get_me()
    print(f"✅ Бот авторизован как: @{me.username} (ID: {me.id})")
    print(f"📝 Имя бота: {me.first_name}")
except Exception as e:
    print(f"❌ Ошибка авторизации бота: {e}")
    print("👉 Проверь, что BOT_TOKEN правильный и бот существует")
    print("👉 Токен должен выглядеть так: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ")
    exit(1)

# ============================================
# ЗАГРУЗКА ДАННЫХ ИЗ JSON
# ============================================

DATA_DIR = Path(__file__).parent.parent / "data"
print(f"📁 Путь к данным: {DATA_DIR}")

def load_json(filename):
    """Загрузить JSON файл из папки data"""
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Загружен {filename}")
            return data
    except FileNotFoundError:
        print(f"⚠️ Файл не найден: {filename}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в JSON файле {filename}: {e}")
        return {}
    except Exception as e:
        print(f"❌ Ошибка загрузки {filename}: {e}")
        return {}

# Загружаем все JSON файлы
print("🚀 Загрузка JSON файлов...")
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

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def get_or_create_player(telegram_id, username=None, first_name=None):
    """Получить игрока из БД или создать нового"""
    db = get_db()
    
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
        print(f"👤 Создан новый пользователь: {telegram_id}")
    else:
        character = db.query(Character).filter(Character.user_id == user.id).first()
        user.last_active = datetime.utcnow()
        db.commit()
    
    db.close()
    return user, character

def save_character(character):
    """Сохранить изменения персонажа"""
    db = get_db()
    db.merge(character)
    db.commit()
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
    
    # Прошло больше суток?
    if now - last_login > 86400:
        # Сбрасываем стрик, если прошло больше 48 часов
        if now - last_login > 172800:
            character.login_streak = 0
        
        # Увеличиваем счётчик дней
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
# ⚠️ КОМАНДА /start ЗАКОММЕНТИРОВАНА - используется из handlers/start.py
# ============================================

# @bot.message_handler(commands=['start'])
# def start_command(message):
#     user_id = message.from_user.id
#     username = message.from_user.username
#     first_name = message.from_user.first_name
#
#     user, character = get_or_create_player(user_id, username, first_name)
#
#     refresh_energy(character)
#     refresh_magic(character)
#    
#     # Проверяем ежедневный вход
#     claimed, streak = check_daily_login(character)
#     if claimed:
#         reward = get_daily_reward(streak)
#         character.gold += reward["gold"]
#         character.destiny_tokens += reward["dstn"]
#         for item in reward["items"]:
#             if isinstance(item, list):
#                 for _ in range(item[1]):
#                     character.add_item(item[0])
#             else:
#                 character.add_item(item)
#         save_character(character)
#        
#         bot.send_message(
#             message.chat.id,
#             f"🎁 *Ежедневная награда!*\nДень {streak}\n"
#             f"💰 +{reward['gold']} золота\n"
#             f"🪙 +{reward['dstn']} DSTN",
#             parse_mode='Markdown'
#         )
#
#     # Создаем клавиатуру с WebApp
#     markup = InlineKeyboardMarkup()
#     webapp_button = InlineKeyboardButton(
#         text="🎮 ОТКРЫТЬ ИГРУ",
#         web_app=WebAppInfo(url="https://destiny-1-6m57.onrender.com")
#     )
#     markup.add(webapp_button)
#    
#     # Добавляем кнопки для команд
#     markup.row(
#         InlineKeyboardButton("📊 Статус", callback_data="game:status"),
#         InlineKeyboardButton("🎒 Инвентарь", callback_data="game:inventory")
#     )
#     markup.row(
#         InlineKeyboardButton("🗺️ Карта", callback_data="game:map"),
#         InlineKeyboardButton("📜 Квесты", callback_data="game:quests")
#     )
#     markup.row(
#         InlineKeyboardButton("🐾 Питомцы", callback_data="pets:menu"),
#         InlineKeyboardButton("💱 Обмен", callback_data="exchange:menu")
#     )
#
#     bot.send_message(
#         message.chat.id,
#         f"👋 *Добро пожаловать, {first_name}!*\n\n"
#         f"⚡ Энергия: {character.energy}/{character.max_energy}\n"
#         f"💰 Золото: {character.gold}\n"
#         f"🪙 DSTN: {character.destiny_tokens}\n"
#         f"❤️ Здоровье: {character.health}/{character.max_health}\n\n"
#         f"📅 Стрик входа: {character.login_streak or 0} дней",
#         reply_markup=markup,
#         parse_mode='Markdown'
#     )

print("📝 Регистрация обработчиков команд...")

# ============================================
# КОМАНДА /profile
# ============================================

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

# ============================================
# КОМАНДА /status
# ============================================

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

# ============================================
# КОМАНДА /inventory
# ============================================

@bot.message_handler(commands=['inventory'])
def inventory_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    inventory = character.get_inventory()
    
    if not inventory:
        text = "🎒 *Инвентарь пуст*"
    else:
        text = "🎒 *Твой инвентарь:*\n\n"
        
        # Группируем предметы
        items_count = {}
        for item_id in inventory:
            if item_id in items_count:
                items_count[item_id] += 1
            else:
                items_count[item_id] = 1
        
        # Показываем с количеством
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

# ============================================
# КОМАНДА /location
# ============================================

@bot.message_handler(commands=['location'])
def location_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    location_id = character.location
    location = locations_data.get("locations", {}).get(location_id, {})
    
    if not location:
        location = {
            "name": "Неизвестная локация",
            "description": "Ты находишься в неизвестном месте."
        }
    
    text = f"📍 *{location.get('name', 'Локация')}*\n\n"
    text += location.get('description', '')
    text += f"\n\n⚡ Энергия: {character.energy}/{character.max_energy}"
    
    # Добавляем информацию о монстрах
    if location.get('mobs'):
        text += f"\n\n👾 Враги: {', '.join(location['mobs'])}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🗺️ Карта мира", callback_data="game:map"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /map
# ============================================

@bot.message_handler(commands=['map'])
def map_command(message):
    text = "🗺️ *Карта мира*\n\n"
    text += "🌲 *Начальные локации (1-10)*\n"
    text += "├ Лесная опушка\n"
    text += "├ Деревенская площадь\n"
    text += "└ Берег озера\n\n"
    text += "⛰️ *Средние локации (10-20)*\n"
    text += "├ Горная тропа\n"
    text += "├ Шахта\n"
    text += "└ Древние руины\n\n"
    text += "🔥 *Сложные локации (20-30)*\n"
    text += "├ Жерло вулкана\n"
    text += "├ Логово дракона\n"
    text += "└ Лабиринт\n\n"
    text += "🏜️ *Биомы (30-50)*\n"
    text += "├ Пустыня забвения\n"
    text += "├ Болото туманов\n"
    text += "└ Ледяные равнины"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📍 Текущая локация", callback_data="game:location"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /class
# ============================================

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
        "🌟 *Выбери свой класс:*\n\n"
        "⚔️ *Мечник* - высокий урон, криты\n"
        "🏹 *Лучник* - дальний бой, уклонение\n"
        "🔮 *Маг* - магический урон, много маны\n"
        "🛡️ *Страж* - защита, много здоровья",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# КОМАНДА /craft
# ============================================

@bot.message_handler(commands=['craft'])
def craft_command(message):
    text = "🔨 *Крафт предметов*\n\n"
    text += "Выбери категорию:\n\n"
    text += "⚔️ Оружие\n"
    text += "🛡️ Броня\n"
    text += "🛠️ Инструменты\n"
    text += "⚗️ Зелья\n"
    text += "🍲 Еда\n"
    text += "🪱 Наживки"
    
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

# ============================================
# КОМАНДА /house
# ============================================

@bot.message_handler(commands=['house'])
def house_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    house_level = character.house_level or 0
    
    if house_level == 0:
        text = "🏗️ *У тебя пока нет домика*\n\n"
        text += "Отправляйся на Берег озера, чтобы построить его!\n"
        text += "Требуется: 100🪵, 100🪨, 20🔩, 10🪟"
    else:
        house_info = house_data.get("house", {}).get("levels", {}).get(str(house_level), {})
        text = f"🏠 *Твой домик (уровень {house_level})*\n\n"
        text += house_info.get('description', '') + "\n\n"
        text += "⚡ Отдых восстанавливает больше энергии\n"
        text += "📦 Есть сундук для хранения\n"
        if house_level >= 2:
            text += "🔥 Есть мангал для готовки\n"
        if house_level >= 3:
            text += "🪟 Есть печь для стекла\n"
        if house_level >= 4:
            text += "✨ Есть телепорт\n"
        if house_level >= 5:
            text += "🏠 Есть баня и теплица\n"
    
    markup = InlineKeyboardMarkup()
    if house_level == 0:
        markup.add(InlineKeyboardButton("🏗️ Построить", callback_data="game:house:build"))
    else:
        markup.add(InlineKeyboardButton("🚪 Войти в домик", callback_data="game:house:enter"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /help
# ============================================

@bot.message_handler(commands=['help'])
def help_command(message):
    text = "❓ *Помощь*\n\n"
    text += "📋 *Основные команды:*\n"
    text += "/start - начать игру\n"
    text += "/profile - профиль\n"
    text += "/status - статус\n"
    text += "/inventory - инвентарь\n"
    text += "/location - локация\n"
    text += "/map - карта мира\n\n"
    text += "⚔️ *Боевые:*\n"
    text += "/class - выбор класса\n"
    text += "/pvp - PvP арена\n\n"
    text += "🏠 *Домик:*\n"
    text += "/house - домик\n"
    text += "/craft - крафт\n\n"
    text += "🐾 *Питомцы:*\n"
    text += "/pets - питомцы\n\n"
    text += "👥 *Социальное:*\n"
    text += "/guild - гильдия\n"
    text += "/top - рейтинги\n\n"
    text += "📚 *Информация:*\n"
    text += "/codex - энциклопедия\n"
    text += "/events - ивенты\n\n"
    text += "💎 *Премиум:*\n"
    text += "/premium - подписка\n"
    text += "/nft - NFT осколки\n"
    text += "/rainbow - радужные камни\n"
    text += "/shop - магазин\n\n"
    text += "💱 *Экономика:*\n"
    text += "/exchange - обмен TON/DSTN"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ============================================
# ОБРАБОТКА КОЛБЭКОВ (КНОПОК)
# ============================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработка всех колбэков"""
    try:
        parts = call.data.split(':')
        handler = parts[0]
        
        if handler == "game":
            # Обработка игровых кнопок
            if len(parts) > 1:
                action = parts[1]
                
                if action == "back_to_start":
                    # Вызываем start_command из handlers
                    from handlers.start import start_command
                    start_command(call.message, bot, get_or_create_player, locations_data)
                
                elif action == "status":
                    status_command(call.message)
                
                elif action == "inventory":
                    inventory_command(call.message)
                
                elif action == "map":
                    map_command(call.message)
                
                elif action == "location":
                    location_command(call.message)
                
                elif action.startswith("class:"):
                    class_name = action.split(':')[1]
                    user_id = call.from_user.id
                    user, character = get_or_create_player(user_id)
                    
                    if character.player_class:
                        bot.answer_callback_query(call.id, "❌ Ты уже выбрал класс")
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
                    # Вызываем start_command из handlers
                    from handlers.start import start_command
                    start_command(call.message, bot, get_or_create_player, locations_data)
                
                else:
                    bot.answer_callback_query(call.id, "⏳ Эта функция в разработке")
        
        elif handler == "pets":
            if hasattr(pets, 'handle_callback'):
                pets.handle_callback(call, bot, get_or_create_player, pets_data)
            else:
                bot.answer_callback_query(call.id, "🐾 Система питомцев в разработке")
        
        elif handler == "exchange":
            if hasattr(exchange, 'handle_callback'):
                exchange.handle_callback(call, bot, get_or_create_player, exchange_data)
            else:
                bot.answer_callback_query(call.id, "💱 Обменник в разработке")
        
        elif handler == "rainbow":
            if hasattr(rainbow, 'handle_callback'):
                rainbow.handle_callback(call, bot, get_or_create_player, rainbow_data)
            else:
                bot.answer_callback_query(call.id, "🌈 Радужные камни в разработке")
        
        elif handler == "premium":
            if hasattr(premium, 'handle_callback'):
                premium.handle_callback(call, bot, get_or_create_player, premium_data)
            else:
                bot.answer_callback_query(call.id, "👑 Премиум в разработке")
        
        elif handler == "nft":
            if hasattr(nft, 'handle_callback'):
                nft.handle_callback(call, bot, get_or_create_player, nft_data)
            else:
                bot.answer_callback_query(call.id, "💎 NFT в разработке")
        
        elif handler == "guild":
            if hasattr(guild, 'handle_callback'):
                guild.handle_callback(call, bot, get_or_create_player)
            else:
                bot.answer_callback_query(call.id, "🏛️ Гильдии в разработке")
        
        elif handler == "pvp":
            if hasattr(pvp, 'handle_callback'):
                pvp.handle_callback(call, bot, get_or_create_player)
            else:
                bot.answer_callback_query(call.id, "⚔️ PvP в разработке")
        
        elif handler == "codex":
            if hasattr(codex, 'handle_callback'):
                codex.handle_callback(call, bot, codex_data)
            else:
                bot.answer_callback_query(call.id, "📚 Энциклопедия в разработке")
        
        elif handler == "events":
            if hasattr(events, 'handle_callback'):
                events.handle_callback(call, bot, events_data)
            else:
                bot.answer_callback_query(call.id, "🎪 Ивенты в разработке")
        
        elif handler == "shop":
            if hasattr(shop, 'handle_callback'):
                shop.handle_callback(call, bot, get_or_create_player, items_data)
            else:
                bot.answer_callback_query(call.id, "🏪 Магазин в разработке")
        
        elif handler == "top":
            if hasattr(top, 'handle_callback'):
                top.handle_callback(call, bot, get_or_create_player)
            else:
                bot.answer_callback_query(call.id, "🏆 Рейтинги в разработке")
        
        elif handler == "admin":
            if hasattr(admin, 'handle_callback'):
                admin.handle_callback(call, bot, get_or_create_player)
            else:
                bot.answer_callback_query(call.id, "👨‍💻 Админка")
        
        else:
            bot.answer_callback_query(call.id, "⏳ Эта функция в разработке")
    
    except Exception as e:
        print(f"❌ Ошибка в handle_callback: {e}")
        bot.answer_callback_query(call.id, "⚠️ Произошла ошибка")

print("✅ Обработчики команд зарегистрированы")

# ============================================
# HTTP СЕРВЕР ДЛЯ RENDER
# ============================================

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os

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
        print(f"✅ Health server running on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Health server error: {e}")

# Запускаем health-сервер в отдельном потоке
health_thread = threading.Thread(target=run_health_server, daemon=True)
health_thread.start()

# ============================================
# ЗАПУСК БОТА
# ============================================

print("=" * 50)
print("🤖 Destiny Bot v2.0 - ГОТОВ К РАБОТЕ")
print("=" * 50)
print("✅ Все системы запущены")
print("🟢 Ожидание команд от пользователей...")
print("=" * 50)

if __name__ == "__main__":
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")
        time.sleep(5)
