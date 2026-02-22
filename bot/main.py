import telebot
import json
import time
import random
import os
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from database import engine, Base, get_db
from models import User, Character

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не задан!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Загружаем данные квеста
try:
    with open('quest.json', 'r', encoding='utf-8') as f:
        quest_data = json.load(f)
    print(f"✅ Квест загружен! Локаций: {len(quest_data.get('locations', {}))}")
except Exception as e:
    print(f"❌ Ошибка загрузки квеста: {e}")
    quest_data = {"locations": {}, "items": {}, "spells": {}, "enemies": {}}

# Загружаем дополнительные JSON файлы
try:
    with open('../data/items.json', 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    print(f"✅ Предметы загружены")
except:
    items_data = {"items": {}}
    print("⚠️ Предметы не загружены")

try:
    with open('../data/classes.json', 'r', encoding='utf-8') as f:
        classes_data = json.load(f)
    print(f"✅ Классы загружены")
except:
    classes_data = {"classes": {}}
    print("⚠️ Классы не загружены")

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

# ============================================
# КОМАНДА /start
# ============================================

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    user, character = get_or_create_player(user_id, username, first_name)

    refresh_energy(character)
    refresh_magic(character)

    # Создаем клавиатуру с WebApp
    markup = InlineKeyboardMarkup()
    webapp_button = InlineKeyboardButton(
        text="🎮 ОТКРЫТЬ ИГРУ",
        web_app=WebAppInfo(url="https://destiny-1-6m57.onrender.com")
    )
    markup.add(webapp_button)
    
    # Добавляем кнопки для команд
    markup.row(
        InlineKeyboardButton("📊 Статус", callback_data="cmd_status"),
        InlineKeyboardButton("🎒 Инвентарь", callback_data="cmd_inventory")
    )
    markup.row(
        InlineKeyboardButton("🗺️ Карта", callback_data="cmd_map"),
        InlineKeyboardButton("📜 Квесты", callback_data="cmd_quests")
    )

    bot.send_message(
        message.chat.id,
        f"👋 *Добро пожаловать, {first_name}!*\n\n"
        f"⚡ Энергия: {character.energy}/{character.max_energy}\n"
        f"💰 Золото: {character.gold}\n"
        f"🪙 DSTN: {character.destiny_tokens}\n"
        f"❤️ Здоровье: {character.health}/{character.max_health}\n\n"
        f"Нажми кнопку ниже, чтобы открыть игру 👇",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# КОМАНДА /profile - Профиль игрока
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
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /status - Статус персонажа
# ============================================

@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    damage = character.base_damage + (character.strength - 1)
    defense = character.defense_bonus + (character.vitality - 1)
    
    text = f"⚔️ *Статус персонажа*\n\n"
    text += f"❤️ Здоровье: {character.health}/{character.max_health}\n"
    text += f"⚡ Энергия: {character.energy}/{character.max_energy}\n"
    text += f"🔮 Магия: {character.magic}/{character.max_magic}\n"
    text += f"💰 Золото: {character.gold}\n"
    text += f"🪙 DSTN: {character.destiny_tokens}\n"
    text += f"\n⚔️ Урон: {damage}\n"
    text += f"🛡️ Защита: {defense}\n"
    text += f"🎯 Удача: {character.luck}%\n"
    text += f"⚡ Крит: {character.crit_chance}% (x{character.crit_multiplier})\n"
    text += f"💨 Уклонение: {character.dodge_chance}%\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /inventory - Инвентарь
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
        for item_id in inventory[:10]:  # Показываем первые 10
            if item_id in items_data.get("items", {}):
                item = items_data["items"][item_id]
                text += f"• {item.get('name', item_id)}"
                if item.get('rarity'):
                    text += f" ({item['rarity']})"
                text += "\n"
        
        if len(inventory) > 10:
            text += f"\n...и ещё {len(inventory) - 10} предметов"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /class - Выбор класса
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
        InlineKeyboardButton("⚔️ Мечник", callback_data="class:warrior"),
        InlineKeyboardButton("🏹 Лучник", callback_data="class:archer"),
        InlineKeyboardButton("🔮 Маг", callback_data="class:mage"),
        InlineKeyboardButton("🛡️ Страж", callback_data="class:guardian")
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
# КОМАНДА /map - Карта мира
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
    markup.add(InlineKeyboardButton("📍 Текущая локация", callback_data="cmd_location"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /location - Текущая локация
# ============================================

@bot.message_handler(commands=['location'])
def location_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    location_id = character.location
    location = quest_data.get("locations", {}).get(location_id, {})
    
    if not location:
        location = {
            "title": "Неизвестная локация",
            "description": "Ты находишься в неизвестном месте."
        }
    
    text = f"📍 *{location.get('title', 'Локация')}*\n\n"
    text += location.get('description', '')
    text += f"\n\n⚡ Энергия: {character.energy}/{character.max_energy}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🗺️ Карта мира", callback_data="cmd_map"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /craft - Крафт
# ============================================

@bot.message_handler(commands=['craft'])
def craft_command(message):
    text = "🔨 *Крафт предметов*\n\n"
    text += "Выбери категорию:\n\n"
    text += "⚔️ Оружие\n"
    text += "🛡️ Броня\n"
    text += "🛠️ Инструменты\n"
    text += "⚗️ Зелья\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Оружие", callback_data="craft:weapons"),
        InlineKeyboardButton("🛡️ Броня", callback_data="craft:armor"),
        InlineKeyboardButton("🛠️ Инструменты", callback_data="craft:tools"),
        InlineKeyboardButton("⚗️ Зелья", callback_data="craft:potions")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /house - Домик
# ============================================

@bot.message_handler(commands=['house'])
def house_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    if character.house_level == 0:
        text = "🏗️ *У тебя пока нет домика*\n\n"
        text += "Отправляйся на Берег озера, чтобы построить его!"
    else:
        text = f"🏠 *Твой домик (уровень {character.house_level})*\n\n"
        text += "⚡ Отдых восстанавливает больше энергии\n"
        text += "📦 Есть сундук для хранения\n"
        if character.house_level >= 2:
            text += "🔥 Есть мангал для готовки\n"
        if character.house_level >= 3:
            text += "🪟 Есть печь для стекла\n"
        if character.house_level >= 4:
            text += "✨ Есть телепорт\n"
        if character.house_level >= 5:
            text += "🏠 Есть баня и теплица\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚪 Войти в домик", callback_data="house:enter"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /pvp - PvP арена
# ============================================

@bot.message_handler(commands=['pvp'])
def pvp_command(message):
    text = "⚔️ *PvP Арена*\n\n"
    text += "Сражайся с другими игроками и поднимайся в рейтинге!\n\n"
    text += "🥊 *Тренировочная арена* - без рейтинга\n"
    text += "🏆 *Рейтинговая арена* - за рейтинг и награды\n"
    text += "👑 *Турнир* - по выходным\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🥊 Тренировка", callback_data="pvp:training"),
        InlineKeyboardButton("🏆 Рейтинг", callback_data="pvp:ranked")
    )
    markup.add(InlineKeyboardButton("📊 Рейтинг игроков", callback_data="pvp:rating"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /guild - Гильдия
# ============================================

@bot.message_handler(commands=['guild'])
def guild_command(message):
    text = "🏛️ *Гильдии*\n\n"
    text += "Объединяйся с другими игроками и получай бонусы!\n\n"
    text += "📋 Ты не состоишь в гильдии\n\n"
    text += "Команды:\n"
    text += "/guild_create [название] - создать гильдию\n"
    text += "/guild_join [название] - вступить в гильдию\n"
    text += "/guild_info - информация о гильдии"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /codex - Энциклопедия
# ============================================

@bot.message_handler(commands=['codex'])
def codex_command(message):
    text = "📚 *Энциклопедия*\n\n"
    text += "Выбери раздел:\n\n"
    text += "👾 Бестиарий - все монстры\n"
    text += "⚔️ Предметы - все предметы\n"
    text += "🗺️ Локации - все места\n"
    text += "🏆 Достижения - все ачивки\n"
    text += "🔨 Крафт - все рецепты\n"
    text += "🎭 Классы - информация о классах"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👾 Бестиарий", callback_data="codex:bestiary"),
        InlineKeyboardButton("⚔️ Предметы", callback_data="codex:items"),
        InlineKeyboardButton("🗺️ Локации", callback_data="codex:locations"),
        InlineKeyboardButton("🏆 Достижения", callback_data="codex:achievements"),
        InlineKeyboardButton("🔨 Крафт", callback_data="codex:crafting"),
        InlineKeyboardButton("🎭 Классы", callback_data="codex:classes")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /events - Ивенты
# ============================================

@bot.message_handler(commands=['events'])
def events_command(message):
    today = datetime.now().strftime("%A")
    events = {
        "Monday": "⛏️ Шахтёрский день - руда x2",
        "Tuesday": "🏹 Охотничий день - шкуры x2",
        "Wednesday": "🎣 Рыбный день - рыба x2",
        "Thursday": "🌈 День радуги - осколки x2",
        "Friday": "⚔️ PvP турнир - рейтинг x2",
        "Saturday": "🏛️ Гильдейские войны - опыт гильдии x2",
        "Sunday": "🙏 Благословение - всё x2"
    }
    
    text = "🎪 *Еженедельные ивенты*\n\n"
    for day, event in events.items():
        if day == today:
            text += f"👉 *СЕГОДНЯ*: {event}\n"
        else:
            text += f"• {event}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /premium - Премиум
# ============================================

@bot.message_handler(commands=['premium'])
def premium_command(message):
    text = "👑 *Премиум-подписка*\n\n"
    text += "🟢 *7 дней* - 50⭐\n"
    text += "├ Энергия: 150\n"
    text += "├ +10% золота\n"
    text += "└ +1 сундук/день\n\n"
    text += "🔵 *28 дней* - 150⭐\n"
    text += "├ Энергия: 175\n"
    text += "├ +15% золота\n"
    text += "└ +2 сундука/день\n\n"
    text += "🟣 *90 дней* - 400⭐\n"
    text += "├ Энергия: 200\n"
    text += "├ +20% золота\n"
    text += "├ +15% DSTN\n"
    text += "└ Фиолетовый ник\n\n"
    text += "🟡 *180 дней* - 700⭐\n"
    text += "├ Энергия: 225\n"
    text += "├ +25% золота\n"
    text += "├ +20% DSTN\n"
    text += "└ Золотой ник\n\n"
    text += "🔴 *365 дней* - 1200⭐\n"
    text += "├ Энергия: 250\n"
    text += "├ +30% золота\n"
    text += "├ +25% DSTN\n"
    text += "└ Красный ник + титул"
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🟢 7 дней - 50⭐", callback_data="premium:7days"),
        InlineKeyboardButton("🔵 28 дней - 150⭐", callback_data="premium:28days"),
        InlineKeyboardButton("🟣 90 дней - 400⭐", callback_data="premium:90days"),
        InlineKeyboardButton("🟡 180 дней - 700⭐", callback_data="premium:180days"),
        InlineKeyboardButton("🔴 365 дней - 1200⭐", callback_data="premium:365days")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /nft - NFT осколки
# ============================================

@bot.message_handler(commands=['nft'])
def nft_command(message):
    text = "💎 *NFT-осколки*\n\n"
    text += "Уникальные NFT, выпущенные ограниченным тиражом:\n\n"
    text += "🔴 *Красный* (10 шт) - 100⭐\n"
    text += "├ +5% урона\n"
    text += "└ Способность: Ярость\n\n"
    text += "🔵 *Синий* (10 шт) - 100⭐\n"
    text += "├ +5% защиты\n"
    text += "└ Способность: Щит\n\n"
    text += "🟢 *Зелёный* (10 шт) - 100⭐\n"
    text += "├ +5% уклонения\n"
    text += "└ Способность: Ветер\n\n"
    text += "🟡 *Жёлтый* (10 шт) - 100⭐\n"
    text += "├ +5% маг. урона\n"
    text += "└ Способность: Молния\n\n"
    text += "🟣 *Фиолетовый* (10 шт) - 200⭐\n"
    text += "├ +7% удачи\n"
    text += "└ Способность: Удача"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /rainbow - Радужные камни
# ============================================

@bot.message_handler(commands=['rainbow'])
def rainbow_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    text = "🌈 *Радужные камни*\n\n"
    text += "Собирай осколки и создавай легендарные предметы!\n\n"
    text += f"📊 Твои осколки: {character.rainbow_shards or 0}/9\n"
    text += f"💎 Твои камни: {character.rainbow_stones or 0}\n\n"
    text += "📅 *4-й день входа* - 1 осколок (100%)\n"
    text += "🔥 *Боссы* - шанс 5-30%\n"
    text += "🎁 *Легендарные сундуки* - шанс 25%\n\n"
    text += "🔮 *Крафт камня*: 9 осколков = 1 🌈 камень"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /shop - Магазин
# ============================================

@bot.message_handler(commands=['shop'])
def shop_command(message):
    text = "🏪 *Магазин*\n\n"
    text += "Выбери категорию:\n\n"
    text += "⚔️ Оружие\n"
    text += "🛡️ Броня\n"
    text += "🛠️ Инструменты\n"
    text += "⚗️ Зелья\n"
    text += "🎁 Сундуки\n"
    text += "👑 Премиум"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Оружие", callback_data="shop:weapons"),
        InlineKeyboardButton("🛡️ Броня", callback_data="shop:armor"),
        InlineKeyboardButton("🛠️ Инструменты", callback_data="shop:tools"),
        InlineKeyboardButton("⚗️ Зелья", callback_data="shop:potions"),
        InlineKeyboardButton("🎁 Сундуки", callback_data="shop:chests"),
        InlineKeyboardButton("👑 Премиум", callback_data="cmd_premium")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /top - Рейтинги
# ============================================

@bot.message_handler(commands=['top'])
def top_command(message):
    text = "🏆 *Рейтинги*\n\n"
    text += "1. Игрок1 - уровень 50\n"
    text += "2. Игрок2 - уровень 48\n"
    text += "3. Игрок3 - уровень 47\n"
    text += "4. Игрок4 - уровень 45\n"
    text += "5. Игрок5 - уровень 44\n"
    text += "...\n\n"
    text += "Ты пока не в топе"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 По уровню", callback_data="top:level"),
        InlineKeyboardButton("💰 По богатству", callback_data="top:gold"),
        InlineKeyboardButton("⚔️ По PvP", callback_data="top:pvp"),
        InlineKeyboardButton("🏛️ Гильдии", callback_data="top:guilds")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# КОМАНДА /help - Помощь
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
    text += "/shop - магазин"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    if call.data == "back_to_start":
        start_command(call.message)
    
    elif call.data == "cmd_status":
        status_command(call.message)
    
    elif call.data == "cmd_inventory":
        inventory_command(call.message)
    
    elif call.data == "cmd_map":
        map_command(call.message)
    
    elif call.data == "cmd_location":
        location_command(call.message)
    
    elif call.data == "cmd_premium":
        premium_command(call.message)
    
    elif call.data.startswith("class:"):
        class_name = call.data.split(":")[1]
        
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
        start_command(call.message)
    
    else:
        bot.answer_callback_query(call.id, "⏳ Эта функция в разработке")

# ============================================
# ЗАПУСК БОТА
# ============================================

print("=" * 40)
print("🤖 Destiny Bot с новыми командами")
print("=" * 40)
print("✅ Бот запускается...")
print("✅ Все команды загружены")
print("=" * 40)

if __name__ == "__main__":
    bot.infinity_polling()
