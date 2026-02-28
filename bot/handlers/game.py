# /bot/handlers/game.py
import logging
import random
import time
import json
import tempfile
import os
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logger = logging.getLogger(__name__)

# ========== КОНСТАНТЫ ==========

ENERGY_COSTS = {
    "move": 1,
    "hunt": 5,
    "fish": 2,
    "craft": 2,
    "rest": 0,
    "gather": 2,
    "mine": 2,
    "dig_worms": 1
}

# Данные из codex.py
CLASS_INFO = {
    "warrior": {
        "name": "⚔️ Мечник",
        "description": "Мастер клинка, наносящий огромный урон. Специализируется на критических ударах.",
        "health": 120,
        "damage": 15,
        "defense": 8,
        "mastery": "Критические удары наносят на 50% больше урона",
        "difficulty": "⭐"
    },
    "archer": {
        "name": "🏹 Лучник",
        "description": "Меткий стрелок, поражающий цели издалека. Высокое уклонение и точность.",
        "health": 100,
        "damage": 12,
        "defense": 5,
        "mastery": "Критические удары игнорируют 50% защиты",
        "difficulty": "⭐⭐"
    },
    "mage": {
        "name": "🔮 Маг",
        "description": "Повелитель стихий, обрушивающий на врагов мощь магии.",
        "health": 80,
        "magic_damage": 20,
        "defense": 3,
        "mastery": "Заклинания стоят на 20% меньше маны",
        "difficulty": "⭐⭐⭐"
    },
    "paladin": {
        "name": "⚔️✨ Паладин",
        "description": "Святой воин, сочетающий мощь меча с божественной магией. Растущий щит.",
        "health": 150,
        "damage": 10,
        "defense": 12,
        "magic_damage": 8,
        "mastery": "Щит растёт с каждым ударом (до 150)",
        "difficulty": "⭐⭐"
    },
    "rogue": {
        "name": "🗡️ Разбойник",
        "description": "Тень в ночи, мастер скрытности и смертоносных атак из тени.",
        "health": 90,
        "damage": 12,
        "defense": 4,
        "mastery": "Атаки из скрытности наносят +50% урона",
        "difficulty": "⭐⭐⭐"
    },
    "druid": {
        "name": "🌿 Друид",
        "description": "Хранитель леса, повелевающий силами природы. Может лечить и призывать.",
        "health": 110,
        "magic_damage": 12,
        "defense": 6,
        "mastery": "Призывы живут на 1 ход дольше",
        "difficulty": "⭐⭐⭐"
    }
}

# Карта привалов (локация -> данные привала)
RESPOT_SPOTS = {
    "lake_shore": {
        "name": "🪵 У озера",
        "description": "Тихий уголок на берегу озера, чуть в стороне от домика рыбака. Шепот камышей и плеск воды успокаивают.",
        "energy_gain": 25,
        "health_gain": 15,
        "cooldown": 3600,  # 1 час
        "connections": ["deep_forest"],  # Отсюда можно пойти в глухой лес
        "image": "rest_lake.jpeg"
    },
    "mountain_path": {
        "name": "⛰️ Горный привал",
        "description": "Уютная площадка среди скал, защищённая от ветра. Отсюда открывается вид на долину.",
        "energy_gain": 20,
        "health_gain": 10,
        "cooldown": 3600,
        "connections": ["mountain_peak", "mine_entrance"],
        "image": "rest_mountain.jpeg"
    },
    "volcano_path": {
        "name": "🌋 Привал у вулкана",
        "description": "Тёплое место у подножия вулкана. Земля здесь нагрета лавой, можно погреть руки.",
        "energy_gain": 15,
        "health_gain": 5,
        "magic_gain": 20,
        "cooldown": 3600,
        "connections": ["volcano_crater", "volcanic_beach"],
        "image": "rest_volcano.jpeg"
    },
    "bridge_before_dragon": {
        "name": "🌉 Привал на мосту",
        "description": "Костер, разожжённый предыдущими путниками. Отсюда виден вход в логово дракона.",
        "energy_gain": 30,
        "health_gain": 30,
        "magic_gain": 30,
        "cooldown": 7200,  # 2 часа - особенное место
        "special_action": {
            "name": "🔥 Разжечь костёр",
            "description": "Разжечь костёр из шкуры и дров",
            "ingredients": {"leather": 1, "wood": 5},
            "achievement": "Поджигатель шкур"
        },
        "connections": ["dragon_lair", "ancient_ruins"],
        "image": "rest_bridge.jpeg"
    },
    "desert_oasis": {
        "name": "🏝️ Привал в оазисе",
        "description": "Прохладный оазис посреди пустыни. Пальмы дают тень, вода утоляет жажду.",
        "energy_gain": 35,
        "health_gain": 25,
        "cooldown": 3600,
        "connections": ["desert", "desert_pyramid"],
        "image": "rest_oasis.jpeg"
    },
    "ice_cave": {
        "name": "🧊 Привал в ледяной пещере",
        "description": "Укрытие от вечной пурги. Стены пещеры светятся голубым светом.",
        "energy_gain": 20,
        "health_gain": 15,
        "magic_gain": 25,
        "cooldown": 3600,
        "connections": ["ice_plains", "frozen_ocean"],
        "image": "rest_ice_cave.jpeg"
    },
    "witch_hut": {
        "name": "🏚️ Привал у ведьмы",
        "description": "Поляна перед хижиной болотной ведьмы. В котле что-то варится.",
        "energy_gain": 15,
        "health_gain": 10,
        "magic_gain": 40,
        "cooldown": 7200,
        "special_action": {
            "name": "🧙 Сварить зелье",
            "description": "Попросить ведьму сварить особенное зелье",
            "ingredients": {"swamp_herb": 3, "mushroom": 2, "magic_dust": 1},
            "result": "witch_potion"
        },
        "connections": ["swamp", "swamp_depths"],
        "image": "rest_witch.jpeg"
    },
    "crystal_grove": {
        "name": "💎 Привал в кристальной роще",
        "description": "Поляна, где растут кристальные деревья. Воздух искрится магией.",
        "energy_gain": 25,
        "health_gain": 20,
        "magic_gain": 50,
        "cooldown": 7200,
        "connections": ["crystal_island", "crystal_dragon_lair"],
        "image": "rest_crystal.jpeg"
    },
    "dragon_island_beach": {
        "name": "🐉 Привал на острове драконов",
        "description": "Песчаный пляж, где драконы греются на солнце. Относительно безопасно.",
        "energy_gain": 40,
        "health_gain": 30,
        "magic_gain": 40,
        "cooldown": 7200,
        "connections": ["dragon_island", "dragon_king_throne"],
        "image": "rest_dragon_beach.jpeg"
    }
}

# ========== ПРОФИЛЬ И СТАТИСТИКА ==========

def profile_command(message, bot, get_or_create_player_func, items_data):
    """Команда /profile - профиль игрока"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
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
    text += f"👑 Премиум: {premium_text}\n"
    
    if character.player_class:
        class_name = CLASS_INFO.get(character.player_class, {}).get('name', character.player_class)
        text += f"⚔️ Класс: {class_name}\n"
    
    # Информация о последнем отдыхе
    if character.last_rest_time:
        last_rest = datetime.fromtimestamp(character.last_rest_time)
        time_diff = datetime.utcnow() - last_rest
        hours = time_diff.total_seconds() // 3600
        text += f"⏰ Последний отдых: {int(hours)} ч назад\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Статистика", callback_data="game:stats"),
        InlineKeyboardButton("📦 Инвентарь", callback_data="game:inventory"),
        InlineKeyboardButton("⚔️ Бой", callback_data="combat:choose"),
        InlineKeyboardButton("🔙 В меню", callback_data="start:menu")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

def stats_command(message, bot, get_or_create_player_func, items_data):
    """Команда /stats - детальная статистика персонажа"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    attack = character.strength * 2 + (character.level * 2)
    defense = character.vitality * 2 + (character.level * 1)
    magic = character.intelligence * 2 + (character.level * 1)
    
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
        class_name = CLASS_INFO.get(character.player_class, {}).get('name', character.player_class)
        text += f"\n🎯 Класс: {class_name} (ур. {character.class_level or 1})"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="game:profile"))
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

# ========== КВЕСТЫ ==========

def quest_command(message, bot, get_or_create_player_func, quests_data):
    """Команда /quest - просмотр доступных квестов"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "📜 *Доступные квесты*\n\n"
    
    # Получаем активные квесты
    active_quests = character.active_quests or []
    
    if active_quests:
        text += "*📋 Активные квесты:*\n"
        for quest_id in active_quests[:3]:  # Показываем первые 3
            quest = quests_data.get("quests", {}).get(quest_id, {})
            if quest:
                progress = character.quest_progress.get(quest_id, {})
                current = progress.get("current", 0)
                target = quest.get("target", 1)
                text += f"├ {quest.get('name', quest_id)}: {current}/{target}\n"
        text += "\n"
    
    # Доступные квесты в локации
    location_id = character.location or "start"
    location_quests = []
    
    for q_id, q_data in quests_data.get("quests", {}).items():
        if q_id not in active_quests and q_id not in character.completed_quests:
            if location_id in q_data.get("locations", []):
                if character.level >= q_data.get("level_req", 1):
                    location_quests.append((q_id, q_data))
    
    if location_quests:
        text += "*📍 Квесты в текущей локации:*\n"
        for q_id, q_data in location_quests[:5]:
            text += f"├ {q_data.get('name')} (ур. {q_data.get('level_req', 1)})\n"
            text += f"│  {q_data.get('description', '')[:50]}...\n"
            text += f"│  🏆 Награда: {q_data.get('reward_gold', 0)}💰"
            if q_data.get('reward_exp'):
                text += f", {q_data.get('reward_exp')}✨"
            text += "\n"
    else:
        text += "❌ В этой локации нет доступных квестов.\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📋 Взять квест", callback_data="quest:available"),
        InlineKeyboardButton("📊 Прогресс", callback_data="quest:progress"),
        InlineKeyboardButton("✅ Завершённые", callback_data="quest:completed"),
        InlineKeyboardButton("🔙 Назад", callback_data="start:menu")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

# ========== КРАФТ ==========

def craft_command(message, bot, get_or_create_player_func, crafting_data, items_data):
    """Команда /craft - просмотр доступных рецептов крафта"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "⚒️ *Мастерская крафта*\n\n"
    
    # Группируем рецепты по категориям
    categories = {
        "weapons": "⚔️ Оружие",
        "armor": "🛡️ Броня",
        "tools": "🛠️ Инструменты",
        "potions": "🧪 Зелья",
        "food": "🍲 Еда",
        "special": "✨ Особые"
    }
    
    available_recipes = 0
    
    for cat_id, cat_name in categories.items():
        cat_recipes = []
        # Ищем рецепты
        if "crafting" in crafting_data and "categories" in crafting_data["crafting"]:
            recipes_data = crafting_data["crafting"]["categories"].get(cat_id, {})
            for recipe in recipes_data.get("recipes", []):
                if character.level >= recipe.get("level_req", 1):
                    cat_recipes.append(recipe)
        
        if cat_recipes:
            text += f"\n*{cat_name}:*\n"
            for recipe in cat_recipes[:3]:  # Показываем первые 3
                text += f"├ {recipe.get('name', 'Рецепт')}\n"
                available_recipes += 1
    
    if available_recipes == 0:
        text += "❌ Нет доступных рецептов\n"
    
    text += f"\n📊 Доступно рецептов: {available_recipes}"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⚔️ Оружие", callback_data="craft:weapons"),
        InlineKeyboardButton("🛡️ Броня", callback_data="craft:armor"),
        InlineKeyboardButton("🧪 Зелья", callback_data="craft:potions"),
        InlineKeyboardButton("🍲 Еда", callback_data="craft:food"),
        InlineKeyboardButton("📦 Все рецепты", callback_data="craft:all"),
        InlineKeyboardButton("🔙 Назад", callback_data="start:menu")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

# ========== ДОМ ==========

def house_command(message, bot, get_or_create_player_func, house_data):
    """Команда /house - управление домом"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверяем, есть ли у игрока дом
    if not character.house_level:
        text = "🏠 *У тебя пока нет дома*\n\n"
        text += "Ты можешь купить дом на рыночной площади!\n\n"
        text += "🏚️ *Домики:*\n"
        text += "├ Ур. 1 - Маленький домик: 1000💰\n"
        text += "├ Ур. 2 - Обычный дом: 5000💰\n"
        text += "├ Ур. 3 - Большой дом: 15000💰\n"
        text += "├ Ур. 4 - Особняк: 50000💰\n"
        text += "└ Ур. 5 - Замок: 100000💰\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("🏚️ Купить дом", callback_data="house:buy:1"),
            InlineKeyboardButton("🔙 Назад", callback_data="start:menu")
        )
    else:
        house_level = character.house_level
        house_info = house_data.get("houses", {}).get(str(house_level), {})
        
        text = f"🏠 *Твой дом (Ур. {house_level})*\n\n"
        text += f"📦 Хранилище: {len(character.house_storage or [])}/{house_info.get('storage', 50)}\n"
        text += f"⚡ Восстановление энергии: +{house_info.get('energy_bonus', 5)}/час\n"
        text += f"❤️ Восстановление здоровья: +{house_info.get('health_bonus', 10)}/час\n\n"
        
        text += "*🛏️ Удобства:*\n"
        if house_info.get('bed'):
            text += "├ 🛏️ Кровать\n"
        if house_info.get('crafting_table'):
            text += "├ 🔨 Верстак\n"
        if house_info.get('furnace'):
            text += "├ 🔥 Печь\n"
        if house_info.get('garden'):
            text += "├ 🌿 Сад\n"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📦 Хранилище", callback_data="house:storage"),
            InlineKeyboardButton("🛏️ Отдохнуть", callback_data="house:rest"),
            InlineKeyboardButton("🔨 Улучшить", callback_data=f"house:upgrade:{house_level}"),
            InlineKeyboardButton("🔙 Назад", callback_data="start:menu")
        )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

# ========== ЭКСПЕДИЦИИ ==========

def expedition_command(message, bot, get_or_create_player_func, expeditions_data):
    """Команда /expedition - управление экспедициями"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "🧭 *Экспедиции*\n\n"
    
    # Проверяем, есть ли активная экспедиция
    if character.active_expedition:
        expedition_id = character.active_expedition
        expedition = expeditions_data.get("expeditions", {}).get(expedition_id, {})
        
        if expedition:
            start_time = character.expedition_start_time or 0
            duration = expedition.get("duration", 3600)  # в секундах
            current_time = int(time.time())
            time_left = max(0, start_time + duration - current_time)
            
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            
            text += f"*Активная экспедиция:*\n"
            text += f"├ {expedition.get('name', expedition_id)}\n"
            text += f"├ Локация: {expedition.get('location', 'Неизвестно')}\n"
            text += f"├ Осталось: {hours}ч {minutes}м\n"
            text += f"├ Шанс успеха: {expedition.get('success_chance', 70)}%\n\n"
            
            if time_left <= 0:
                text += "✅ *Экспедиция завершена!*\n"
                text += "Используй /expedition claim, чтобы получить награду!\n"
                
                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton("🎁 Забрать награду", callback_data="expedition:claim"),
                    InlineKeyboardButton("🔙 Назад", callback_data="start:menu")
                )
            else:
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
    else:
        # Показываем доступные экспедиции
        location_id = character.location or "start"
        available_expeditions = []
        
        for exp_id, exp_data in expeditions_data.get("expeditions", {}).items():
            if location_id in exp_data.get("locations", []):
                if character.level >= exp_data.get("level_req", 1):
                    available_expeditions.append((exp_id, exp_data))
        
        if available_expeditions:
            text += "*Доступные экспедиции:*\n\n"
            for exp_id, exp_data in available_expeditions[:5]:
                text += f"├ {exp_data.get('name', exp_id)}\n"
                text += f"│  🎯 Уровень: {exp_data.get('level_req', 1)}\n"
                text += f"│  ⏱️ Время: {exp_data.get('duration', 3600) // 60} мин\n"
                text += f"│  🎁 Награда: {exp_data.get('reward_gold', 0)}💰"
                if exp_data.get('reward_exp'):
                    text += f", {exp_data.get('reward_exp')}✨"
                text += "\n\n"
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            for exp_id, exp_data in available_expeditions[:4]:
                keyboard.add(InlineKeyboardButton(
                    exp_data.get('name', exp_id),
                    callback_data=f"expedition:start:{exp_id}"
                ))
            keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
        else:
            text += "❌ Нет доступных экспедиций в текущей локации."
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

# ========== ПОДБОР ПРЕДМЕТОВ ==========

def take_item_action(call, bot, get_or_create_player_func, locations_data, items_data):
    """Обработчик подбора предмета с земли (одноразовое действие)"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    parts = call.data.split(':')
    if len(parts) >= 3:
        item_id = parts[2]
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка")
        return
    
    # Добавляем предмет
    character.add_item(item_id)
    
    # Запоминаем, что действие выполнено
    if not hasattr(character, 'one_time_actions') or character.one_time_actions is None:
        character.one_time_actions = []
    
    # Находим текст действия из локации
    location_id = character.location or "start"
    location = locations_data.get("locations", {}).get(location_id, {})
    action_text = "⚔️ Подобрать ржавый меч"  # По умолчанию
    
    for action in location.get('actions', []):
        if action.get('type') == 'take_item' and action.get('item') == item_id:
            action_text = action.get('text', action_text)
            break
    
    character.one_time_actions.append(action_text)
    
    from main import save_character
    save_character(character)
    
    # Получаем название предмета
    item = items_data.get("items", {}).get(item_id, {})
    item_name = item.get('name', item_id)
    
    bot.answer_callback_query(call.id, f"✅ Вы подобрали {item_name}!")
    
    # Обновляем локацию (кнопка должна исчезнуть)
    location_command(call.message, bot, get_or_create_player_func, locations_data, items_data)

# ========== ПОИСК В ТАЙНИКЕ ==========

def search_stash_action(call, bot, get_or_create_player_func, locations_data, items_data):
    """Обработчик поиска в тайнике"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    parts = call.data.split(':')
    if len(parts) >= 3:
        location_id = parts[2]
    else:
        location_id = character.location or "start"
    
    location = locations_data.get("locations", {}).get(location_id, {})
    stash = location.get('hidden_stash', {})
    
    if not stash:
        bot.answer_callback_query(call.id, "❌ Здесь нет тайника")
        return
    
    # Проверяем кулдаун
    now = int(time.time())
    last_search = character.last_stash_search.get(location_id, 0) if hasattr(character, 'last_stash_search') else 0
    cooldown = stash.get('cooldown', 3600)
    
    if now - last_search < cooldown:
        remaining = cooldown - (now - last_search)
        minutes = remaining // 60
        bot.answer_callback_query(call.id, f"⏳ Тайник ещё не восстановился. Подожди {minutes} мин.", show_alert=True)
        return
    
    # Записываем время поиска
    if not hasattr(character, 'last_stash_search'):
        character.last_stash_search = {}
    character.last_stash_search[location_id] = now
    
    # Гарантированное золото
    gold = random.randint(
        stash.get('guaranteed', {}).get('gold_min', 5),
        stash.get('guaranteed', {}).get('gold_max', 15)
    )
    character.gold += gold
    
    result_text = f"🔍 *{stash.get('name', 'Тайник')}*\n\n"
    result_text += f"💰 +{gold} золота\n"
    
    # Обычные предметы
    for item_data in stash.get('items', []):
        if random.randint(1, 100) <= item_data['chance']:
            amount = random.randint(item_data['amount_min'], item_data['amount_max'])
            character.add_item(item_data['item'], amount)
            item_name = items_data.get("items", {}).get(item_data['item'], {}).get('name', item_data['item'])
            emoji = items_data.get("items", {}).get(item_data['item'], {}).get('emoji', '📦')
            result_text += f"📦 {emoji} {item_name} x{amount}\n"
    
    # Редкие предметы
    for item_data in stash.get('rare_items', []):
        if random.randint(1, 100) <= item_data['chance']:
            amount = random.randint(item_data['amount_min'], item_data['amount_max'])
            character.add_item(item_data['item'], amount)
            item_name = items_data.get("items", {}).get(item_data['item'], {}).get('name', item_data['item'])
            emoji = items_data.get("items", {}).get(item_data['item'], {}).get('emoji', '✨')
            result_text += f"✨ {emoji} {item_name} x{amount} (редко!)\n"
    
    from main import save_character
    save_character(character)
    
    bot.send_message(call.message.chat.id, result_text, parse_mode='Markdown')

# ========== КОПКА ЧЕРВЕЙ ==========

def dig_worms_action(call, bot, get_or_create_player_func):
    """Копка червей на берегу озера (10 сек, 1-7 червей)"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверка энергии
    if character.energy < 1:
        bot.answer_callback_query(call.id, "❌ Нужна энергия для копки!", show_alert=True)
        return
    
    # Проверка кулдауна (10 минут)
    now = int(time.time())
    last_dig = character.last_worm_dig or 0
    cooldown = 600  # 10 минут
    
    if now - last_dig < cooldown:
        remaining = cooldown - (now - last_dig)
        minutes = remaining // 60
        seconds = remaining % 60
        bot.answer_callback_query(
            call.id, 
            f"⏳ Земля ещё не восстановилась. Подожди {minutes} мин {seconds} сек.",
            show_alert=True
        )
        return
    
    # Тратим энергию
    character.energy -= 1
    
    # Анимация копки
    bot.answer_callback_query(call.id, "⏳ Копаю червей... 10 секунд")
    
    # Ждём 10 секунд
    time.sleep(10)
    
    # Случайное количество червей (1-7)
    worms = random.randint(1, 7)
    
    # Добавляем червей в инвентарь
    for _ in range(worms):
        character.add_item("worm")
    
    character.last_worm_dig = now
    
    # Опыт за копку
    exp_gain = worms * 2
    character.experience += exp_gain
    
    from main import save_character
    save_character(character)
    
    bot.send_message(
        call.message.chat.id,
        f"🪱 *Копка червей!*\n\n"
        f"Найдено червей: {worms} 🪱\n"
        f"✨ +{exp_gain} опыта\n\n"
        f"📌 Следующая копка через 10 минут",
        parse_mode='Markdown'
    )

# ========== ЛОКАЦИИ И ПЕРЕМЕЩЕНИЕ ==========

def location_command(message, bot, get_or_create_player_func, locations_data, items_data=None):
    """Команда /location - текущая локация"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    location_id = character.location or "start"
    location = locations_data.get("locations", {}).get(location_id, {})
    
    if not location:
        location = {"name": "Неизвестно", "description": "Локация не найдена"}
    
    # Получаем список выполненных одноразовых действий
    one_time_actions = character.one_time_actions or []
    
    # Проверяем, рыночная ли это площадь
    if location_id == "market_square":
        text = "🏪 *Рыночная площадь*\n\n"
        text += "Оживлённое место, где кипит торговля. Здесь можно найти:\n"
        text += "├ 🛡️ Оружейник - продаёт оружие и броню\n"
        text += "├ 🧪 Алхимик - торгует зельями и ингредиентами\n"
        text += "├ 🍖 Мясник - покупает мясо и шкуры\n"
        text += "├ 🎣 Рыбак - покупает рыбу\n"
        text += "└ 🏠 Риэлтор - продаёт дома\n\n"
        text += "Подойди к любому торговцу!"
        
        # Показываем фотографию рыночной площади
        try:
            with open('bot/data/images/market_square.jpeg', 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=text, parse_mode='Markdown')
        except:
            # Если фото не найдено, отправляем просто текст
            bot.send_message(message.chat.id, text, parse_mode='Markdown')
        
        # Создаём клавиатуру с торговцами
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🛡️ Оружейник", callback_data="shop:open:weaponsmith"),
            InlineKeyboardButton("🧪 Алхимик", callback_data="shop:open:alchemist"),
            InlineKeyboardButton("🍖 Мясник", callback_data="shop:open:butcher"),
            InlineKeyboardButton("🎣 Рыбак", callback_data="shop:open:fisherman"),
            InlineKeyboardButton("🏠 Риэлтор", callback_data="shop:open:realtor"),
            InlineKeyboardButton("🔙 Назад", callback_data="start:menu")
        )
        bot.send_message(message.chat.id, "Выбери торговца:", reply_markup=keyboard)
        return
    
    # Проверяем, есть ли здесь привал
    rest_spot = RESPOT_SPOTS.get(location_id)
    
    text = f"📍 *{location.get('name', 'Локация')}*\n\n"
    text += location.get('description', 'Описание отсутствует')
    
    # Добавляем информацию о привале, если есть
    if rest_spot:
        text += f"\n\n⛺ *{rest_spot['name']}*\n"
        text += f"├ {rest_spot['description']}\n"
        text += f"├ +{rest_spot['energy_gain']}⚡"
        if rest_spot.get('health_gain'):
            text += f", +{rest_spot['health_gain']}❤️"
        if rest_spot.get('magic_gain'):
            text += f", +{rest_spot['magic_gain']}🔮"
        text += f"\n└ ⏱️ Перезарядка: {rest_spot['cooldown']//3600} ч"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    actions_added = 0
    
    # Добавляем кнопку привала, если есть
    if rest_spot:
        now = int(time.time())
        last_rest = character.last_rest_time or 0
        
        if now - last_rest < rest_spot['cooldown']:
            remaining = rest_spot['cooldown'] - (now - last_rest)
            minutes = remaining // 60
            keyboard.add(InlineKeyboardButton(
                f"⏳ {rest_spot['name']} (ждём {minutes} мин)",
                callback_data="game:rest_cooldown"
            ))
        else:
            keyboard.add(InlineKeyboardButton(
                f"⛺ Отдохнуть на {rest_spot['name']}",
                callback_data=f"game:rest_spot:{location_id}"
            ))
        actions_added += 1
    
    # Добавляем кнопку поиска тайника, если есть
    stash = location.get('hidden_stash', {})
    if stash:
        now = int(time.time())
        last_search = character.last_stash_search.get(location_id, 0) if hasattr(character, 'last_stash_search') else 0
        cooldown = stash.get('cooldown', 3600)
        
        if now - last_search < cooldown:
            remaining = cooldown - (now - last_search)
            minutes = remaining // 60
            keyboard.add(InlineKeyboardButton(
                f"⏳ {stash['name']} (ждём {minutes} мин)",
                callback_data="game:stash_cooldown"
            ))
        else:
            keyboard.add(InlineKeyboardButton(
                f"🔍 Искать в {stash['name']}",
                callback_data=f"game:search_stash:{location_id}"
            ))
        actions_added += 1
    
    # Специальная кнопка для копки червей на берегу озера
    if location_id == "lake_shore":
        keyboard.add(InlineKeyboardButton(
            "🪱 Копать червей (10 сек, 1-7🪱)",
            callback_data="game:dig_worms"
        ))
        actions_added += 1
    
    # Стандартные действия из локации
    actions = location.get('actions', [])
    for action in actions:
        # Пропускаем уже выполненные одноразовые действия
        if action.get('one_time') and action['text'] in one_time_actions:
            continue
        
        if action['type'] == 'move':
            level_req = action.get('level_req', 1)
            if character.level >= level_req:
                energy_cost = action.get('energy_cost', 1)
                if character.energy >= energy_cost:
                    keyboard.add(InlineKeyboardButton(
                        action['text'],
                        callback_data=f"game:move_to:{action['next']}"
                    ))
                    actions_added += 1
                else:
                    keyboard.add(InlineKeyboardButton(
                        f"❌ {action['text']} (нужно {energy_cost}⚡)",
                        callback_data="game:no_energy"
                    ))
                    actions_added += 1
        elif action['type'] == 'take_item':
            # Действие с подбором предмета
            keyboard.add(InlineKeyboardButton(
                action['text'],
                callback_data=f"game:take_item:{action['item']}"
            ))
            actions_added += 1
        elif action['type'] == 'hunt':
            if character.energy >= 5:
                keyboard.add(InlineKeyboardButton(
                    action['text'],
                    callback_data="game:hunt"
                ))
                actions_added += 1
        elif action['type'] == 'rest':
            # Это обычный отдых из локации, не привал
            if character.energy < character.max_energy:
                keyboard.add(InlineKeyboardButton(
                    action['text'],
                    callback_data="game:rest_local"
                ))
                actions_added += 1
        elif action['type'] == 'open_shop':
            keyboard.add(InlineKeyboardButton(
                action['text'],
                callback_data=f"shop:open:{action['shop']}"
            ))
            actions_added += 1
        elif action['type'] == 'craft':
            keyboard.add(InlineKeyboardButton(
                action['text'],
                callback_data=f"craft:{action.get('category', 'menu')}"
            ))
            actions_added += 1
        elif action['type'] == 'fish':
            if character.energy >= 2:
                keyboard.add(InlineKeyboardButton(
                    action['text'],
                    callback_data="game:fish"
                ))
                actions_added += 1
        elif action['type'] == 'gather':
            if character.energy >= 2:
                keyboard.add(InlineKeyboardButton(
                    action['text'],
                    callback_data="game:gather"
                ))
                actions_added += 1
        elif action['type'] == 'mine':
            if character.energy >= 2:
                keyboard.add(InlineKeyboardButton(
                    action['text'],
                    callback_data="game:mine"
                ))
                actions_added += 1
        elif action['type'] == 'special_craft':
            keyboard.add(InlineKeyboardButton(
                action['text'],
                callback_data=f"craft:special:{action['recipe']}"
            ))
            actions_added += 1
    
    # Добавляем кнопку карты
    if actions_added < 4:
        keyboard.add(InlineKeyboardButton("🗺️ Карта", callback_data="game:map"))
    else:
        keyboard.row(InlineKeyboardButton("🗺️ Карта", callback_data="game:map"))
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

def map_command(message, bot):
    """Отправляет интерактивную HTML-карту"""
    
    # Пробуем загрузить HTML-карту
    map_path = 'bot/data/map.html'
    if os.path.exists(map_path):
        try:
            with open(map_path, 'r', encoding='utf-8') as file:
                map_html = file.read()
            
            # Сохраняем во временный файл и отправляем
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(map_html)
                temp_path = f.name
            
            with open(temp_path, 'rb') as file:
                bot.send_document(
                    message.chat.id,
                    file,
                    caption="🗺️ *Карта мира Destiny*\n\n"
                            "1. Скачай файл\n"
                            "2. Открой в браузере\n"
                            "3. Нажимай на иконки локаций!\n\n"
                            "📱 На телефоне файл откроется автоматически",
                    parse_mode='Markdown'
                )
            
            # Удаляем временный файл
            os.unlink(temp_path)
            return
        except Exception as e:
            logger.error(f"Ошибка отправки HTML-карты: {e}")
    
    # Если HTML не работает, отправляем текстовую карту
    text = "🗺️ *Карта мира Destiny*\n\n"
    
    text += "🏘️ **Деревня:**\n"
    text += "├ 🏪 Рыночная площадь (ур. 1+)\n"
    text += "├ 🍺 Таверна (ур. 1+)\n"
    text += "├ ⚒️ Кузница (ур. 5+)\n"
    text += "├ 🔮 Башня мага (ур. 10+)\n\n"
    
    text += "🌲 **Лесные зоны:**\n"
    text += "├ 🌲 Лесная опушка (ур. 1-5)\n"
    text += "├ 🌿 Лесная тропа (ур. 2+)\n"
    text += "├ 🛤️ Лесная развилка (ур. 3+)\n"
    text += "├ 🌳 Глухой лес (ур. 2+)\n"
    text += "├ 🏞️ Берег озера (ур. 3+) *⛺ Привал*\n\n"
    
    text += "⛰️ **Горные зоны:**\n"
    text += "├ ⛰️ Горная тропа (ур. 10+) *⛺ Привал*\n"
    text += "├ ⛏️ Вход в шахту (ур. 15+)\n"
    text += "├ 🏔️ Горная вершина (ур. 12+)\n"
    text += "├ 🌋 Тропа к вулкану (ур. 25+) *⛺ Привал*\n"
    text += "├ 🌋 Жерло вулкана (ур. 28+)\n"
    text += "├ 🏖️ Вулканический пляж (ур. 25+)\n\n"
    
    text += "🏜️ **Пустыня:**\n"
    text += "├ 🏜️ Пустыня забвения (ур. 30+)\n"
    text += "├ 🏝️ Оазис (ур. 30+) *⛺ Привал*\n\n"
    
    text += "🌿 **Болото:**\n"
    text += "├ 🌿 Болото туманов (ур. 35+)\n"
    text += "├ 🏚️ Хижина ведьмы (ур. 35+) *⛺ Привал*\n\n"
    
    text += "❄️ **Ледяные земли:**\n"
    text += "├ ❄️ Ледяные равнины (ур. 40+)\n"
    text += "├ 🧊 Ледяная пещера (ур. 42+) *⛺ Привал*\n"
    text += "├ 🌊 Замёрзший океан (ур. 40+)\n\n"
    
    text += "🏛️ **Подземелья:**\n"
    text += "├ ⛏️ Шахта (5 уровней, ур. 15-30)\n"
    text += "├ 🏛️ Древние руины (ур. 35+)\n"
    text += "├ 🌉 Мост перед драконом (ур. 40+) *⛺ Привал*\n"
    text += "├ 🐉 Логово дракона (ур. 50+)\n\n"
    
    text += "🏝️ **Острова:**\n"
    text += "├ ⚓ Гавань островов (ур. 30+)\n"
    text += "├ 🌋 Огненный остров (ур. 45+, 3🌈)\n"
    text += "├ 💎 Кристальный остров (ур. 50+, 1💎) *⛺ Привал*\n"
    text += "├ 🐉 Остров драконов (ур. 55+, 5💎) *⛺ Привал*\n\n"
    
    text += "⛺ *Привалы* - места для отдыха с особыми бонусами (перезарядка 1-2ч)"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📍 Текущая локация", callback_data="game:location"),
        InlineKeyboardButton("🚶 Переместиться", callback_data="game:move"),
        InlineKeyboardButton("🔙 Назад", callback_data="start:menu")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

def move_command(message, bot, get_or_create_player_func, locations_data):
    """Команда /move - перемещение между локациями"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    current_location = character.location or "start"
    all_locations = locations_data.get("locations", {})
    current_loc_data = all_locations.get(current_location, {})
    
    text = f"🗺️ *Куда отправимся?*\n\n"
    text += f"📍 Текущая локация: {current_loc_data.get('name', 'Неизвестно')}\n\n"
    text += "🎯 *Доступные локации:*\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    locations_found = 0
    
    # Группируем по категориям
    village_locs = []
    forest_locs = []
    mountain_locs = []
    desert_locs = []
    swamp_locs = []
    ice_locs = []
    island_locs = []
    dungeon_locs = []
    
    for loc_id, loc_data in all_locations.items():
        if loc_id != current_location:
            level_req = loc_data.get('level_req', 1)
            if character.level >= level_req:
                name = loc_data.get('name', loc_id)
                has_rest = "⛺" if loc_id in RESPOT_SPOTS else ""
                
                if "дерев" in name.lower() or "площадь" in name.lower() or "таверн" in name.lower() or "рыночн" in name.lower() or "кузниц" in name.lower() or "башн" in name.lower():
                    village_locs.append((loc_id, f"{has_rest} {name}" if has_rest else name))
                elif "лес" in name.lower() or "троп" in name.lower() or "развил" in name.lower() or "озер" in name.lower():
                    forest_locs.append((loc_id, f"{has_rest} {name}" if has_rest else name))
                elif "гор" in name.lower() or "шахт" in name.lower() or "вершин" in name.lower():
                    mountain_locs.append((loc_id, f"{has_rest} {name}" if has_rest else name))
                elif "пустын" in name.lower() or "оазис" in name.lower():
                    desert_locs.append((loc_id, f"{has_rest} {name}" if has_rest else name))
                elif "болот" in name.lower() or "хижин" in name.lower():
                    swamp_locs.append((loc_id, f"{has_rest} {name}" if has_rest else name))
                elif "лед" in name.lower() or "снеж" in name.lower() or "мороз" in name.lower() or "замёрз" in name.lower():
                    ice_locs.append((loc_id, f"{has_rest} {name}" if has_rest else name))
                elif "остров" in name.lower() or "гаван" in name.lower():
                    island_locs.append((loc_id, f"{has_rest} {name}" if has_rest else name))
                elif "руин" in name.lower() or "мост" in name.lower() or "логов" in name.lower() or "шахт" in name.lower():
                    dungeon_locs.append((loc_id, f"{has_rest} {name}" if has_rest else name))
    
    if village_locs:
        text += "🏘️ *Деревня:*\n"
        for loc_id, name in village_locs:
            text += f"├ {name}\n"
            clean_id = loc_id.split()[0] if '⛺' in name else loc_id
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{clean_id}"))
            locations_found += 1
        text += "\n"
    
    if forest_locs:
        text += "🌲 *Лес:*\n"
        for loc_id, name in forest_locs:
            text += f"├ {name}\n"
            clean_id = loc_id.split()[0] if '⛺' in name else loc_id
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{clean_id}"))
            locations_found += 1
        text += "\n"
    
    if mountain_locs:
        text += "⛰️ *Горы:*\n"
        for loc_id, name in mountain_locs:
            text += f"├ {name}\n"
            clean_id = loc_id.split()[0] if '⛺' in name else loc_id
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{clean_id}"))
            locations_found += 1
        text += "\n"
    
    if desert_locs:
        text += "🏜️ *Пустыня:*\n"
        for loc_id, name in desert_locs:
            text += f"├ {name}\n"
            clean_id = loc_id.split()[0] if '⛺' in name else loc_id
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{clean_id}"))
            locations_found += 1
        text += "\n"
    
    if swamp_locs:
        text += "🌿 *Болото:*\n"
        for loc_id, name in swamp_locs:
            text += f"├ {name}\n"
            clean_id = loc_id.split()[0] if '⛺' in name else loc_id
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{clean_id}"))
            locations_found += 1
        text += "\n"
    
    if ice_locs:
        text += "❄️ *Ледяные земли:*\n"
        for loc_id, name in ice_locs:
            text += f"├ {name}\n"
            clean_id = loc_id.split()[0] if '⛺' in name else loc_id
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{clean_id}"))
            locations_found += 1
        text += "\n"
    
    if island_locs:
        text += "🏝️ *Острова:*\n"
        for loc_id, name in island_locs:
            text += f"├ {name}\n"
            clean_id = loc_id.split()[0] if '⛺' in name else loc_id
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{clean_id}"))
            locations_found += 1
        text += "\n"
    
    if dungeon_locs:
        text += "🏛️ *Подземелья:*\n"
        for loc_id, name in dungeon_locs:
            text += f"├ {name}\n"
            clean_id = loc_id.split()[0] if '⛺' in name else loc_id
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{clean_id}"))
            locations_found += 1
        text += "\n"
    
    if locations_found == 0:
        text += "❌ Нет доступных локаций для перемещения."
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="game:location"))
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

def move_to_location(call, bot, get_or_create_player_func, locations_data):
    """Обработчик перемещения в локацию"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
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
        bot.answer_callback_query(call.id, f"❌ Нужен уровень {level_req}!", show_alert=True)
        return
    
    # Проверяем стоимость входа (радужные осколки/камни)
    entry_cost = location.get('entry_cost', {})
    if entry_cost:
        if 'rainbow_shard' in entry_cost:
            cost = entry_cost['rainbow_shard']
            if (character.rainbow_shards or 0) < cost:
                bot.answer_callback_query(call.id, f"❌ Нужно {cost} радужных осколков!", show_alert=True)
                return
            character.rainbow_shards = (character.rainbow_shards or 0) - cost
        if 'rainbow_stone' in entry_cost:
            cost = entry_cost['rainbow_stone']
            if (character.rainbow_stones or 0) < cost:
                bot.answer_callback_query(call.id, f"❌ Нужно {cost} радужных камней!", show_alert=True)
                return
            character.rainbow_stones = (character.rainbow_stones or 0) - cost
    
    # Проверяем энергию
    energy_cost = 1
    if character.energy < energy_cost:
        bot.answer_callback_query(call.id, "❌ Нет энергии!", show_alert=True)
        return
    
    character.energy -= energy_cost
    character.location = new_location
    from main import save_character
    save_character(character)
    
    bot.answer_callback_query(call.id, f"✅ Перемещён")
    location_command(call.message, bot, get_or_create_player_func, locations_data)

# ========== ОТДЫХ НА ПРИВАЛАХ ==========

def rest_spot_action(call, bot, get_or_create_player_func):
    """Обработчик отдыха на привале"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    parts = call.data.split(':')
    if len(parts) >= 3:
        location_id = parts[2]
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка")
        return
    
    rest_spot = RESPOT_SPOTS.get(location_id)
    if not rest_spot:
        bot.answer_callback_query(call.id, "❌ Привал не найден")
        return
    
    # Проверяем кулдаун
    now = int(time.time())
    last_rest = character.last_rest_time or 0
    cooldown = rest_spot['cooldown']
    
    if now - last_rest < cooldown:
        remaining = cooldown - (now - last_rest)
        minutes = remaining // 60
        bot.answer_callback_query(call.id, f"⏳ Отдых ещё не доступен. Подожди {minutes} мин.", show_alert=True)
        return
    
    # Применяем бонусы
    energy_gain = rest_spot.get('energy_gain', 20)
    health_gain = rest_spot.get('health_gain', 0)
    magic_gain = rest_spot.get('magic_gain', 0)
    
    character.energy = min(character.energy + energy_gain, character.max_energy)
    character.health = min(character.health + health_gain, character.max_health)
    character.mana = min(character.mana + magic_gain, character.max_mana)
    character.last_rest_time = now
    
    # Проверяем особые действия на привале
    special_action = rest_spot.get('special_action')
    if special_action:
        # Проверяем, есть ли ингредиенты
        has_all = True
        missing = []
        for item, amount in special_action['ingredients'].items():
            if not character.has_item(item, amount):
                has_all = False
                missing.append(f"{item} x{amount}")
        
        if has_all:
            # Тратим ингредиенты
            for item, amount in special_action['ingredients'].items():
                character.remove_item(item, amount)
            
            # Даём результат
            if 'achievement' in special_action:
                if not hasattr(character, 'achievements'):
                    character.achievements = []
                if special_action['achievement'] not in character.achievements:
                    character.achievements.append(special_action['achievement'])
            
            if 'result' in special_action:
                character.add_item(special_action['result'])
                
            bot.send_message(
                call.message.chat.id,
                f"✨ *Особое событие на привале!*\n\n{special_action['description']}\n\n✅ Выполнено!",
                parse_mode='Markdown'
            )
    
    from main import save_character
    save_character(character)
    
    # Пытаемся отправить картинку привала
    try:
        with open(f'bot/data/images/{rest_spot["image"]}', 'rb') as photo:
            bot.send_photo(
                call.message.chat.id,
                photo,
                caption=f"✅ *Отдохнул на {rest_spot['name']}!*\n\n+{energy_gain}⚡ энергии\n+{health_gain}❤️ здоровья\n+{magic_gain}🔮 маны",
                parse_mode='Markdown'
            )
    except:
        bot.send_message(
            call.message.chat.id,
            f"✅ *Отдохнул на {rest_spot['name']}!*\n\n+{energy_gain}⚡ энергии\n+{health_gain}❤️ здоровья\n+{magic_gain}🔮 маны",
            parse_mode='Markdown'
        )
    
    # Показываем доступные пути с привала
    if rest_spot.get('connections'):
        text = "🗺️ *С привала можно пойти:*\n\n"
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        from main import locations_data
        for conn_id in rest_spot['connections']:
            conn_loc = locations_data.get("locations", {}).get(conn_id, {})
            if conn_loc:
                text += f"├ {conn_loc.get('name', conn_id)}\n"
                keyboard.add(InlineKeyboardButton(
                    f"➡️ {conn_loc.get('name', conn_id)}",
                    callback_data=f"game:move_to:{conn_id}"
                ))
        
        keyboard.add(InlineKeyboardButton("🔙 Остаться здесь", callback_data="game:location"))
        bot.send_message(call.message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

# ========== ДЕЙСТВИЯ ==========

def hunt_action(call, bot, get_or_create_player_func, locations_data, enemies_data, items_data):
    """Обработчик охоты с новыми процентами:
    40% - взрослое животное (шкура + мясо)
    15% - тайник (hidden_stash из локации)
    20% - детёныш (при атаке призовёт мать)
    25% - горсть монет
    """
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверка энергии
    if character.energy < 5:
        bot.answer_callback_query(call.id, "❌ Нужно 5⚡ энергии для охоты!", show_alert=True)
        return
    
    # Тратим энергию
    character.energy -= 5
    from main import save_character
    save_character(character)
    
    # Анимация охоты
    bot.answer_callback_query(call.id, "🏹 Выслеживаю добычу...")
    
    # Определяем результат (сумма = 100%)
    roll = random.randint(1, 100)
    
    exp_gain = random.randint(15, 30)
    character.experience += exp_gain
    character.kills_total = (character.kills_total or 0) + 1
    
    result_text = f"🏹 *Охота*\n\n"
    
    if roll <= 40:  # 40% - взрослое животное
        # Выбираем случайное взрослое животное из локации
        location_id = character.location or "start"
        location = locations_data.get("locations", {}).get(location_id, {})
        
        possible_enemies = []
        for enemy_id in location.get('enemies', []):
            enemy = enemies_data.get("enemies", {}).get(enemy_id, {})
            # Выбираем только взрослых (не детёнышей)
            if enemy.get('gender') in ['male', 'female'] and enemy.get('type') != 'group':
                possible_enemies.append(enemy)
        
        if possible_enemies:
            enemy = random.choice(possible_enemies)
            
            # Собираем дроп
            drops = []
            for drop in enemy.get('drops', []):
                if random.randint(1, 100) <= drop['chance']:
                    amount = random.randint(drop['min'], drop['max'])
                    character.add_item(drop['item'], amount)
                    item_name = items_data.get("items", {}).get(drop['item'], {}).get('emoji', '📦')
                    drops.append(f"{item_name} x{amount}")
            
            result_text += f"🐺 Ты выследил {enemy.get('name', 'зверя')}!\n"
            result_text += f"📦 Добыча: {', '.join(drops) if drops else 'ничего'}\n"
        else:
            # Если врагов нет, даём монеты
            gold = random.randint(20, 40)
            character.gold += gold
            result_text += f"💰 Ты нашёл горсть монет: +{gold} золота\n"
    
    elif roll <= 55:  # 15% - тайник
        location_id = character.location or "start"
        location = locations_data.get("locations", {}).get(location_id, {})
        stash = location.get('hidden_stash', {})
        
        if stash:
            gold = random.randint(
                stash.get('guaranteed', {}).get('gold_min', 5),
                stash.get('guaranteed', {}).get('gold_max', 15)
            )
            character.gold += gold
            
            result_text += f"🔍 Ты нашёл {stash.get('name', 'тайник')}!\n"
            result_text += f"💰 +{gold} золота\n"
            
            # Шанс найти предметы из тайника
            for item_data in stash.get('items', []):
                if random.randint(1, 100) <= item_data['chance']:
                    amount = random.randint(item_data['amount_min'], item_data['amount_max'])
                    character.add_item(item_data['item'], amount)
                    item_name = items_data.get("items", {}).get(item_data['item'], {}).get('emoji', '📦')
                    result_text += f"📦 Найдено: {item_name} x{amount}\n"
            
            # Шанс найти редкие предметы
            for item_data in stash.get('rare_items', []):
                if random.randint(1, 100) <= item_data['chance']:
                    amount = random.randint(item_data['amount_min'], item_data['amount_max'])
                    character.add_item(item_data['item'], amount)
                    item_name = items_data.get("items", {}).get(item_data['item'], {}).get('emoji', '📦')
                    result_text += f"✨ Найдено редкое: {item_name} x{amount}\n"
        else:
            # Если тайника нет, даём монеты
            gold = random.randint(15, 30)
            character.gold += gold
            result_text += f"💰 Ты нашёл горсть монет: +{gold} золота\n"
    
    elif roll <= 75:  # 20% - детёныш
        # Определяем тип детёныша в зависимости от локации
        location_id = character.location or "start"
        
        # Маппинг локаций на возможных детёнышей
        cub_types = {
            "deep_forest": ["wolf_cub", "boar_piglet", "bear_cub"],
            "forest_path": ["moose_calf"],
            "mountain_path": ["bear_cub"],
            "desert": ["scorpion_hatchling"],
            "swamp": ["frog_cub", "snake_cub"],
            "ice_plains": ["ice_wolf_cub", "white_bear_cub"],
            "volcanic_beach": ["crab_cub"],
            "frozen_ocean": ["seal_cub", "walrus_cub"],
            "mine_level1": ["giant_rat_cub"],
            "mine_level2": ["cave_spider_cub"],
            "mine_level3": ["cave_spider_cub"]
        }
        
        possible_cubs = cub_types.get(location_id, ["wolf_cub"])
        cub_id = random.choice(possible_cubs)
        
        # Ищем в бестиарии
        cub = enemies_data.get("enemies", {}).get(cub_id, {})
        
        result_text += f"🐾 Ты нашёл {cub.get('name', 'детёныша')}!\n"
        result_text += f"⚔️ *ВНИМАНИЕ!* При атаке он призовёт мать!\n"
        result_text += f"📖 {cub.get('lore', 'Маленький и беззащитный... но мама рядом.')}\n\n"
        
        # Проверяем, можно ли приручить
        can_be_tamed = cub.get('can_be_tamed', False)
        
        # Создаём клавиатуру для выбора
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("⚔️ Атаковать", callback_data=f"combat:attack:{cub_id}"),
            InlineKeyboardButton("🏃 Отпустить", callback_data="game:location")
        )
        
        if can_be_tamed:
            tame_item = cub.get('tame_item', 'мясо')
            tame_chance = cub.get('tame_chance', 30)
            keyboard.add(InlineKeyboardButton(
                f"🪤 Приручить ({tame_chance}%, нужен {tame_item})",
                callback_data=f"pet:tame:{cub_id}"
            ))
        
        bot.send_message(call.message.chat.id, result_text, reply_markup=keyboard, parse_mode='Markdown')
        return
    
    else:  # 25% - горсть монет
        gold = random.randint(20, 50)
        character.gold += gold
        result_text += f"💰 Ты нашёл горсть монет: +{gold} золота\n"
    
    result_text += f"\n✨ +{exp_gain} опыта"
    
    from main import save_character
    save_character(character)
    bot.send_message(call.message.chat.id, result_text, parse_mode='Markdown')

def fish_action(call, bot, get_or_create_player_func, items_data):
    """Обработчик рыбалки с кулдауном и затратами энергии"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверка энергии
    if character.energy < 2:
        bot.answer_callback_query(call.id, "❌ Нужно 2⚡ энергии для рыбалки!", show_alert=True)
        return
    
    # Проверка кулдауна (30 минут)
    now = int(time.time())
    last_fish = character.last_fish_time or 0
    cooldown = 1800  # 30 минут
    
    if now - last_fish < cooldown:
        remaining = cooldown - (now - last_fish)
        minutes = remaining // 60
        seconds = remaining % 60
        bot.answer_callback_query(call.id, f"⏳ Рыбалка ещё не доступна. Подожди {minutes} мин {seconds} сек.", show_alert=True)
        return
    
    # Тратим энергию
    character.energy -= 2
    character.last_fish_time = now
    
    # Определяем биом для разной рыбы
    location_id = character.location or "start"
    
    fish_types = {
        "lake_shore": [
            {"id": "fish", "name": "🐟 Обычная рыба", "chance": 70, "min": 1, "max": 3, "exp": 10},
            {"id": "pike", "name": "🐟 Щука", "chance": 20, "min": 1, "max": 1, "exp": 20},
            {"id": "carp", "name": "🐟 Карп", "chance": 10, "min": 1, "max": 1, "exp": 25}
        ],
        "frozen_ocean": [
            {"id": "frozen_fish", "name": "🐟 Ледяная рыба", "chance": 60, "min": 1, "max": 2, "exp": 15},
            {"id": "salmon", "name": "🐟 Лосось", "chance": 30, "min": 1, "max": 1, "exp": 25},
            {"id": "ice_fish", "name": "❄️ Ледяная форель", "chance": 10, "min": 1, "max": 1, "exp": 35}
        ],
        "volcanic_beach": [
            {"id": "tropical_fish", "name": "🐠 Тропическая рыбка", "chance": 50, "min": 1, "max": 3, "exp": 12},
            {"id": "crab", "name": "🦀 Краб", "chance": 30, "min": 1, "max": 2, "exp": 18},
            {"id": "lobster", "name": "🦞 Лобстер", "chance": 20, "min": 1, "max": 1, "exp": 30}
        ],
        "swamp": [
            {"id": "catfish", "name": "🐟 Сом", "chance": 50, "min": 1, "max": 2, "exp": 15},
            {"id": "frog_legs", "name": "🐸 Лягушачьи лапки", "chance": 40, "min": 1, "max": 2, "exp": 10},
            {"id": "eel", "name": "🐍 Угорь", "chance": 10, "min": 1, "max": 1, "exp": 25}
        ]
    }
    
    # Выбираем рыбу для текущей локации
    fish_pool = fish_types.get(location_id, fish_types["lake_shore"])
    
    # Случайный результат
    roll = random.randint(1, 100)
    cumulative = 0
    caught_fish = None
    
    for fish in fish_pool:
        cumulative += fish['chance']
        if roll <= cumulative:
            caught_fish = fish
            break
    
    if not caught_fish:
        caught_fish = fish_pool[-1]
    
    # Количество рыбы
    amount = random.randint(caught_fish['min'], caught_fish['max'])
    
    # Добавляем в инвентарь
    for _ in range(amount):
        character.add_item(caught_fish['id'])
    
    # Опыт
    exp_gain = caught_fish['exp'] * amount
    character.experience += exp_gain
    
    # Шанс найти сокровище (5%)
    treasure_found = None
    if random.random() < 0.05:
        if location_id == "frozen_ocean":
            treasure_found = "ancient_coin"
            character.add_item("ancient_coin")
        elif location_id == "volcanic_beach":
            treasure_found = "pearl"
            character.add_item("pearl")
        elif location_id == "lake_shore":
            treasure_found = "old_boot"
            character.add_item("old_boot")
    
    from main import save_character
    save_character(character)
    
    result_text = f"🎣 *Рыбалка!*\n\n"
    result_text += f"🐟 Поймано: {caught_fish['name']} x{amount}\n"
    result_text += f"✨ +{exp_gain} опыта\n"
    
    if treasure_found:
        item_name = items_data.get("items", {}).get(treasure_found, {}).get('emoji', '📦')
        result_text += f"✨ Найдено сокровище: {item_name}\n"
    
    bot.send_message(call.message.chat.id, result_text, parse_mode='Markdown')

def gather_action(call, bot, get_or_create_player_func, items_data):
    """Обработчик сбора трав с кулдауном и затратами энергии"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверка энергии
    if character.energy < 2:
        bot.answer_callback_query(call.id, "❌ Нужно 2⚡ энергии для сбора!", show_alert=True)
        return
    
    # Проверка кулдауна (30 минут)
    now = int(time.time())
    last_gather = character.last_gather_time or 0
    cooldown = 1800  # 30 минут
    
    if now - last_gather < cooldown:
        remaining = cooldown - (now - last_gather)
        minutes = remaining // 60
        bot.answer_callback_query(call.id, f"⏳ Сбор ещё не доступен. Подожди {minutes} мин.", show_alert=True)
        return
    
    # Тратим энергию
    character.energy -= 2
    character.last_gather_time = now
    
    # Определяем биом для разных трав
    location_id = character.location or "start"
    
    herb_types = {
        "deep_forest": [
            {"id": "herb", "name": "🌿 Обычная трава", "chance": 80, "min": 2, "max": 5, "exp": 8},
            {"id": "berry", "name": "🫐 Лесная ягода", "chance": 60, "min": 1, "max": 3, "exp": 5},
            {"id": "mushroom", "name": "🍄 Гриб", "chance": 40, "min": 1, "max": 2, "exp": 10},
            {"id": "magic_herb", "name": "✨ Магическая трава", "chance": 10, "min": 1, "max": 1, "exp": 25}
        ],
        "mountain_path": [
            {"id": "herb", "name": "🌿 Горная трава", "chance": 70, "min": 1, "max": 3, "exp": 10},
            {"id": "edelweiss", "name": "🏔️ Эдельвейс", "chance": 30, "min": 1, "max": 1, "exp": 20},
            {"id": "mountain_herb", "name": "⛰️ Альпийская трава", "chance": 15, "min": 1, "max": 1, "exp": 25}
        ],
        "desert": [
            {"id": "cactus_fruit", "name": "🌵 Плод кактуса", "chance": 70, "min": 1, "max": 2, "exp": 12},
            {"id": "desert_herb", "name": "🏜️ Пустынная трава", "chance": 40, "min": 1, "max": 2, "exp": 15},
            {"id": "desert_rose", "name": "🌹 Роза пустыни", "chance": 5, "min": 1, "max": 1, "exp": 40}
        ],
        "swamp": [
            {"id": "swamp_herb", "name": "🌿 Болотная трава", "chance": 70, "min": 2, "max": 4, "exp": 10},
            {"id": "mushroom", "name": "🍄 Болотный гриб", "chance": 50, "min": 1, "max": 2, "exp": 12},
            {"id": "glowing_mushroom", "name": "✨ Светящийся гриб", "chance": 10, "min": 1, "max": 1, "exp": 30}
        ],
        "ice_plains": [
            {"id": "ice_herb", "name": "❄️ Ледяная трава", "chance": 60, "min": 1, "max": 2, "exp": 15},
            {"id": "frost_flower", "name": "🧊 Морозный цветок", "chance": 30, "min": 1, "max": 1, "exp": 25},
            {"id": "eternal_ice", "name": "💎 Вечная мерзлота", "chance": 5, "min": 1, "max": 1, "exp": 50}
        ]
    }
    
    herb_pool = herb_types.get(location_id, herb_types["deep_forest"])
    
    # Собираем травы
    collected = []
    exp_gain = 0
    
    for herb in herb_pool:
        if random.randint(1, 100) <= herb['chance']:
            amount = random.randint(herb['min'], herb['max'])
            character.add_item(herb['id'], amount)
            collected.append(f"{herb['name']} x{amount}")
            exp_gain += herb['exp'] * amount
    
    from main import save_character
    save_character(character)
    
    if collected:
        result_text = f"🌿 *Сбор трав!*\n\n"
        result_text += f"📦 Найдено:\n├ " + "\n├ ".join(collected) + "\n"
        result_text += f"\n✨ +{exp_gain} опыта"
    else:
        result_text = f"🌿 *Сбор трав!*\n\n❌ Ничего не найдено. В следующий раз повезёт!"
    
    bot.send_message(call.message.chat.id, result_text, parse_mode='Markdown')

def mine_action(call, bot, get_or_create_player_func, items_data):
    """Обработчик добычи руды с разными этажами"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверка энергии
    if character.energy < 2:
        bot.answer_callback_query(call.id, "❌ Нужно 2⚡ энергии для добычи!", show_alert=True)
        return
    
    # Проверка кулдауна (30 минут)
    now = int(time.time())
    last_mine = character.last_mine_time or 0
    cooldown = 1800  # 30 минут
    
    if now - last_mine < cooldown:
        remaining = cooldown - (now - last_mine)
        minutes = remaining // 60
        bot.answer_callback_query(call.id, f"⏳ Добыча ещё не доступна. Подожди {minutes} мин.", show_alert=True)
        return
    
    # Тратим энергию
    character.energy -= 2
    character.last_mine_time = now
    
    # Определяем руды в зависимости от уровня шахты
    location_id = character.location or "start"
    
    # Руды по этажам
    ores_by_level = {
        "mine_level1": [  # 1 уровень - медная, оловянная
            {"id": "copper_ore", "name": "🟤 Медная руда", "chance": 70, "min": 1, "max": 3, "exp": 8},
            {"id": "tin_ore", "name": "⚪ Оловянная руда", "chance": 50, "min": 1, "max": 2, "exp": 7},
            {"id": "stone", "name": "🪨 Камень", "chance": 80, "min": 1, "max": 5, "exp": 2}
        ],
        "mine_level2": [  # 2 уровень - железная, серебряная
            {"id": "iron_ore", "name": "⚫ Железная руда", "chance": 60, "min": 1, "max": 3, "exp": 12},
            {"id": "silver_ore", "name": "✨ Серебряная руда", "chance": 30, "min": 1, "max": 2, "exp": 15},
            {"id": "coal", "name": "🪨 Уголь", "chance": 50, "min": 1, "max": 4, "exp": 5}
        ],
        "mine_level3": [  # 3 уровень - золотая, кристаллы
            {"id": "gold_ore", "name": "🟡 Золотая руда", "chance": 40, "min": 1, "max": 2, "exp": 20},
            {"id": "crystal", "name": "💎 Кристалл", "chance": 30, "min": 1, "max": 2, "exp": 18},
            {"id": "ruby", "name": "🔴 Рубин", "chance": 10, "min": 1, "max": 1, "exp": 30}
        ],
        "mine_level4": [  # 4 уровень - мифриловая, платиновая
            {"id": "mythril_ore", "name": "🔷 Мифриловая руда", "chance": 30, "min": 1, "max": 2, "exp": 30},
            {"id": "platinum_ore", "name": "⚪✨ Платиновая руда", "chance": 25, "min": 1, "max": 1, "exp": 35},
            {"id": "sapphire", "name": "🔵 Сапфир", "chance": 15, "min": 1, "max": 1, "exp": 40}
        ],
        "mine_level5": [  # 5 уровень - редкие самоцветы
            {"id": "diamond", "name": "💎 Алмаз", "chance": 20, "min": 1, "max": 1, "exp": 50},
            {"id": "emerald", "name": "💚 Изумруд", "chance": 20, "min": 1, "max": 1, "exp": 45},
            {"id": "ancient_relic", "name": "🏺 Древний артефакт", "chance": 5, "min": 1, "max": 1, "exp": 100}
        ]
    }
    
    ore_pool = ores_by_level.get(location_id, ores_by_level["mine_level1"])
    
    # Добываем руду
    mined = []
    exp_gain = 0
    
    for ore in ore_pool:
        if random.randint(1, 100) <= ore['chance']:
            amount = random.randint(ore['min'], ore['max'])
            character.add_item(ore['id'], amount)
            mined.append(f"{ore['name']} x{amount}")
            exp_gain += ore['exp'] * amount
    
    from main import save_character
    save_character(character)
    
    if mined:
        result_text = f"⛏️ *Добыча руды!*\n\n"
        result_text += f"📦 Найдено:\n├ " + "\n├ ".join(mined) + "\n"
        result_text += f"\n✨ +{exp_gain} опыта"
    else:
        result_text = f"⛏️ *Добыча руды!*\n\n❌ Ничего не найдено. Только порода..."
    
    bot.send_message(call.message.chat.id, result_text, parse_mode='Markdown')

def rest_action(call, bot, get_or_create_player_func):
    """Обработчик локального отдыха (не привал)"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверяем кулдаун для локального отдыха (30 минут)
    now = int(time.time())
    last_rest = character.last_rest_time or 0
    cooldown = 1800  # 30 минут
    
    if now - last_rest < cooldown:
        remaining = cooldown - (now - last_rest)
        minutes = remaining // 60
        bot.answer_callback_query(call.id, f"⏳ Отдых ещё не доступен. Подожди {minutes} мин.", show_alert=True)
        return
    
    # Определяем бонус отдыха в зависимости от локации
    location_id = character.location or "start"
    from main import locations_data
    location = locations_data.get("locations", {}).get(location_id, {})
    rest_spot = location.get('rest_spot', {})
    
    energy_gain = rest_spot.get('energy_gain', 15)
    health_gain = rest_spot.get('health_gain', 10)
    magic_gain = rest_spot.get('magic_gain', 0)
    
    character.energy = min(character.energy + energy_gain, character.max_energy)
    character.health = min(character.health + health_gain, character.max_health)
    character.mana = min(character.mana + magic_gain, character.max_mana)
    character.last_rest_time = now
    
    from main import save_character
    save_character(character)
    
    rest_text = f"✅ Отдохнул! +{energy_gain}⚡, +{health_gain}❤️"
    if magic_gain > 0:
        rest_text += f", +{magic_gain}🔮"
    
    bot.answer_callback_query(call.id, rest_text)

# ========== БОЙ ==========

def battle_command(message, bot, get_or_create_player_func, enemies_data):
    """Команда /battle - начало боя"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверяем энергию
    if character.energy < 10:
        bot.send_message(
            message.chat.id,
            "❌ Недостаточно энергии! Нужно 10⚡ для боя.",
            parse_mode='Markdown'
        )
        return
    
    # Получаем врагов в текущей локации
    from main import locations_data
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

# ========== КЛАССЫ ==========

def class_command(message, bot, get_or_create_player_func):
    """Команда /class - выбор класса"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if character.player_class:
        class_name = CLASS_INFO.get(character.player_class, {}).get('name', character.player_class)
        text = f"⚔️ *Твой класс:*\n\n🎯 {class_name}\n📊 Уровень класса: {character.class_level or 1}"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
        bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')
        return
    
    text = "⚔️ *Выбери свой класс:*\n\n"
    text += "🛡️ *Воин* - Сила: +5 | Выносливость: +3\n"
    text += "🏹 *Лучник* - Ловкость: +5 | Удача: +2\n"
    text += "🔮 *Маг* - Интеллект: +5 | Мана: +50\n"
    text += "⚔️✨ *Паладин* - Сила: +3 | Выносливость: +3 | Интеллект: +2\n"
    text += "🗡️ *Разбойник* - Ловкость: +4 | Удача: +3\n"
    text += "🌿 *Друид* - Интеллект: +4 | Выносливость: +2"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    classes = ["warrior", "archer", "mage", "paladin", "rogue", "druid"]
    class_names = ["Воин", "Лучник", "Маг", "Паладин", "Разбойник", "Друид"]
    
    for i, class_id in enumerate(classes):
        keyboard.add(InlineKeyboardButton(class_names[i], callback_data=f"game:select_class:{class_id}"))
    
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
    
    class_bonuses = {
        "warrior": {"strength": 5, "vitality": 3},
        "archer": {"agility": 5, "luck": 2},
        "mage": {"intelligence": 5, "max_mana": 50},
        "paladin": {"strength": 3, "vitality": 3, "intelligence": 2},
        "rogue": {"agility": 4, "luck": 3},
        "druid": {"intelligence": 4, "vitality": 2}
    }
    
    bonuses = class_bonuses.get(class_name, {})
    
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
    from .start import start_command
    start_command(call.message, bot, get_or_create_player_func)

# ========== ИНВЕНТАРЬ ==========

def inventory_command(message, bot, get_or_create_player_func, items_data):
    """Команда /inventory - просмотр инвентаря"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = f"📦 *Инвентарь*\n\n"
    
    if not character.inventory:
        text += "🗂️ Инвентарь пуст"
    else:
        items_by_cat = {}
        for item_id, quantity in character.inventory.items():
            item = items_data.get("items", {}).get(item_id, {})
            category = item.get("type", "other")
            if category not in items_by_cat:
                items_by_cat[category] = []
            items_by_cat[category].append((item_id, item, quantity))
        
        category_names = {
            "weapon": "⚔️ Оружие",
            "armor": "🛡️ Броня",
            "potion": "🧪 Зелья",
            "food": "🍖 Еда",
            "material": "📦 Материалы",
            "quest": "📜 Квестовые",
            "other": "📦 Прочее"
        }
        
        for category, items in items_by_cat.items():
            cat_name = category_names.get(category, f"📦 {category.capitalize()}")
            text += f"\n*{cat_name}:*\n"
            for item_id, item, quantity in items:
                name = item.get("name", item_id)
                emoji = item.get("icon", "📦")
                text += f"├ {emoji} {name} x{quantity}\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⚔️ Экипировка", callback_data="game:equipment"),
        InlineKeyboardButton("🔙 Назад", callback_data="game:profile")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

def equipment_command(message, bot, get_or_create_player_func, items_data):
    """Команда просмотра экипировки"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "⚔️ *Экипировка*\n\n"
    
    weapon_id = character.equipped_weapon
    armor_id = character.equipped_armor
    
    weapon = items_data.get("items", {}).get(weapon_id, {}) if weapon_id else None
    armor = items_data.get("items", {}).get(armor_id, {}) if armor_id else None
    
    if weapon:
        text += f"⚔️ *Оружие:* {weapon.get('icon', '')} {weapon.get('name', weapon_id)}\n"
        text += f"├ Урон: +{weapon.get('damage', 0)}\n"
    else:
        text += "⚔️ *Оружие:* не экипировано\n"
    
    if armor:
        text += f"\n🛡️ *Броня:* {armor.get('icon', '')} {armor.get('name', armor_id)}\n"
        text += f"├ Защита: +{armor.get('defense', 0)}\n"
    else:
        text += "\n🛡️ *Броня:* не экипирована\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔙 В инвентарь", callback_data="game:inventory")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

# ========== ОБРАБОТЧИК КОЛБЭКОВ ==========

def handle_callback(call, bot, get_or_create_player_func, locations_data, items_data, 
                   enemies_data, quests_data, crafting_data, house_data, expeditions_data):
    """Обработчик callback-запросов для game"""
    data = call.data
    
    if data == "game:profile":
        profile_command(call.message, bot, get_or_create_player_func, items_data)
    elif data == "game:stats":
        stats_command(call.message, bot, get_or_create_player_func, items_data)
    elif data == "game:inventory":
        inventory_command(call.message, bot, get_or_create_player_func, items_data)
    elif data == "game:equipment":
        equipment_command(call.message, bot, get_or_create_player_func, items_data)
    elif data == "game:location":
        location_command(call.message, bot, get_or_create_player_func, locations_data, items_data)
    elif data == "game:map":
        map_command(call.message, bot)
    elif data == "game:move":
        move_command(call.message, bot, get_or_create_player_func, locations_data)
    elif data == "game:hunt":
        hunt_action(call, bot, get_or_create_player_func, locations_data, enemies_data, items_data)
    elif data == "game:fish":
        fish_action(call, bot, get_or_create_player_func, items_data)
    elif data == "game:gather":
        gather_action(call, bot, get_or_create_player_func, items_data)
    elif data == "game:mine":
        mine_action(call, bot, get_or_create_player_func, items_data)
    elif data == "game:rest_local":
        rest_action(call, bot, get_or_create_player_func)
    elif data.startswith("game:rest_spot:"):
        rest_spot_action(call, bot, get_or_create_player_func)
    elif data == "game:rest_cooldown":
        bot.answer_callback_query(call.id, "⏳ Отдых ещё не доступен! Подожди.", show_alert=True)
    elif data.startswith("game:move_to:"):
        move_to_location(call, bot, get_or_create_player_func, locations_data)
    elif data.startswith("game:select_class:"):
        select_class_callback(call, bot, get_or_create_player_func)
    elif data == "game:no_energy":
        bot.answer_callback_query(call.id, "❌ Недостаточно энергии!", show_alert=True)
    elif data.startswith("game:take_item:"):
        take_item_action(call, bot, get_or_create_player_func, locations_data, items_data)
    elif data.startswith("game:search_stash:"):
        search_stash_action(call, bot, get_or_create_player_func, locations_data, items_data)
    elif data == "game:dig_worms":
        dig_worms_action(call, bot, get_or_create_player_func)
    elif data == "game:stash_cooldown":
        bot.answer_callback_query(call.id, "⏳ Тайник ещё не восстановился!", show_alert=True)

# ========== ЭКСПОРТ ==========

__all__ = [
    # Команды
    'profile_command',
    'stats_command',
    'quest_command',
    'craft_command',
    'house_command',
    'expedition_command',
    'location_command',
    'map_command',
    'move_command',
    'battle_command',
    'class_command',
    'inventory_command',
    'equipment_command',
    
    # Обработчики действий
    'hunt_action',
    'fish_action',
    'gather_action',
    'mine_action',
    'rest_action',
    'rest_spot_action',
    'move_to_location',
    'select_class_callback',
    'take_item_action',
    'search_stash_action',
    'dig_worms_action',
    
    # Главный обработчик
    'handle_callback',
    
    # Константы
    'ENERGY_COSTS',
    'RESPOT_SPOTS'
]
