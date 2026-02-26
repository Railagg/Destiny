# /bot/handlers/game.py
import logging
import random
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# ========== ПРОФИЛЬ И СТАТИСТИКА ==========

def profile_command(message, bot, get_or_create_player_func, items_data):
    """Команда /profile - профиль игрока"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверяем премиум статус
    premium_text = "✅" if user.premium_until and user.premium_until > datetime.utcnow() else "❌"
    
    text = f"👤 *Профиль игрока*\n\n"
    text += f"📛 Имя: {character.name}\n"
    text += f"📊 Уровень: {character.level}\n"
    text += f"✨ Опыт: {character.experience}\n"
    text += f"❤️ Здоровье: {character.health}/{character.max_health}\n"
    text += f"💙 Мана: {character.mana}/{character.max_mana}\n"
    text += f"⚡ Энергия: {character.energy}/{character.max_energy}\n"
    text += f"💰 Золото: {character.gold}\n"
    text += f"💫 DSTN: {character.destiny_tokens or 0}\n"
    text += f"⭐ Stars: {character.stars or 0}\n"
    text += f"👑 Премиум: {premium_text}\n"
    
    if character.player_class:
        text += f"⚔️ Класс: {character.player_class}\n"
    
    # Клавиатура
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Статистика", callback_data="game:stats"),
        InlineKeyboardButton("📦 Инвентарь", callback_data="game:inventory"),
        InlineKeyboardButton("⚔️ Бой", callback_data="combat:choose"),
        InlineKeyboardButton("🔙 В меню", callback_data="start:menu")
    )
    
    bot.send_message(
        message.chat.id, 
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

def stats_command(message, bot, get_or_create_player_func, items_data):
    """Команда /stats - детальная статистика персонажа"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Рассчитываем боевые показатели
    attack = character.strength * 2 + (character.level * 2)
    defense = character.vitality * 2 + (character.level * 1)
    magic = character.intelligence * 2 + (character.level * 1)
    
    # Учитываем экипировку
    if character.equipped_weapon:
        weapon = items_data.get("items", {}).get(character.equipped_weapon, {})
        attack += weapon.get("damage", 0)
    
    if character.equipped_armor:
        armor = items_data.get("items", {}).get(character.equipped_armor, {})
        defense += armor.get("defense", 0)
    
    text = f"⚔️ *Детальная статистика*\n\n"
    
    text += f"📊 *Основные параметры:*\n"
    text += f"├ Сила: {character.strength} (атака: {attack})\n"
    text += f"├ Ловкость: {character.agility} (шанс крита: {character.agility // 2}%)\n"
    text += f"├ Интеллект: {character.intelligence} (магия: {magic})\n"
    text += f"├ Выносливость: {character.vitality} (защита: {defense})\n"
    text += f"└ Удача: {character.luck} (шанс дропа: +{character.luck}%)\n\n"
    
    text += f"⚔️ *Боевые показатели:*\n"
    text += f"├ Общая атака: {attack}\n"
    text += f"├ Общая защита: {defense}\n"
    text += f"├ Магическая сила: {magic}\n"
    text += f"└ Крит. урон: x{1.5 + (character.agility / 100):.2f}\n\n"
    
    text += f"📈 *Прогресс:*\n"
    text += f"├ Убито мобов: {character.kills_total or 0}\n"
    text += f"├ Побед в PvP: {character.pvp_wins or 0}\n"
    text += f"├ Скрафчено предметов: {character.items_crafted or 0}\n"
    text += f"└ Собрано ресурсов: {character.resources_gathered or 0}\n"
    
    if character.player_class:
        text += f"\n🎯 Класс: {character.player_class} (ур. {character.class_level or 1})"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="game:profile"))
    
    bot.send_message(
        message.chat.id, 
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

# ========== ЛОКАЦИИ И ПЕРЕМЕЩЕНИЕ ==========

def location_command(message, bot, get_or_create_player_func, locations_data):
    """Команда /location - текущая локация"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    location_id = character.location or "start"
    location = locations_data.get("locations", {}).get(location_id, {})
    
    if not location:
        location = {
            "name": "Неизвестно",
            "description": "Локация не найдена",
            "enemies": []
        }
    
    text = f"📍 *{location.get('name', 'Локация')}*\n\n"
    text += location.get('description', 'Описание отсутствует')
    
    # Информация о врагах
    enemies = location.get('enemies', [])
    if enemies:
        text += f"\n\n⚔️ *Враги в локации:*\n"
        for enemy_id in enemies[:5]:  # Показываем первых 5
            from utils import enemies_data
            enemy = enemies_data.get("enemies", {}).get(enemy_id, {})
            name = enemy.get('name', enemy_id)
            level = enemy.get('level', 1)
            text += f"├ {name} (ур. {level})\n"
    
    # Информация о ресурсах
    resources = location.get('resources', [])
    if resources:
        text += f"\n🌿 *Ресурсы:*\n"
        for resource in resources[:3]:
            text += f"├ {resource}\n"
    
    # Клавиатура
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🗺️ Карта", callback_data="game:map"),
        InlineKeyboardButton("⚔️ Атаковать", callback_data="combat:choose"),
        InlineKeyboardButton("📦 Инвентарь", callback_data="game:inventory"),
        InlineKeyboardButton("🏠 Домик", callback_data="house:menu")
    )
    
    bot.send_message(
        message.chat.id, 
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

def map_command(message, bot):
    """Команда /map - карта мира"""
    text = "🗺️ *Карта мира Destiny*\n\n"
    
    text += "🌲 **Лесные зоны:**\n"
    text += "├ Лесная опушка (ур. 1-5)\n"
    text += "├ Дремучий лес (ур. 5-10)\n"
    text += "├ Священная роща (ур. 15-20)\n\n"
    
    text += "⛰️ **Горные зоны:**\n"
    text += "├ Скалистые горы (ур. 10-15)\n"
    text += "├ Пещеры гоблинов (ур. 15-20)\n"
    text += "├ Заснеженные вершины (ур. 20-25)\n\n"
    
    text += "🏜️ **Пустынные зоны:**\n"
    text += "├ Песчаные дюны (ур. 15-20)\n"
    text += "├ Древние руины (ур. 20-25)\n"
    text += "├ Оазис (ур. 25-30)\n\n"
    
    text += "🌊 **Водные зоны:**\n"
    text += "├ Берег озера (ур. 5-10)\n"
    text += "├ Глубокое озеро (ур. 10-15)\n"
    text += "├ Замёрзший океан (ур. 25-30)\n\n"
    
    text += "🌋 **Особые зоны:**\n"
    text += "├ Вулкан (ур. 30-35)\n"
    text += "├ Вулканический пляж (ур. 35-40)\n"
    text += "├ Логово дракона (ур. 50+)\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📍 Текущая локация", callback_data="game:location"),
        InlineKeyboardButton("🔙 Назад", callback_data="start:menu")
    )
    
    bot.send_message(
        message.chat.id, 
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

def move_command(message, bot, get_or_create_player_func, locations_data):
    """Команда /move - перемещение между локациями"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    current_location = character.location or "start"
    
    # Получаем доступные локации для перемещения
    all_locations = locations_data.get("locations", {})
    
    text = f"🗺️ *Куда отправимся?*\n\n"
    text += f"📍 Текущая локация: {all_locations.get(current_location, {}).get('name', 'Неизвестно')}\n\n"
    text += "🎯 *Доступные локации:*\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Добавляем кнопки для каждой локации
    for loc_id, loc_data in list(all_locations.items())[:8]:  # Ограничим 8 локациями
        if loc_id != current_location:
            name = loc_data.get('name', loc_id)
            level_req = loc_data.get('level_req', 1)
            
            if character.level >= level_req:
                text += f"├ {name} (ур. {level_req}+)\n"
                keyboard.add(InlineKeyboardButton(
                    f"➡️ {name}", 
                    callback_data=f"game:move_to:{loc_id}"
                ))
            else:
                text += f"├ {name} (🔒 ур. {level_req}+)\n"
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="game:location"))
    
    bot.send_message(
        message.chat.id, 
        text, 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

def move_to_location(call, bot, get_or_create_player_func, locations_data):
    """Обработчик перемещения в локацию"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Получаем ID локации из callback_data
    parts = call.data.split(':')
    if len(parts) >= 3:
        new_location = parts[2]
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка перемещения")
        return
    
    location = locations_data.get("locations", {}).get(new_location, {})
    
    if not location:
        bot.answer_callback_query(call.id, "❌ Локация не найдена")
        return
    
    # Проверяем уровень
    level_req = location.get('level_req', 1)
    if character.level < level_req:
        bot.answer_callback_query(
            call.id, 
            f"❌ Нужен уровень {level_req}!", 
            show_alert=True
        )
        return
    
    # Проверяем энергию
    energy_cost = location.get('travel_cost', 5)
    if character.energy < energy_cost:
        bot.answer_callback_query(
            call.id, 
            f"❌ Нужно {energy_cost} энергии!", 
            show_alert=True
        )
        return
    
    # Перемещаемся
    character.energy -= energy_cost
    character.location = new_location
    from main import save_character
    save_character(character)
    
    bot.answer_callback_query(call.id, f"✅ Перемещён в {location.get('name')}")
    
    # Показываем новую локацию
    location_command(call.message, bot, get_or_create_player_func, locations_data)

# ========== КЛАССЫ ==========

def class_command(message, bot, get_or_create_player_func):
    """Команда /class - выбор класса"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if character.player_class:
        text = f"⚔️ *Твой класс:*\n\n"
        text += f"🎯 {character.player_class.capitalize()}\n"
        text += f"📊 Уровень класса: {character.class_level or 1}\n\n"
        
        text += "Хочешь сменить класс? Используй /class_change"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
        
        bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')
        return
    
    text = "⚔️ *Выбери свой класс:*\n\n"
    
    text += "🛡️ *Воин*\n"
    text += "├ Сила: +5 | Выносливость: +3\n"
    text += "└ Мастер ближнего боя\n\n"
    
    text += "🏹 *Лучник*\n"
    text += "├ Ловкость: +5 | Удача: +2\n"
    text += "└ Быстрые атаки издалека\n\n"
    
    text += "🔮 *Маг*\n"
    text += "├ Интеллект: +5 | Мана: +50\n"
    text += "└ Могущественные заклинания\n\n"
    
    text += "🛡️ *Паладин*\n"
    text += "├ Сила: +3 | Выносливость: +3 | Интеллект: +2\n"
    text += "└ Защита и поддержка\n\n"
    
    text += "🗡️ *Разбойник*\n"
    text += "├ Ловкость: +4 | Удача: +3\n"
    text += "└ Высокий шанс крита\n\n"
    
    text += "🌿 *Друид*\n"
    text += "├ Интеллект: +4 | Выносливость: +2\n"
    text += "└ Магия природы и исцеление\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    classes = ["warrior", "archer", "mage", "paladin", "rogue", "druid"]
    class_names = ["Воин", "Лучник", "Маг", "Паладин", "Разбойник", "Друид"]
    
    for i, class_id in enumerate(classes):
        keyboard.add(InlineKeyboardButton(
            class_names[i], 
            callback_data=f"game:select_class:{class_id}"
        ))
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

def select_class_callback(call, bot, get_or_create_player_func):
    """Обработчик выбора класса"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    parts = call.data.split(':')
    if len(parts) >= 3:
        class_name = parts[2]
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка выбора")
        return
    
    if character.player_class:
        bot.answer_callback_query(call.id, "❌ Класс уже выбран!", show_alert=True)
        return
    
    # Бонусы классов
    class_bonuses = {
        "warrior": {"strength": 5, "vitality": 3},
        "archer": {"agility": 5, "luck": 2},
        "mage": {"intelligence": 5, "max_mana": 50},
        "paladin": {"strength": 3, "vitality": 3, "intelligence": 2},
        "rogue": {"agility": 4, "luck": 3},
        "druid": {"intelligence": 4, "vitality": 2}
    }
    
    bonuses = class_bonuses.get(class_name, {})
    
    # Применяем бонусы
    for stat, value in bonuses.items():
        if stat == "max_mana":
            character.max_mana += value
            character.mana = character.max_mana
        else:
            setattr(character, stat, getattr(character, stat) + value)
    
    character.player_class = class_name
    character.class_level = 1
    
    from main import save_character
    save_character(character)
    
    class_names = {
        "warrior": "Воин", "archer": "Лучник", "mage": "Маг",
        "paladin": "Паладин", "rogue": "Разбойник", "druid": "Друид"
    }
    
    bot.answer_callback_query(call.id, f"✅ Ты стал {class_names.get(class_name, class_name)}!")
    
    # Показываем профиль
    from .start import start_command
    start_command(call.message, bot, get_or_create_player_func)

# ========== БОЙ ==========

def battle_command(message, bot, get_or_create_player_func, enemies_data):
    """Команда /battle - начало боя"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверяем энергию
    if character.energy < 10:
        bot.send_message(
            message.chat.id,
            "❌ Недостаточно энергии! Отдохни в домике или подожди.",
            parse_mode='Markdown'
        )
        return
    
    # Получаем врагов в текущей локации
    from utils import locations_data
    location_id = character.location or "start"
    location = locations_data.get("locations", {}).get(location_id, {})
    enemy_ids = location.get('enemies', [])
    
    if not enemy_ids:
        bot.send_message(
            message.chat.id,
            "❌ В этой локации нет врагов!",
            parse_mode='Markdown'
        )
        return
    
    # Выбираем случайного врага
    enemy_id = random.choice(enemy_ids)
    enemy = enemies_data.get("enemies", {}).get(enemy_id, {})
    
    if not enemy:
        bot.send_message(message.chat.id, "❌ Ошибка загрузки врага")
        return
    
    # Показываем информацию о враге
    text = f"⚔️ *Бой!*\n\n"
    text += f"🐉 *Враг:* {enemy.get('name', enemy_id)}\n"
    text += f"📊 Уровень: {enemy.get('level', 1)}\n"
    text += f"❤️ Здоровье: {enemy.get('health', 50)}\n"
    text += f"⚔️ Атака: {enemy.get('damage', 5)}\n"
    
    if enemy.get('description'):
        text += f"\n📝 {enemy['description']}\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("⚔️ Атаковать", callback_data=f"combat:attack:{enemy_id}"),
        InlineKeyboardButton("🏃 Сбежать", callback_data="game:location")
    )
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ========== КВЕСТЫ ==========

def quest_command(message, bot, get_or_create_player_func, quests_data):
    """Команда /quest - список квестов"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Получаем доступные квесты
    all_quests = quests_data.get("quests", {}).get("daily", {})
    
    text = "📜 *Доступные квесты*\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for quest_id, quest in list(all_quests.items())[:5]:
        name = quest.get('name', quest_id)
        desc = quest.get('description', '')
        reward = quest.get('rewards', {})
        
        reward_text = []
        if reward.get('gold'):
            reward_text.append(f"{reward['gold']}💰")
        if reward.get('exp'):
            reward_text.append(f"{reward['exp']}✨")
        if reward.get('dstn'):
            reward_text.append(f"{reward['dstn']}💫")
        
        text += f"*{name}*\n"
        text += f"├ {desc}\n"
        text += f"└ Награда: {', '.join(reward_text)}\n\n"
        
        keyboard.add(InlineKeyboardButton(
            f"📋 {name[:20]}", 
            callback_data=f"quest:accept:{quest_id}"
        ))
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ========== КРАФТ ==========

def craft_command(message, bot, get_or_create_player_func, crafting_data, items_data):
    """Команда /craft - крафт предметов"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    recipes = crafting_data.get("crafting", {})
    
    text = "🔨 *Крафт предметов*\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Показываем категории крафта
    categories = {
        "weapons": "⚔️ Оружие",
        "armor": "🛡️ Броня", 
        "potions": "🧪 Зелья",
        "materials": "📦 Материалы"
    }
    
    for cat_id, cat_name in categories.items():
        if cat_id in recipes:
            text += f"├ {cat_name}\n"
            keyboard.add(InlineKeyboardButton(
                cat_name, 
                callback_data=f"craft:category:{cat_id}"
            ))
    
    text += "\nВыбери категорию для крафта"
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ========== ДОМИК ==========

def house_command(message, bot, get_or_create_player_func, house_data):
    """Команда /house - управление домиком"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    house_level = character.house_level or 0
    house_info = house_data.get("house", {}).get("levels", {}).get(str(house_level), {})
    
    text = f"🏠 *Твой домик*\n\n"
    text += f"📊 Уровень: {house_level}\n"
    
    if house_info:
        text += f"📝 {house_info.get('description', '')}\n\n"
        
        # Бонусы дома
        bonuses = house_info.get('bonuses', {})
        if bonuses:
            text += "✨ *Бонусы:*\n"
            if bonuses.get('rest_multiplier'):
                text += f"├ Отдых: x{bonuses['rest_multiplier']}\n"
            if bonuses.get('storage'):
                text += f"├ Хранилище: +{bonuses['storage']} слотов\n"
            if bonuses.get('craft_discount'):
                text += f"├ Скидка на крафт: {bonuses['craft_discount']}%\n"
            text += "\n"
    
    # Количество отдыхающих питомцев
    if character.house_pets:
        text += f"🐾 Питомцев в доме: {len(character.house_pets)}\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🛏️ Отдохнуть", callback_data="house:rest"),
        InlineKeyboardButton("📦 Хранилище", callback_data="house:storage"),
        InlineKeyboardButton("📈 Улучшить", callback_data="house:upgrade"),
        InlineKeyboardButton("🔙 Назад", callback_data="start:menu")
    )
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

def rest_in_house(call, bot, get_or_create_player_func, house_data):
    """Отдых в домике - восстановление энергии"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    house_level = character.house_level or 0
    house_info = house_data.get("house", {}).get("levels", {}).get(str(house_level), {})
    
    # Бонус к отдыху
    rest_multiplier = house_info.get('bonuses', {}).get('rest_multiplier', 1.0)
    
    # Восстанавливаем энергию
    energy_recovered = int(50 * rest_multiplier)
    old_energy = character.energy
    character.energy = min(character.max_energy, character.energy + energy_recovered)
    recovered = character.energy - old_energy
    
    from main import save_character
    save_character(character)
    
    bot.answer_callback_query(
        call.id, 
        f"✨ Отдохнул! +{recovered} энергии"
    )
    
    # Обновляем сообщение
    house_command(call.message, bot, get_or_create_player_func, house_data)

# ========== ЭКСПЕДИЦИИ ==========

def expedition_command(message, bot, get_or_create_player_func, expeditions_data):
    """Команда /expedition - экспедиции"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "🧭 *Экспедиции*\n\n"
    text += "Отправь своего питомца в экспедицию за ресурсами!\n\n"
    
    expeditions = expeditions_data.get("expeditions", {}).get("available", {})
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for exp_id, exp in expeditions.items():
        name = exp.get('name', exp_id)
        duration = exp.get('duration_hours', 1)
        rewards = exp.get('rewards', {})
        
        reward_text = []
        if rewards.get('gold'):
            reward_text.append(f"{rewards['gold']}💰")
        if rewards.get('items'):
            reward_text.append("🎁")
        
        text += f"*{name}*\n"
        text += f"├ ⏱️ {duration} ч.\n"
        text += f"└ 🎁 Награда: {', '.join(reward_text)}\n\n"
        
        keyboard.add(InlineKeyboardButton(
            f"🚀 {name}", 
            callback_data=f"expedition:start:{exp_id}"
        ))
    
    if character.current_expedition:
        text += f"\n⏳ Текущая экспедиция: активна!"
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ========== ОБРАБОТЧИК КОЛБЭКОВ ==========

def handle_callback(call, bot, get_or_create_player_func, locations_data, items_data, 
                   enemies_data, quests_data, crafting_data, house_data, expeditions_data):
    """Обработчик callback-запросов для game"""
    data = call.data
    
    if data == "game:profile":
        profile_command(call.message, bot, get_or_create_player_func, items_data)
    
    elif data == "game:stats":
        stats_command(call.message, bot, get_or_create_player_func, items_data)
    
    elif data == "game:location":
        location_command(call.message, bot, get_or_create_player_func, locations_data)
    
    elif data == "game:map":
        map_command(call.message, bot)
    
    elif data == "game:move":
        move_command(call.message, bot, get_or_create_player_func, locations_data)
    
    elif data.startswith("game:move_to:"):
        move_to_location(call, bot, get_or_create_player_func, locations_data)
    
    elif data.startswith("game:select_class:"):
        select_class_callback(call, bot, get_or_create_player_func)
    
    elif data == "house:rest":
        rest_in_house(call, bot, get_or_create_player_func, house_data)
    
    else:
        bot.answer_callback_query(call.id, "⏳ В разработке")

# ========== ЭКСПОРТ ==========

__all__ = [
    'profile_command',
    'stats_command',
    'location_command',
    'map_command',
    'move_command',
    'class_command',
    'battle_command',
    'quest_command',
    'craft_command',
    'house_command',
    'expedition_command',
    'handle_callback'
]
