# /bot/handlers/game.py
import logging
import random
import time
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# ========== КОНСТАНТЫ ==========

ENERGY_COSTS = {
    "move": 1,
    "hunt": 5,
    "fish": 2,
    "craft": 2,
    "rest": 0,
    "gather": 2,
    "mine": 2
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
        text += f"⚔️ Класс: {character.player_class}\n"
    
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
        text += f"\n🎯 Класс: {character.player_class} (ур. {character.class_level or 1})"
    
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
        "weapon": "⚔️ Оружие",
        "armor": "🛡️ Броня",
        "potion": "🧪 Зелья",
        "food": "🍖 Еда",
        "tool": "🔧 Инструменты",
        "material": "📦 Материалы"
    }
    
    available_recipes = 0
    
    for cat_id, cat_name in categories.items():
        cat_recipes = []
        for recipe_id, recipe in crafting_data.get("recipes", {}).items():
            if recipe.get("category") == cat_id:
                if character.level >= recipe.get("level_req", 1):
                    cat_recipes.append((recipe_id, recipe))
        
        if cat_recipes:
            text += f"\n*{cat_name}:*\n"
            for recipe_id, recipe in cat_recipes[:3]:  # Показываем первые 3
                text += f"├ {recipe.get('name', recipe_id)}\n"
                available_recipes += 1
    
    if available_recipes == 0:
        text += "❌ Нет доступных рецептов\n"
    
    text += f"\n📊 Доступно рецептов: {available_recipes}"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⚔️ Оружие", callback_data="craft:weapon"),
        InlineKeyboardButton("🛡️ Броня", callback_data="craft:armor"),
        InlineKeyboardButton("🧪 Зелья", callback_data="craft:potion"),
        InlineKeyboardButton("🍖 Еда", callback_data="craft:food"),
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

# ========== ЛОКАЦИИ И ПЕРЕМЕЩЕНИЕ ==========

def location_command(message, bot, get_or_create_player_func, locations_data):
    """Команда /location - текущая локация"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    location_id = character.location or "start"
    location = locations_data.get("locations", {}).get(location_id, {})
    
    if not location:
        location = {"name": "Неизвестно", "description": "Локация не найдена"}
    
    text = f"📍 *{location.get('name', 'Локация')}*\n\n"
    text += location.get('description', 'Описание отсутствует')
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    actions_added = 0
    
    actions = location.get('actions', [])
    for action in actions:
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
        elif action['type'] == 'hunt':
            if character.energy >= 5:
                keyboard.add(InlineKeyboardButton(
                    action['text'],
                    callback_data="game:hunt"
                ))
                actions_added += 1
        elif action['type'] == 'rest':
            keyboard.add(InlineKeyboardButton(
                action['text'],
                callback_data="game:rest"
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
    """Команда /map - карта мира"""
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
    text += "├ 🏞️ Берег озера (ур. 3+)\n\n"
    
    text += "⛰️ **Горные зоны:**\n"
    text += "├ ⛰️ Горная тропа (ур. 10+)\n"
    text += "├ ⛏️ Вход в шахту (ур. 15+)\n"
    text += "├ 🏔️ Горная вершина (ур. 12+)\n"
    text += "├ 🌋 Тропа к вулкану (ур. 25+)\n"
    text += "├ 🌋 Жерло вулкана (ур. 28+)\n"
    text += "├ 🏖️ Вулканический пляж (ур. 25+)\n\n"
    
    text += "🏝️ **Острова:**\n"
    text += "├ ⚓ Гавань островов (ур. 30+)\n"
    text += "├ 🌋 Огненный остров (ур. 45+, 3🌈)\n"
    text += "├ 💎 Кристальный остров (ур. 50+, 1💎)\n"
    text += "├ 🐉 Остров драконов (ур. 55+, 5💎)\n\n"
    
    text += "🏛️ **Подземелья:**\n"
    text += "├ ⛏️ Шахта (5 уровней, ур. 15-30)\n"
    text += "├ 🏛️ Древние руины (ур. 35+)\n"
    text += "├ 🌉 Мост перед драконом (ур. 40+)\n"
    text += "├ 🐉 Логово дракона (ур. 50+)\n"
    
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
    island_locs = []
    dungeon_locs = []
    
    for loc_id, loc_data in all_locations.items():
        if loc_id != current_location:
            level_req = loc_data.get('level_req', 1)
            if character.level >= level_req:
                name = loc_data.get('name', loc_id)
                
                if "дерев" in name.lower() or "площадь" in name.lower() or "таверн" in name.lower() or "рыночн" in name.lower() or "кузниц" in name.lower() or "башн" in name.lower():
                    village_locs.append((loc_id, name))
                elif "лес" in name.lower() or "троп" in name.lower() or "развил" in name.lower() or "озер" in name.lower():
                    forest_locs.append((loc_id, name))
                elif "гор" in name.lower() or "шахт" in name.lower() or "вулкан" in name.lower() or "пляж" in name.lower() or "вершин" in name.lower():
                    mountain_locs.append((loc_id, name))
                elif "остров" in name.lower() or "гаван" in name.lower():
                    island_locs.append((loc_id, name))
                elif "руин" in name.lower() or "мост" in name.lower() or "логов" in name.lower():
                    dungeon_locs.append((loc_id, name))
    
    if village_locs:
        text += "🏘️ *Деревня:*\n"
        for loc_id, name in village_locs:
            text += f"├ {name}\n"
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{loc_id}"))
            locations_found += 1
        text += "\n"
    
    if forest_locs:
        text += "🌲 *Лес:*\n"
        for loc_id, name in forest_locs:
            text += f"├ {name}\n"
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{loc_id}"))
            locations_found += 1
        text += "\n"
    
    if mountain_locs:
        text += "⛰️ *Горы:*\n"
        for loc_id, name in mountain_locs:
            text += f"├ {name}\n"
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{loc_id}"))
            locations_found += 1
        text += "\n"
    
    if island_locs:
        text += "🏝️ *Острова:*\n"
        for loc_id, name in island_locs:
            text += f"├ {name}\n"
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{loc_id}"))
            locations_found += 1
        text += "\n"
    
    if dungeon_locs:
        text += "🏛️ *Подземелья:*\n"
        for loc_id, name in dungeon_locs:
            text += f"├ {name}\n"
            keyboard.add(InlineKeyboardButton(f"➡️ {name}", callback_data=f"game:move_to:{loc_id}"))
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
            if character.rainbow_shards < cost:
                bot.answer_callback_query(call.id, f"❌ Нужно {cost} радужных осколков!", show_alert=True)
                return
            character.rainbow_shards -= cost
        if 'rainbow_stone' in entry_cost:
            cost = entry_cost['rainbow_stone']
            if character.rainbow_stones < cost:
                bot.answer_callback_query(call.id, f"❌ Нужно {cost} радужных камней!", show_alert=True)
                return
            character.rainbow_stones -= cost
    
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

# ========== ДЕЙСТВИЯ ==========

def hunt_action(call, bot, get_or_create_player_func):
    """Обработчик охоты"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if character.energy < 5:
        bot.answer_callback_query(call.id, "❌ Нужно 5⚡ энергии!")
        return
    
    character.energy -= 5
    from main import save_character
    save_character(character)
    
    bot.answer_callback_query(call.id, "⏳ Охота... 5 секунд")
    
    # Имитация задержки
    time.sleep(5)
    
    # Случайный результат охоты
    exp_gain = random.randint(10, 30)
    gold_gain = random.randint(5, 15)
    
    # Шанс найти предмет
    item_found = None
    if random.random() < 0.3:  # 30% шанс
        possible_items = ["wolf_fur", "boar_tusk", "spider_silk", "feather"]
        item_found = random.choice(possible_items)
        character.add_item(item_found)
    
    character.experience += exp_gain
    character.gold += gold_gain
    character.kills_total = (character.kills_total or 0) + 1
    save_character(character)
    
    result_text = f"🎯 *Охота завершена!*\n\n✨ +{exp_gain} опыта\n💰 +{gold_gain} золота"
    if item_found:
        item_name = {
            "wolf_fur": "🐺 Волчья шкура",
            "boar_tusk": "🐗 Клык кабана",
            "spider_silk": "🕷️ Паучий шёлк",
            "feather": "🪶 Перо"
        }.get(item_found, item_found)
        result_text += f"\n📦 Найдено: {item_name}"
    
    bot.send_message(call.message.chat.id, result_text, parse_mode='Markdown')

def fish_action(call, bot, get_or_create_player_func):
    """Обработчик рыбалки"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if character.energy < 2:
        bot.answer_callback_query(call.id, "❌ Нужно 2⚡ энергии!")
        return
    
    character.energy -= 2
    from main import save_character
    save_character(character)
    
    # Случайный результат рыбалки
    exp_gain = random.randint(5, 15)
    fish_gain = random.randint(1, 3)
    
    character.experience += exp_gain
    for _ in range(fish_gain):
        character.add_item("fish")
    save_character(character)
    
    bot.send_message(
        call.message.chat.id,
        f"🎣 *Рыбалка!*\n\n🐟 Поймано рыб: {fish_gain}\n✨ +{exp_gain} опыта",
        parse_mode='Markdown'
    )

def gather_action(call, bot, get_or_create_player_func):
    """Обработчик сбора трав"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if character.energy < 2:
        bot.answer_callback_query(call.id, "❌ Нужно 2⚡ энергии!")
        return
    
    character.energy -= 2
    from main import save_character
    save_character(character)
    
    # Случайный результат сбора
    exp_gain = random.randint(5, 10)
    herb_gain = random.randint(1, 3)
    berry_gain = random.randint(0, 2)
    
    character.experience += exp_gain
    for _ in range(herb_gain):
        character.add_item("herb")
    for _ in range(berry_gain):
        character.add_item("berry")
    save_character(character)
    
    bot.send_message(
        call.message.chat.id,
        f"🌿 *Сбор трав!*\n\n🌿 Трав: {herb_gain}\n🫐 Ягод: {berry_gain}\n✨ +{exp_gain} опыта",
        parse_mode='Markdown'
    )

def mine_action(call, bot, get_or_create_player_func):
    """Обработчик добычи руды"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if character.energy < 2:
        bot.answer_callback_query(call.id, "❌ Нужно 2⚡ энергии!")
        return
    
    character.energy -= 2
    from main import save_character
    save_character(character)
    
    # Случайный результат добычи
    exp_gain = random.randint(10, 20)
    
    # Определяем руду в зависимости от уровня шахты
    location_id = character.location or "start"
    if "mine_level1" in location_id:
        ores = ["copper_ore", "copper_ore", "iron_ore"]
    elif "mine_level2" in location_id:
        ores = ["iron_ore", "iron_ore", "gold_ore"]
    elif "mine_level3" in location_id:
        ores = ["gold_ore", "gold_ore", "crystal"]
    elif "mine_level4" in location_id:
        ores = ["mythril_ore", "crystal", "ruby"]
    else:
        ores = ["stone", "coal", "iron_ore"]
    
    ore_found = random.choice(ores)
    amount = random.randint(1, 3)
    
    character.experience += exp_gain
    for _ in range(amount):
        character.add_item(ore_found)
    save_character(character)
    
    ore_names = {
        "copper_ore": "Медная руда",
        "iron_ore": "Железная руда",
        "gold_ore": "Золотая руда",
        "mythril_ore": "Мифриловая руда",
        "crystal": "Кристалл",
        "ruby": "Рубин",
        "stone": "Камень",
        "coal": "Уголь"
    }
    
    bot.send_message(
        call.message.chat.id,
        f"⛏️ *Добыча руды!*\n\n📦 Найдено: {ore_names.get(ore_found, ore_found)} x{amount}\n✨ +{exp_gain} опыта",
        parse_mode='Markdown'
    )

def rest_action(call, bot, get_or_create_player_func):
    """Обработчик отдыха"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверяем кулдаун
    now = int(time.time())
    last_rest = character.last_rest_time or 0
    cooldown = 3600  # 1 час
    
    if now - last_rest < cooldown:
        remaining = cooldown - (now - last_rest)
        minutes = remaining // 60
        bot.answer_callback_query(call.id, f"⏳ Отдых ещё не доступен. Подожди {minutes} мин.")
        return
    
    # Определяем бонус отдыха в зависимости от локации
    location_id = character.location or "start"
    from main import locations_data
    location = locations_data.get("locations", {}).get(location_id, {})
    rest_spot = location.get('rest_spot', {})
    
    energy_gain = rest_spot.get('energy_gain', 30)
    health_gain = rest_spot.get('health_gain', 20)
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

# ========== КЛАССЫ ==========

def class_command(message, bot, get_or_create_player_func):
    """Команда /class - выбор класса"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if character.player_class:
        text = f"⚔️ *Твой класс:*\n\n🎯 {character.player_class.capitalize()}\n📊 Уровень класса: {character.class_level or 1}"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="start:menu"))
        bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')
        return
    
    text = "⚔️ *Выбери свой класс:*\n\n"
    text += "🛡️ *Воин* - Сила: +5 | Выносливость: +3\n"
    text += "🏹 *Лучник* - Ловкость: +5 | Удача: +2\n"
    text += "🔮 *Маг* - Интеллект: +5 | Мана: +50\n"
    text += "🛡️ *Паладин* - Сила: +3 | Выносливость: +3 | Интеллект: +2\n"
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
            category = item.get("category", "other")
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
                emoji = item.get("emoji", "📦")
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
        text += f"⚔️ *Оружие:* {weapon.get('emoji', '')} {weapon.get('name', weapon_id)}\n"
        text += f"├ Урон: +{weapon.get('damage', 0)}\n"
    else:
        text += "⚔️ *Оружие:* не экипировано\n"
    
    if armor:
        text += f"\n🛡️ *Броня:* {armor.get('emoji', '')} {armor.get('name', armor_id)}\n"
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
        location_command(call.message, bot, get_or_create_player_func, locations_data)
    elif data == "game:map":
        map_command(call.message, bot)
    elif data == "game:move":
        move_command(call.message, bot, get_or_create_player_func, locations_data)
    elif data == "game:hunt":
        hunt_action(call, bot, get_or_create_player_func)
    elif data == "game:fish":
        fish_action(call, bot, get_or_create_player_func)
    elif data == "game:gather":
        gather_action(call, bot, get_or_create_player_func)
    elif data == "game:mine":
        mine_action(call, bot, get_or_create_player_func)
    elif data == "game:rest":
        rest_action(call, bot, get_or_create_player_func)
    elif data.startswith("game:move_to:"):
        move_to_location(call, bot, get_or_create_player_func, locations_data)
    elif data.startswith("game:select_class:"):
        select_class_callback(call, bot, get_or_create_player_func)
    elif data == "game:no_energy":
        bot.answer_callback_query(call.id, "❌ Недостаточно энергии!", show_alert=True)

# ========== ЭКСПОРТ ==========

__all__ = [
    # Команды
    'profile_command',
    'stats_command',
    'quest_command',
    'craft_command',
    'house_command',
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
    'move_to_location',
    'select_class_callback',
    
    # Главный обработчик
    'handle_callback',
    
    # Константы
    'ENERGY_COSTS'
]
