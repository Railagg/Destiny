import telebot
import json
import time
import random
import os
from datetime import datetime
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

def calculate_damage(character):
    """Посчитать урон"""
    weapon_damage = 0
    inventory = character.get_inventory()
    for item_id in inventory:
        if item_id in quest_data.get("items", {}):
            item = quest_data["items"][item_id]
            if item.get("type") == "weapon":
                weapon_damage += item.get("damage", 0)
    return character.base_damage + weapon_damage + (character.strength - 1)

def calculate_defense(character):
    """Посчитать защиту"""
    defense = character.defense_bonus
    inventory = character.get_inventory()
    for item_id in inventory:
        if item_id in quest_data.get("items", {}):
            item = quest_data["items"][item_id]
            if item.get("type") == "armor":
                defense += item.get("defense", 0)
    return defense + (character.vitality - 1)# ============================================
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
# КОМАНДА /status
# ============================================

@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    text = f"📊 *Статус персонажа*\n\n"
    text += f"👤 Имя: {user.first_name}\n"
    if character.player_class:
        text += f"📖 Класс: {character.player_class} (ур. {character.class_level})\n"
    text += f"\n⚡ Энергия: {character.energy}/{character.max_energy}"
    text += f"\n🔮 Магия: {character.magic}/{character.max_magic}"
    text += f"\n❤️ Здоровье: {character.health}/{character.max_health}"
    text += f"\n💰 Золото: {character.gold}"
    text += f"\n🪙 DSTN: {character.destiny_tokens}"
    text += f"\n⚔️ Урон: {calculate_damage(character)}"
    text += f"\n🛡️ Защита: {calculate_defense(character)}"
    text += f"\n🎒 Предметов: {len(character.get_inventory())}"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

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
        InlineKeyboardButton("⚔️ Воин", callback_data="class:warrior"),
        InlineKeyboardButton("🏹 Лучник", callback_data="class:archer"),
        InlineKeyboardButton("🔮 Маг", callback_data="class:mage"),
        InlineKeyboardButton("🛡️ Страж", callback_data="class:guardian")
    )
    
    bot.send_message(
        message.chat.id,
        "🌟 *Выбери свой класс:*\n\n"
        "⚔️ Воин: +3 силы, +2 урона\n"
        "🏹 Лучник: +3 ловкости, +5% уклонения\n"
        "🔮 Маг: +3 интеллекта, +30 маны\n"
        "🛡️ Страж: +3 живучести, +30 здоровья, +5 защиты",
        reply_markup=markup,
        parse_mode='Markdown'
    )# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    # Выбор класса
    if call.data.startswith("class:"):
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
        
        # Отправляем клавиатуру с WebApp
        markup = InlineKeyboardMarkup()
        webapp_button = InlineKeyboardButton(
            text="🎮 ОТКРЫТЬ ИГРУ",
            web_app=WebAppInfo(url="https://destiny-1-6m57.onrender.com")
        )
        markup.add(webapp_button)
        
        bot.send_message(
            call.message.chat.id,
            f"🎉 *Поздравляю!* Ты стал {class_name}!\n\n"
            f"Теперь можно играть! 👇",
            reply_markup=markup,
            parse_mode='Markdown'
        )
        return
    
    # Если кнопка не обработана
    bot.answer_callback_query(call.id)

# ============================================
# ЗАПУСК
# ============================================

print("=" * 40)
print("🤖 Destiny Bot с PostgreSQL")
print("=" * 40)
print("✅ Бот запускается...")
print("✅ База данных подключена")
print("=" * 40)

if __name__ == "__main__":
    bot.infinity_polling()
