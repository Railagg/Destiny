import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import random
import time
from datetime import datetime

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ КЛАССОВ
# ============================================

CLASSES = {
    "warrior": {
        "name": "⚔️ Мечник",
        "description": "Мастер клинка, наносящий огромный урон. Специализируется на критических ударах.",
        "emoji": "⚔️",
        "bonuses": {
            "strength": 3,
            "base_damage": 2,
            "crit_chance": 5
        },
        "start_items": ["iron_sword", "leather_armor"]
    },
    "archer": {
        "name": "🏹 Лучник",
        "description": "Меткий стрелок, поражающий цели издалека. Высокое уклонение и точность.",
        "emoji": "🏹",
        "bonuses": {
            "dexterity": 3,
            "dodge_chance": 8,
            "accuracy": 5
        },
        "start_items": ["longbow", "leather_armor"]
    },
    "mage": {
        "name": "🔮 Маг",
        "description": "Повелитель стихий, обрушивающий на врагов мощь магии.",
        "emoji": "🔮",
        "bonuses": {
            "intelligence": 3,
            "max_magic": 30,
            "magic_damage": 5
        },
        "start_items": ["staff", "robe"]
    },
    "guardian": {
        "name": "🛡️ Страж",
        "description": "Несокрушимый защитник, принимающий удар на себя. Огромная защита.",
        "emoji": "🛡️",
        "bonuses": {
            "vitality": 3,
            "max_health": 30,
            "defense_bonus": 5,
            "block_chance": 5
        },
        "start_items": ["iron_sword", "chainmail", "wooden_shield"]
    },
    "paladin": {
        "name": "⚔️✨ Паладин",
        "description": "Святой воин, сочетающий мощь меча с божественной магией. Растущий щит.",
        "emoji": "⚔️✨",
        "bonuses": {
            "strength": 2,
            "vitality": 2,
            "max_health": 20,
            "base_damage": 1,
            "holy_damage": 3
        },
        "start_items": ["iron_sword", "chainmail"]
    },
    "rogue": {
        "name": "🗡️ Разбойник",
        "description": "Тень в ночи, мастер скрытности и смертоносных атак из тени.",
        "emoji": "🗡️",
        "bonuses": {
            "dexterity": 3,
            "dodge_chance": 12,
            "crit_chance": 8,
            "crit_multiplier": 2.5
        },
        "start_items": ["dagger", "leather_armor"]
    },
    "druid": {
        "name": "🌿 Друид",
        "description": "Хранитель леса, повелевающий силами природы. Может лечить и призывать.",
        "emoji": "🌿",
        "bonuses": {
            "intelligence": 2,
            "vitality": 1,
            "max_magic": 25,
            "max_health": 15,
            "heal_power": 10
        },
        "start_items": ["staff", "robe"]
    },
    "warlock": {
        "name": "💀 Чернокнижник",
        "description": "Тёмный маг, заключивший сделку с демонами. Жертвует здоровьем ради силы.",
        "emoji": "💀",
        "bonuses": {
            "intelligence": 3,
            "max_magic": 30,
            "magic_damage": 8,
            "life_steal": 5
        },
        "start_items": ["staff", "robe"]
    },
    "shaman": {
        "name": "🥁 Шаман",
        "description": "Посредник между мирами, использующий силу духов предков и тотемов.",
        "emoji": "🥁",
        "bonuses": {
            "intelligence": 2,
            "vitality": 1,
            "max_magic": 25,
            "defense_bonus": 3,
            "spirit_power": 10
        },
        "start_items": ["totem", "robe"]
    }
}

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

def profile_command(message):
    """Команда /profile - профиль игрока"""
    from main import get_or_create_player, refresh_energy, refresh_magic
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    # Получаем название класса
    class_name = "Не выбран"
    class_emoji = ""
    if character.player_class and character.player_class in CLASSES:
        class_name = CLASSES[character.player_class]["name"]
        class_emoji = CLASSES[character.player_class]["emoji"]
    
    text = f"👤 *Профиль игрока*\n\n"
    text += f"🆔 ID: {user.telegram_id}\n"
    text += f"📛 Имя: {user.first_name}\n"
    if user.username:
        text += f"📧 Username: @{user.username}\n"
    text += f"\n📊 *Характеристики:*\n"
    text += f"📈 Уровень: {character.level}\n"
    text += f"✨ Опыт: {character.experience}/{character.level * 1000}\n"
    text += f"🎭 Класс: {class_emoji} {class_name} (ур. {character.class_level})\n"
    text += f"💰 Золото: {character.gold:,}\n".replace(",", " ")
    text += f"💎 DSTN: {character.dstn or 0:,}\n".replace(",", " ")
    text += f"📅 В игре с: {user.created_at.strftime('%d.%m.%Y')}\n"
    text += f"🔥 Стрик входа: {character.login_streak or 0} дней"
    
    # Добавляем титулы, если есть
    if character.titles:
        titles = character.titles.split(',') if isinstance(character.titles, str) else character.titles
        if titles:
            text += f"\n\n🏆 *Титулы:*\n"
            for title in titles[:3]:  # Показываем первые 3
                text += f"  • {title}\n"
            if len(titles) > 3:
                text += f"  ... и ещё {len(titles) - 3}"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Статус", callback_data="game:status"),
        InlineKeyboardButton("🎒 Инвентарь", callback_data="game:inventory"),
        InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def status_command(message):
    """Команда /status - статус персонажа"""
    from main import get_or_create_player, refresh_energy, refresh_magic, calculate_damage, calculate_defense, calculate_magic_damage
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    damage = calculate_damage(character)
    magic_damage = calculate_magic_damage(character)
    defense = calculate_defense(character)
    
    # Получаем название класса
    class_name = "Не выбран"
    if character.player_class and character.player_class in CLASSES:
        class_name = CLASSES[character.player_class]["name"]
    
    text = f"⚔️ *Статус персонажа*\n\n"
    text += f"🎭 *{class_name}*\n"
    text += f"📊 Уровень: {character.level}\n"
    text += f"✨ Опыт: {character.experience}/{character.level * 1000}\n\n"
    
    text += f"❤️ *Здоровье:* {character.health}/{character.max_health}\n"
    text += f"⚡ *Энергия:* {character.energy}/{character.max_energy}\n"
    text += f"🔮 *Магия:* {character.magic}/{character.max_magic}\n\n"
    
    text += f"⚔️ *Урон:* {damage} (физ.)\n"
    text += f"✨ *Маг. урон:* {magic_damage}\n"
    text += f"🛡️ *Защита:* {defense}\n\n"
    
    text += f"🎯 *Удача:* {character.luck or 0}%\n"
    text += f"⚡ *Крит:* {character.crit_chance or 0}% (x{character.crit_multiplier or 2})\n"
    text += f"💨 *Уклонение:* {character.dodge_chance or 0}%\n"
    text += f"🛡️ *Блок:* {character.block_chance or 0}% (блок {character.block_amount or 0} урона)\n"
    
    if character.player_class == "paladin":
        text += f"✨ *Щит паладина:* +{character.paladin_shield or 0} защиты\n"
    if character.player_class == "rogue":
        text += f"👻 *Скрытность:* +{character.stealth_bonus or 0}%\n"
    if character.player_class == "druid":
        text += f"🌿 *Сила лечения:* +{character.heal_power or 0}%\n"
    if character.player_class == "warlock":
        text += f"🩸 *Вампиризм:* {character.life_steal or 0}%\n"
    if character.player_class == "shaman":
        text += f"🥁 *Сила тотемов:* +{character.totem_power or 0}%\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👤 Профиль", callback_data="game:profile"),
        InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def inventory_command(message):
    """Команда /inventory - инвентарь"""
    from main import get_or_create_player, items_data, can_show_inventory
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Проверяем, можно ли открыть инвентарь
    if not can_show_inventory(character.current_location or "start"):
        bot.send_message(
            message.chat.id,
            "🎒 *Инвентарь*\n\n❌ Инвентарь можно открыть только на привалах или у торговцев.\n"
            "Найди место для отдыха!",
            parse_mode='Markdown'
        )
        return
    
    # Перенаправляем в новый хендлер инвентаря
    from handlers.inventory import show_inventory_command
    show_inventory_command(message, bot, get_or_create_player, items_data)

def location_command(message):
    """Команда /location - текущая локация"""
    from main import get_or_create_player, refresh_energy, refresh_magic, locations_data
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    location_id = character.current_location or "start"
    location = locations_data.get("locations", {}).get(location_id, {})
    
    if not location:
        location = {
            "name": "Неизвестная локация",
            "description": "Ты находишься в неизвестном месте."
        }
    
    text = f"📍 *{location.get('name', 'Локация')}*\n\n"
    text += location.get('description', '')
    text += f"\n\n⚡ Энергия: {character.energy}/{character.max_energy}"
    text += f"\n❤️ Здоровье: {character.health}/{character.max_health}"
    
    # Добавляем информацию о действиях
    actions = location.get('actions', [])
    if actions:
        text += f"\n\n🎮 *Доступные действия:*"
        for action in actions[:3]:
            action_text = action.get('text', '')
            if action.get('energy_cost'):
                action_text += f" ({action['energy_cost']}⚡)"
            text += f"\n• {action_text}"
    
    # Добавляем информацию о монстрах
    if location.get('enemies'):
        enemies = location['enemies']
        if isinstance(enemies, list):
            text += f"\n\n👾 *Враги:* {', '.join(enemies[:3])}"
            if len(enemies) > 3:
                text += f" и ещё {len(enemies) - 3}"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🗺️ Карта мира", callback_data="game:map"),
        InlineKeyboardButton("⚔️ В бой", callback_data="combat:start"),
        InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def map_command(message):
    """Команда /map - карта мира"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    text = "🗺️ *Карта мира*\n\n"
    text += "🌲 *Начальные локации (1-10)*\n"
    text += "├ Лесная опушка\n"
    text += "├ Деревенская площадь\n"
    text += "└ Берег озера\n\n"
    
    text += "⛰️ *Средние локации (10-20)*\n"
    text += "├ Горная тропа\n"
    text += "├ Шахта (5 уровней)\n"
    text += "└ Древние руины\n\n"
    
    text += "🔥 *Сложные локации (20-30)*\n"
    text += "├ Жерло вулкана\n"
    text += "├ Логово дракона\n"
    text += "└ Лабиринт\n\n"
    
    text += "🏜️ *Биомы (30-50)*\n"
    text += "├ Пустыня забвения\n"
    text += "├ Болото туманов\n"
    text += "└ Ледяные равнины\n\n"
    
    text += "🏖️ *Особые локации*\n"
    text += "├ Вулканический пляж (ур. 20+)\n"
    text += "└ Замёрзший океан (ур. 40+)\n\n"
    
    text += "🌋 *Легендарные острова*\n"
    text += "├ Огненный остров (3🌈)\n"
    text += "├ Кристальный остров (1🌟)\n"
    text += "└ Остров драконов (5🌟)\n\n"
    
    text += f"📍 *Текущая локация:* {character.current_location or 'start'}"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📍 Текущая", callback_data="game:location"),
        InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def class_command(message):
    """Команда /class - выбор класса"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    if character.player_class:
        class_name = CLASSES.get(character.player_class, {}).get("name", character.player_class)
        bot.reply_to(message, f"❌ Ты уже выбрал класс: {class_name}")
        return
    
    text = "🌟 *Выбери свой класс:*\n\n"
    text += "Каждый класс даёт уникальные бонусы и особенности.\n"
    text += "Выбор нельзя изменить!\n\n"
    
    for class_id, class_info in CLASSES.items():
        text += f"{class_info['emoji']} *{class_info['name']}*\n"
        text += f"└ {class_info['description']}\n"
    
    markup = InlineKeyboardMarkup(row_width=3)
    
    # Создаём кнопки для всех 9 классов
    buttons = []
    for class_id, class_info in CLASSES.items():
        buttons.append(InlineKeyboardButton(
            class_info['emoji'], 
            callback_data=f"game:class:{class_id}"
        ))
    
    # Добавляем кнопки рядами по 3
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i+3])
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def craft_command(message):
    """Команда /craft - крафт"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    text = "🔨 *Крафт предметов*\n\n"
    text += f"📊 Твой уровень крафта: {character.crafting_level or 1}\n"
    text += f"⚡ Энергия: {character.energy}/{character.max_energy}\n\n"
    text += "Выбери категорию:\n\n"
    text += "⚔️ Оружие\n"
    text += "🛡️ Броня\n"
    text += "🛠️ Инструменты\n"
    text += "⚗️ Зелья\n"
    text += "🍲 Еда\n"
    text += "📦 Материалы\n"
    text += "🪑 Мебель\n"
    text += "✨ Особое"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Оружие", callback_data="game:craft:weapons"),
        InlineKeyboardButton("🛡️ Броня", callback_data="game:craft:armor"),
        InlineKeyboardButton("🛠️ Инструменты", callback_data="game:craft:tools"),
        InlineKeyboardButton("⚗️ Зелья", callback_data="game:craft:potions"),
        InlineKeyboardButton("🍲 Еда", callback_data="game:craft:food"),
        InlineKeyboardButton("📦 Материалы", callback_data="game:craft:materials"),
        InlineKeyboardButton("🪑 Мебель", callback_data="game:craft:furniture"),
        InlineKeyboardButton("✨ Особое", callback_data="game:craft:special")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def house_command(message):
    """Команда /house - домик"""
    from main import get_or_create_player, house_data
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    house_level = character.house_level or 0
    
    if house_level == 0:
        text = "🏗️ *У тебя пока нет домика*\n\n"
        text += "Отправляйся на Берег озера, чтобы построить его!\n"
        text += "Требуется: 100🪵, 100🪨, 20🔩, 10🪟"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏗️ Построить", callback_data="game:house:build"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
        
    else:
        house_info = house_data.get("house", {}).get("levels", {}).get(str(house_level), {})
        text = f"🏠 *Твой домик (уровень {house_level})*\n\n"
        text += house_info.get('description', '') + "\n\n"
        text += "⚡ *Возможности:*\n"
        text += "• 🛏️ Отдых восстанавливает энергию и здоровье\n"
        text += "• 📦 Есть сундук для хранения\n"
        
        if house_level >= 2:
            text += "• 🔥 Есть мангал для готовки\n"
        if house_level >= 3:
            text += "• 🪟 Есть печь для стекла\n"
        if house_level >= 4:
            text += "• ✨ Есть телепорт\n"
        if house_level >= 5:
            text += "• 🏠 Есть баня и теплица\n"
            text += "• 🐕 Можно разместить питомцев\n"
        
        # Показываем кнопку инвентаря (в доме можно)
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🛏️ Отдохнуть", callback_data="game:house:rest"),
            InlineKeyboardButton("📦 Сундук", callback_data="game:house:storage"),
            InlineKeyboardButton("🎒 Инвентарь", callback_data="game:inventory")
        )
        
        if house_level >= 2:
            markup.add(InlineKeyboardButton("🔥 Мангал", callback_data="game:house:grill"))
        if house_level >= 3:
            markup.add(InlineKeyboardButton("🪟 Печь", callback_data="game:house:furnace"))
        if house_level >= 4:
            markup.add(InlineKeyboardButton("✨ Телепорт", callback_data="game:house:teleport"))
        if house_level >= 5:
            markup.add(
                InlineKeyboardButton("🏠 Баня", callback_data="game:house:bath"),
                InlineKeyboardButton("🌱 Теплица", callback_data="game:house:greenhouse")
            )
        
        markup.add(InlineKeyboardButton("🔨 Улучшить", callback_data="game:house:upgrade"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func, items_data):
    """Обработка игровых кнопок"""
    from main import save_character, refresh_energy, refresh_magic, calculate_damage, calculate_defense, calculate_magic_damage
    
    data = call.data.split(':')
    action = data[1] if len(data) > 1 else ""
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    if action == "back_to_start":
        from handlers.start import start_command
        start_command(call.message)
    
    elif action == "profile":
        profile_command(call.message)
    
    elif action == "status":
        status_command(call.message)
    
    elif action == "inventory":
        # Проверяем, можно ли открыть инвентарь
        from main import can_show_inventory
        if can_show_inventory(character.current_location or "start"):
            from handlers.inventory import show_inventory_command
            show_inventory_command(call.message, bot_instance, get_or_create_player_func, items_data)
        else:
            bot_instance.answer_callback_query(
                call.id, 
                "🎒 Инвентарь можно открыть только на привалах!"
            )
    
    elif action == "map":
        map_command(call.message)
    
    elif action == "location":
        location_command(call.message)
    
    elif action.startswith("class:"):
        class_id = action.split(':')[1]
        
        if character.player_class:
            bot_instance.answer_callback_query(call.id, "❌ Ты уже выбрал класс")
            return
        
        if class_id not in CLASSES:
            bot_instance.answer_callback_query(call.id, "❌ Неизвестный класс")
            return
        
        class_info = CLASSES[class_id]
        
        # Применяем бонусы класса
        character.player_class = class_id
        for stat, value in class_info.get("bonuses", {}).items():
            if hasattr(character, stat):
                current = getattr(character, stat) or 0
                setattr(character, stat, current + value)
        
        # Добавляем стартовые предметы
        for item_id in class_info.get("start_items", []):
            character.add_item(item_id)
        
        save_character(character)
        
        bot_instance.answer_callback_query(call.id, f"✅ Ты стал {class_info['name']}!")
        bot_instance.delete_message(call.message.chat.id, call.message.message_id)
        from handlers.start import start_command
        start_command(call.message)
    
    elif action.startswith("craft:"):
        craft_type = action.split(':')[1]
        
        # Загружаем данные крафта
        try:
            with open('data/crafting.json', 'r', encoding='utf-8') as f:
                crafting_data = json.load(f)
        except:
            crafting_data = {}
        
        text = f"🔨 *Крафт: {craft_type}*\n\n"
        
        # Получаем рецепты из crafting_data
        recipes = crafting_data.get("recipes", {})
        
        # Определяем, какие рецепты показывать
        if craft_type == "weapons":
            category = recipes.get("weapons", {})
            for item_id, item in category.items():
                if item.get("level_req", 0) <= character.crafting_level or 1:
                    text += f"• {item.get('name')} (ур. {item.get('level_req')})\n"
                    mats = item.get('ingredients', {})
                    if mats:
                        text += f"  Требуется: {', '.join([f'{v} {k}' for k, v in mats.items()])}\n"
                    text += f"  ⏱️ {item.get('craft_time', 0)} сек\n\n"
        else:
            text += "Эта категория в разработке"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:craft"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif action == "craft":
        craft_command(call.message)
    
    elif action.startswith("house:"):
        house_action = action.split(':')[1]
        
        if house_action == "build":
            # Проверяем ресурсы для постройки
            required = {"wood": 100, "stone": 100, "iron_ingot": 20, "glass": 10}
            inventory = character.get_inventory()
            
            has_all = True
            missing = []
            for item, count in required.items():
                if inventory.count(item) < count:
                    has_all = False
                    missing.append(f"{count} {item}")
            
            if has_all:
                for item, count in required.items():
                    for _ in range(count):
                        character.remove_item(item)
                character.house_level = 1
                save_character(character)
                bot_instance.answer_callback_query(call.id, "🏠 Домик построен!")
                house_command(call.message)
            else:
                bot_instance.answer_callback_query(call.id, f"❌ Не хватает: {', '.join(missing)}")
        
        elif house_action == "rest":
            # Отдых в домике
            cooldown = 3600  # 1 час
            last_rest = character.last_rest_time or 0
            now = int(time.time())
            
            if now - last_rest < cooldown:
                remaining = cooldown - (now - last_rest)
                minutes = remaining // 60
                bot_instance.answer_callback_query(call.id, f"⏳ Отдых ещё не доступен. Подожди {minutes} мин.")
                return
            
            # Бонус за уровень дома
            house_level = character.house_level or 1
            energy_gain = 20 + (house_level * 10)
            health_gain = 10 * house_level
            
            character.energy = min(character.energy + energy_gain, character.max_energy)
            character.health = min(character.health + health_gain, character.max_health)
            character.last_rest_time = now
            save_character(character)
            
            bot_instance.answer_callback_query(call.id, f"✅ Ты отдохнул! +{energy_gain}⚡, +{health_gain}❤️")
            house_command(call.message)
        
        elif house_action == "storage":
            # Открыть сундук
            bot_instance.answer_callback_query(call.id, "⏳ Сундук в разработке")
        
        elif house_action == "grill":
            # Мангал
            bot_instance.answer_callback_query(call.id, "⏳ Мангал в разработке")
        
        elif house_action == "furnace":
            # Печь для стекла
            bot_instance.answer_callback_query(call.id, "⏳ Печь в разработке")
        
        elif house_action == "teleport":
            # Телепорт
            bot_instance.answer_callback_query(call.id, "⏳ Телепорт в разработке")
        
        elif house_action == "bath":
            # Баня
            bot_instance.answer_callback_query(call.id, "⏳ Баня в разработке")
        
        elif house_action == "greenhouse":
            # Теплица
            bot_instance.answer_callback_query(call.id, "⏳ Теплица в разработке")
        
        elif house_action == "upgrade":
            # Улучшение дома
            bot_instance.answer_callback_query(call.id, "⏳ Улучшение в разработке")
        
        else:
            house_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
