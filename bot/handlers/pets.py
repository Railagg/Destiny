import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import random
import time
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ ПИТОМЦЕВ
# ============================================

PET_RARITIES = {
    "common": "⚪ Обычный",
    "uncommon": "🟢 Необычный",
    "rare": "🔵 Редкий",
    "epic": "🟣 Эпический",
    "legendary": "🟡 Легендарный",
    "ancient": "🔴 Древний",
    "mythic": "💜 Мифический"
}

PET_BONUSES = {
    "forest_fox": {"name": "🦊 Лесная лиса", "bonus": "herb_find", "value": 5},
    "forest_wolf": {"name": "🐺 Лесной волк", "bonus": "damage", "value": 3},
    "mountain_goat": {"name": "🐐 Горный козёл", "bonus": "mining_speed", "value": 5},
    "mountain_eagle": {"name": "🦅 Горный орёл", "bonus": "vision", "value": 20},
    "desert_lizard": {"name": "🦎 Пустынная ящерица", "bonus": "heat_resist", "value": 10},
    "desert_camel": {"name": "🐫 Пустынный верблюд", "bonus": "carry_capacity", "value": 50},
    "swamp_frog": {"name": "🐸 Болотная лягушка", "bonus": "poison_resist", "value": 10},
    "swamp_snake": {"name": "🐍 Болотная змея", "bonus": "stealth", "value": 10},
    "ice_penguin": {"name": "🐧 Ледяной пингвин", "bonus": "cold_resist", "value": 10},
    "ice_owl": {"name": "🦉 Ледяная сова", "bonus": "magic_find", "value": 5},
    "beach_crab": {"name": "🦀 Пляжный краб", "bonus": "pearl_find", "value": 2},
    "frozen_seal": {"name": "🦭 Ледяной тюлень", "bonus": "diving_time", "value": 10},
    "lava_salamander": {"name": "🦎 Лавовая саламандра", "bonus": "fire_resist", "value": 15},
    "crystal_bunny": {"name": "🐇 Кристальный зайчик", "bonus": "luck", "value": 5},
    "wolf_alpha": {"name": "🐺👑 Вожак волков", "bonus": "all_damage", "value": 10},
    "desert_roc": {"name": "🦅 Пустынный рок", "bonus": "fly_speed", "value": 30},
    "ice_phoenix": {"name": "❄️🔥 Ледяной феникс", "bonus": "ice_damage", "value": 20},
    "magma_dragon": {"name": "🐲 Магмовый дракон", "bonus": "fire_damage", "value": 25},
    "phoenix": {"name": "🔥 Феникс", "bonus": "revive", "value": 1},
    "crystal_dragon": {"name": "💎 Кристальный дракон", "bonus": "magic_damage", "value": 30},
    "young_dragon": {"name": "🐉 Молодой дракон", "bonus": "all_stats", "value": 10},
    "dragon_king_cub": {"name": "👑 Детёныш короля драконов", "bonus": "all_stats", "value": 30},
    "world_turtle": {"name": "🐢 Мировая черепаха", "bonus": "defense", "value": 100}
}

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

def pets_command(message, bot_instance, get_or_create_player_func, pets_data):
    """Команда /pets - питомцы"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Получаем список питомцев игрока
    pets = character.pets if hasattr(character, 'pets') else []
    active_pet = character.active_pet if hasattr(character, 'active_pet') else None
    
    text = "🐾 *Система питомцев*\n\n"
    
    if not pets:
        text += "У тебя пока нет питомцев.\n"
        text += "Питомцев можно найти в разных биомах:\n\n"
        text += "🌲 *Лес:* лиса, волк, лесной дух\n"
        text += "⛰️ *Горы:* козёл, орёл\n"
        text += "🏜️ *Пустыня:* ящерица, верблюд, феникс\n"
        text += "🌿 *Болото:* лягушка, змея\n"
        text += "❄️ *Ледяные равнины:* пингвин, сова, ледяной феникс\n"
        text += "🏖️ *Пляж:* краб\n"
        text += "🌋 *Вулкан:* саламандра, магмовый дракон\n"
        text += "🧊 *Замёрзший океан:* тюлень\n"
        text += "💎 *Кристальный остров:* кристальный зайчик, кристальный дракон\n"
        text += "🐉 *Остров драконов:* молодой дракон, королевский детёныш"
    else:
        text += f"📊 Всего питомцев: {len(pets)}\n"
        if active_pet:
            active = next((p for p in pets if p.get('id') == active_pet), None)
            if active:
                text += f"✅ Активный: {active.get('name', 'Питомец')}\n\n"
        
        text += "*Твои питомцы:*\n"
        for pet in pets[:5]:
            name = pet.get('name', 'Питомец')
            level = pet.get('level', 1)
            happiness = pet.get('happiness', 100)
            emoji = "❤️" if happiness > 80 else "😊" if happiness > 50 else "😐" if happiness > 20 else "💔"
            text += f"• {name} (ур.{level}) {emoji} {happiness}%\n"
        
        if len(pets) > 5:
            text += f"...и ещё {len(pets) - 5} питомцев"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📋 Список", callback_data="pets:list"),
        InlineKeyboardButton("🍖 Корм", callback_data="pets:food"),
        InlineKeyboardButton("🏠 Конура", callback_data="pets:house"),
        InlineKeyboardButton("🥚 Яйца", callback_data="pets:eggs"),
        InlineKeyboardButton("📊 Статистика", callback_data="pets:stats"),
        InlineKeyboardButton("❓ Помощь", callback_data="pets:help")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_pets_list(call, bot_instance, character, pets_data):
    """Показать список питомцев"""
    pets = character.pets if hasattr(character, 'pets') else []
    active_pet = character.active_pet if hasattr(character, 'active_pet') else None
    
    if not pets:
        text = "🐾 *У тебя нет питомцев*\n\n"
        text += "Где найти питомцев:\n\n"
        
        # Группируем по биомам
        biomes = {
            "🌲 Лес": ["forest_fox", "forest_wolf", "forest_spirit"],
            "⛰️ Горы": ["mountain_goat", "mountain_eagle"],
            "🏜️ Пустыня": ["desert_lizard", "desert_camel", "desert_phoenix"],
            "🌿 Болото": ["swamp_frog", "swamp_snake", "swamp_kraken"],
            "❄️ Ледяные равнины": ["ice_penguin", "ice_owl", "ice_phoenix"],
            "🏖️ Пляж": ["beach_crab"],
            "🌋 Вулкан": ["lava_salamander", "magma_dragon"],
            "🧊 Замёрзший океан": ["frozen_seal"],
            "💎 Кристальный остров": ["crystal_bunny", "crystal_dragon"],
            "🐉 Остров драконов": ["young_dragon", "dragon_king_cub"]
        }
        
        for biome, pet_list in biomes.items():
            text += f"{biome}: "
            names = []
            for pet_id in pet_list:
                if pet_id in PET_BONUSES:
                    names.append(PET_BONUSES[pet_id]["name"])
            text += ", ".join(names[:3]) + "\n"
    else:
        text = "🐾 *Твои питомцы*\n\n"
        
        markup = InlineKeyboardMarkup(row_width=1)
        
        for pet in pets:
            pet_id = pet.get('id')
            name = pet.get('name', PET_BONUSES.get(pet_id, {}).get('name', 'Питомец'))
            level = pet.get('level', 1)
            exp = pet.get('exp', 0)
            exp_needed = level * 100
            happiness = pet.get('happiness', 100)
            
            # Прогресс-бар опыта
            exp_percent = int((exp / exp_needed) * 10)
            exp_bar = "█" * exp_percent + "░" * (10 - exp_percent)
            
            # Статус
            status = "✅ АКТИВЕН" if pet.get('id') == active_pet else ""
            
            text += f"*{name}* {status}\n"
            text += f"  Ур.{level} | {exp_bar} {exp}/{exp_needed} опыта\n"
            text += f"  😊 Счастье: {happiness}%\n"
            
            # Бонусы
            bonus_info = PET_BONUSES.get(pet_id, {})
            if bonus_info:
                text += f"  ✨ Бонус: +{bonus_info.get('value', 0)} {bonus_info.get('bonus', '')}\n"
            
            text += "\n"
            
            # Кнопки для питомца
            markup.add(InlineKeyboardButton(
                f"📌 {name}",
                callback_data=f"pets:view:{pet.get('id')}"
            ))
    
    markup = InlineKeyboardMarkup() if 'markup' not in locals() else markup
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_pet_details(call, bot_instance, character, pet_id, pets_data):
    """Показать детали питомца"""
    pets = character.pets if hasattr(character, 'pets') else []
    pet = next((p for p in pets if p.get('id') == pet_id), None)
    
    if not pet:
        bot_instance.answer_callback_query(call.id, "❌ Питомец не найден")
        return
    
    name = pet.get('name', PET_BONUSES.get(pet_id, {}).get('name', 'Питомец'))
    level = pet.get('level', 1)
    exp = pet.get('exp', 0)
    exp_needed = level * 100
    happiness = pet.get('happiness', 100)
    
    # Прогресс-бар
    exp_percent = int((exp / exp_needed) * 10)
    exp_bar = "█" * exp_percent + "░" * (10 - exp_percent)
    
    # Способности
    abilities = pet.get('abilities', [])
    
    text = f"🐾 *{name}*\n\n"
    text += f"📊 Уровень: {level}\n"
    text += f"📈 Опыт: {exp_bar} {exp}/{exp_needed}\n"
    text += f"😊 Счастье: {happiness}%\n\n"
    
    # Бонусы
    bonus_info = PET_BONUSES.get(pet_id, {})
    if bonus_info:
        text += f"✨ *Бонус:* +{bonus_info.get('value', 0)} {bonus_info.get('bonus', '')}\n\n"
    
    # Способности
    if abilities:
        text += "*🎯 Способности:*\n"
        for ability in abilities[:3]:
            text += f"• {ability.get('name')}: {ability.get('description', '')}\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🍖 Кормить", callback_data=f"pets:feed:{pet_id}"),
        InlineKeyboardButton("🎮 Играть", callback_data=f"pets:play:{pet_id}"),
        InlineKeyboardButton("⭐ Сделать активным", callback_data=f"pets:activate:{pet_id}")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:list"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def feed_pet(call, bot_instance, character, pet_id):
    """Покормить питомца"""
    from main import save_character
    
    pets = character.pets if hasattr(character, 'pets') else []
    pet_index = next((i for i, p in enumerate(pets) if p.get('id') == pet_id), None)
    
    if pet_index is None:
        bot_instance.answer_callback_query(call.id, "❌ Питомец не найден")
        return
    
    # Проверяем наличие еды
    food_items = ["meat", "fish", "berry", "magic_food"]
    has_food = False
    food_type = None
    
    for food in food_items:
        if character.has_item(food):
            has_food = True
            food_type = food
            break
    
    if not has_food:
        bot_instance.answer_callback_query(call.id, "❌ Нет еды для питомца! Купи в магазине.")
        return
    
    # Кормим
    character.remove_item(food_type)
    
    # Опыт за еду
    exp_gain = {"meat": 10, "fish": 15, "berry": 5, "magic_food": 50}.get(food_type, 10)
    
    pet = pets[pet_index]
    pet['exp'] = pet.get('exp', 0) + exp_gain
    pet['happiness'] = min(100, pet.get('happiness', 100) + 10)
    
    # Повышение уровня
    while pet['exp'] >= pet.get('level', 1) * 100:
        pet['exp'] -= pet['level'] * 100
        pet['level'] = pet.get('level', 1) + 1
        
        # Открываем новую способность
        if pet['level'] % 5 == 0:
            if 'abilities' not in pet:
                pet['abilities'] = []
            pet['abilities'].append({
                'name': f'Способность ур.{pet["level"]}',
                'description': 'Новая способность открыта!'
            })
    
    character.pets = pets
    save_character(character)
    
    bot_instance.answer_callback_query(call.id, f"✅ {PET_BONUSES.get(pet_id, {}).get('name', 'Питомец')} покормлен! +{exp_gain} опыта")
    show_pet_details(call, bot_instance, character, pet_id, None)

def play_with_pet(call, bot_instance, character, pet_id):
    """Поиграть с питомцем"""
    from main import save_character
    
    pets = character.pets if hasattr(character, 'pets') else []
    pet_index = next((i for i, p in enumerate(pets) if p.get('id') == pet_id), None)
    
    if pet_index is None:
        bot_instance.answer_callback_query(call.id, "❌ Питомец не найден")
        return
    
    # Проверяем энергию
    if character.energy < 5:
        bot_instance.answer_callback_query(call.id, "❌ Нужно 5⚡ энергии!")
        return
    
    character.energy -= 5
    pet = pets[pet_index]
    pet['happiness'] = min(100, pet.get('happiness', 100) + 20)
    pet['exp'] = pet.get('exp', 0) + 5
    
    character.pets = pets
    save_character(character)
    
    bot_instance.answer_callback_query(call.id, "✅ Питомец счастлив! +20% счастья, +5 опыта")
    show_pet_details(call, bot_instance, character, pet_id, None)

def activate_pet(call, bot_instance, character, pet_id):
    """Сделать питомца активным"""
    from main import save_character
    
    character.active_pet = pet_id
    save_character(character)
    
    bot_instance.answer_callback_query(call.id, "✅ Питомец активен! Его бонусы работают.")
    show_pet_details(call, bot_instance, character, pet_id, None)

def show_food_shop(call, bot_instance, character, pets_data):
    """Показать магазин корма"""
    text = "🍖 *Магазин корма*\n\n"
    text += f"💰 Твой баланс: {character.gold} золота\n\n"
    
    foods = {
        "meat": {"name": "🥩 Мясо", "price": 10, "exp": 10, "happiness": 5},
        "fish": {"name": "🐟 Рыба", "price": 15, "exp": 15, "happiness": 5},
        "berry": {"name": "🫐 Ягоды", "price": 5, "exp": 5, "happiness": 5},
        "magic_food": {"name": "✨ Волшебный корм", "price": 100, "exp": 50, "happiness": 20}
    }
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for food_id, food in foods.items():
        can_afford = character.gold >= food['price']
        status = "✅" if can_afford else "❌"
        text += f"{status} *{food['name']}*\n"
        text += f"  Цена: {food['price']}💰\n"
        text += f"  Опыт: +{food['exp']} | Счастье: +{food['happiness']}%\n\n"
        
        if can_afford:
            markup.add(InlineKeyboardButton(
                f"Купить {food['name']}",
                callback_data=f"pets:buy_food:{food_id}"
            ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def buy_food(call, bot_instance, character, food_id, pets_data):
    """Купить корм"""
    from main import save_character
    
    foods = {
        "meat": {"name": "🥩 Мясо", "price": 10},
        "fish": {"name": "🐟 Рыба", "price": 15},
        "berry": {"name": "🫐 Ягоды", "price": 5},
        "magic_food": {"name": "✨ Волшебный корм", "price": 100}
    }
    
    if food_id not in foods:
        bot_instance.answer_callback_query(call.id, "❌ Корм не найден")
        return
    
    food = foods[food_id]
    
    if character.gold < food['price']:
        bot_instance.answer_callback_query(call.id, f"❌ Нужно {food['price']} золота")
        return
    
    character.gold -= food['price']
    character.add_item(food_id)
    save_character(character)
    
    bot_instance.answer_callback_query(call.id, f"✅ Куплен {food['name']}!")
    show_food_shop(call, bot_instance, character, pets_data)

def show_pet_house(call, bot_instance, character, pets_data):
    """Показать домик для питомцев"""
    house_level = character.house_level or 0
    pet_house_level = character.pet_house_level if hasattr(character, 'pet_house_level') else 1
    
    # Вместимость в зависимости от уровня
    capacity = {
        1: 2,
        2: 4,
        3: 6,
        4: 8,
        5: 10
    }.get(pet_house_level, 2)
    
    pets = character.pets if hasattr(character, 'pets') else []
    active_pet = character.active_pet if hasattr(character, 'active_pet') else None
    
    text = "🏠 *Домик для питомцев*\n\n"
    
    if house_level < 5:
        text += f"❌ Домик для питомцев доступен на 5 уровне усадьбы.\n"
        text += f"Твой уровень дома: {house_level}\n"
        text += f"Осталось улучшений: {5 - house_level}\n\n"
        text += "На 5 уровне ты сможешь построить конуру и размещать питомцев!"
    else:
        text += f"📊 Уровень конуры: {pet_house_level}\n"
        text += f"📦 Вместимость: {capacity} питомцев\n"
        text += f"🐾 Сейчас в конуре: {len(pets)}/{capacity}\n\n"
        
        if pets:
            text += "*Размещённые питомцы:*\n"
            for pet in pets:
                name = pet.get('name', 'Питомец')
                status = "✅" if pet.get('id') == active_pet else ""
                text += f"• {name} {status}\n"
        
        text += "\n*Бонусы конуры:*\n"
        text += f"• +{pet_house_level * 10}% к счастью всех питомцев\n"
        text += f"• +{pet_house_level * 5}% к опыту\n"
        text += f"• Питомцы не теряют счастье в конуре"
        
        # Кнопка улучшения
        if pet_house_level < 5:
            next_costs = {
                2: {"wood": 500, "stone": 200, "iron_ingot": 50},
                3: {"wood": 1000, "stone": 500, "gold_ingot": 10},
                4: {"wood": 2000, "mythril_ingot": 20, "glass": 50},
                5: {"dragon_scale": 10, "rainbow_stone": 1, "wood": 5000}
            }
            
            cost = next_costs.get(pet_house_level + 1, {})
            if cost:
                text += "\n\n*Для улучшения нужно:*\n"
                for mat, amount in cost.items():
                    count = character.count_item(mat)
                    emoji = "✅" if count >= amount else "❌"
                    text += f"{emoji} {mat}: {count}/{amount}\n"
    
    markup = InlineKeyboardMarkup()
    if house_level >= 5 and pet_house_level < 5:
        markup.add(InlineKeyboardButton("🔨 Улучшить конуру", callback_data="pets:upgrade_house"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_eggs(call, bot_instance, character, pets_data):
    """Показать яйца питомцев"""
    eggs = {
        "common_egg": {"name": "⚪ Обычное яйцо", "chance": "80% обычный, 15% необычный, 4% редкий, 1% эпический"},
        "uncommon_egg": {"name": "🟢 Необычное яйцо", "chance": "40% обычный, 40% необычный, 15% редкий, 4% эпический, 1% легендарный"},
        "rare_egg": {"name": "🔵 Редкое яйцо", "chance": "30% необычный, 40% редкий, 20% эпический, 9% легендарный, 1% древний"},
        "epic_egg": {"name": "🟣 Эпическое яйцо", "chance": "30% редкий, 40% эпический, 25% легендарный, 4% древний, 1% мифический"},
        "legendary_egg": {"name": "🟡 Легендарное яйцо", "chance": "40% эпический, 40% легендарный, 15% древний, 5% мифический"},
        "ancient_egg": {"name": "🔴 Древнее яйцо", "chance": "50% легендарный, 40% древний, 10% мифический"},
        "mythic_egg": {"name": "💜 Мифическое яйцо", "chance": "100% мифический"}
    }
    
    text = "🥚 *Яйца питомцев*\n\n"
    text += "Яйца можно найти в ивентах, сундуках или купить у торговца.\n\n"
    
    for egg_id, egg in eggs.items():
        count = character.count_item(egg_id) if hasattr(character, 'count_item') else 0
        text += f"{egg['name']} x{count}\n"
        text += f"└ {egg['chance']}\n\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_pet_stats(call, bot_instance, character, pets_data):
    """Показать статистику по питомцам"""
    pets = character.pets if hasattr(character, 'pets') else []
    
    total_pets = len(pets)
    total_level = sum(p.get('level', 1) for p in pets)
    avg_level = total_level // total_pets if total_pets > 0 else 0
    total_happiness = sum(p.get('happiness', 100) for p in pets)
    avg_happiness = total_happiness // total_pets if total_pets > 0 else 0
    
    text = "📊 *Статистика питомцев*\n\n"
    text += f"📦 Всего питомцев: {total_pets}\n"
    text += f"📈 Средний уровень: {avg_level}\n"
    text += f"😊 Среднее счастье: {avg_happiness}%\n\n"
    
    # Распределение по редкости
    rarity_count = {}
    for pet in pets:
        rarity = pet.get('rarity', 'common')
        rarity_count[rarity] = rarity_count.get(rarity, 0) + 1
    
    if rarity_count:
        text += "*По редкости:*\n"
        for rarity, count in rarity_count.items():
            emoji = {
                "common": "⚪",
                "uncommon": "🟢",
                "rare": "🔵",
                "epic": "🟣",
                "legendary": "🟡",
                "ancient": "🔴",
                "mythic": "💜"
            }.get(rarity, "⚪")
            text += f"{emoji} {rarity.capitalize()}: {count}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_help(call, bot_instance):
    """Показать помощь по питомцам"""
    text = "🐾 *Система питомцев*\n\n"
    text += "Питомцы — верные друзья, которые помогают в приключениях.\n\n"
    
    text += "📊 *Характеристики:*\n"
    text += "• Уровень - растёт от кормления и игр\n"
    text += "• Опыт - получается за кормление\n"
    text += "• Счастье - падает со временем, растёт от игр\n"
    text += "• Способности - открываются на 5, 10, 15 уровне\n\n"
    
    text += "🎯 *Бонусы питомцев:*\n"
    text += "• 🦊 Лиса: +5% к поиску трав\n"
    text += "• 🐺 Волк: +3 к урону\n"
    text += "• 🦅 Орёл: +20% к обзору\n"
    text += "• 🐫 Верблюд: +50 переносимого веса\n"
    text += "• 🐍 Змея: +10% к скрытности\n"
    text += "• 🦉 Сова: +5% к поиску магии\n"
    text += "• 🦎 Саламандра: +15% к защите от огня\n"
    text += "• 🐇 Кристальный зайчик: +5 к удаче\n"
    text += "• 🔥 Феникс: шанс воскреснуть\n"
    text += "• 🐉 Дракон: +10 ко всем статам\n\n"
    
    text += "🍖 *Кормление:* /pet feed [имя]\n"
    text += "🎮 *Игры:* /pet play [имя]\n"
    text += "🏠 *Конура:* улучшается в доме\n"
    text += "🥚 *Яйца:* вылупляются через 24 часа"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# ФУНКЦИИ ДЛЯ ДРУГИХ ХЕНДЛЕРОВ
# ============================================

def add_pet(character, pet_id, pet_data):
    """Добавить питомца игроку"""
    from main import save_character
    
    if not hasattr(character, 'pets'):
        character.pets = []
    
    # Создаём питомца
    pet = {
        'id': pet_id,
        'name': pet_data.get('name', pet_id),
        'level': 1,
        'exp': 0,
        'happiness': 100,
        'rarity': pet_data.get('rarity', 'common'),
        'abilities': [],
        'acquired': time.time()
    }
    
    character.pets.append(pet)
    save_character(character)
    
    return pet

def hatch_egg(character, egg_id, pets_data):
    """Вылупить питомца из яйца"""
    import random
    
    if not character.has_item(egg_id):
        return None
    
    character.remove_item(egg_id)
    
    # Шансы выпадения в зависимости от яйца
    chances = {
        "common_egg": {
            "common": 80, "uncommon": 15, "rare": 4, "epic": 1
        },
        "uncommon_egg": {
            "common": 40, "uncommon": 40, "rare": 15, "epic": 4, "legendary": 1
        },
        "rare_egg": {
            "uncommon": 30, "rare": 40, "epic": 20, "legendary": 9, "ancient": 1
        },
        "epic_egg": {
            "rare": 30, "epic": 40, "legendary": 25, "ancient": 4, "mythic": 1
        },
        "legendary_egg": {
            "epic": 40, "legendary": 40, "ancient": 15, "mythic": 5
        },
        "ancient_egg": {
            "legendary": 50, "ancient": 40, "mythic": 10
        },
        "mythic_egg": {
            "mythic": 100
        }
    }
    
    egg_chances = chances.get(egg_id, {})
    
    # Выбираем редкость
    roll = random.randint(1, 100)
    cumulative = 0
    selected_rarity = "common"
    
    for rarity, chance in egg_chances.items():
        cumulative += chance
        if roll <= cumulative:
            selected_rarity = rarity
            break
    
    # Выбираем случайного питомца этой редкости
    available_pets = []
    for pet_id, pet_info in pets_data.get("pets", {}).items():
        if pet_info.get("rarity") == selected_rarity:
            available_pets.append((pet_id, pet_info))
    
    if not available_pets:
        return None
    
    selected = random.choice(available_pets)
    pet_id, pet_info = selected
    
    return add_pet(character, pet_id, pet_info)

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func, pets_data):
    """Обработка кнопок питомцев"""
    from main import save_character
    
    parts = call.data.split(':')
    action = parts[1] if len(parts) > 1 else "menu"
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if action == "menu":
        pets_command(call.message, bot_instance, get_or_create_player_func, pets_data)
    
    elif action == "list":
        show_pets_list(call, bot_instance, character, pets_data)
    
    elif action == "view" and len(parts) > 2:
        pet_id = parts[2]
        show_pet_details(call, bot_instance, character, pet_id, pets_data)
    
    elif action == "feed" and len(parts) > 2:
        pet_id = parts[2]
        feed_pet(call, bot_instance, character, pet_id)
    
    elif action == "play" and len(parts) > 2:
        pet_id = parts[2]
        play_with_pet(call, bot_instance, character, pet_id)
    
    elif action == "activate" and len(parts) > 2:
        pet_id = parts[2]
        activate_pet(call, bot_instance, character, pet_id)
    
    elif action == "food":
        show_food_shop(call, bot_instance, character, pets_data)
    
    elif action == "buy_food" and len(parts) > 2:
        food_id = parts[2]
        buy_food(call, bot_instance, character, food_id, pets_data)
    
    elif action == "house":
        show_pet_house(call, bot_instance, character, pets_data)
    
    elif action == "eggs":
        show_eggs(call, bot_instance, character, pets_data)
    
    elif action == "stats":
        show_pet_stats(call, bot_instance, character, pets_data)
    
    elif action == "help":
        show_help(call, bot_instance)
    
    elif action == "upgrade_house":
        bot_instance.answer_callback_query(call.id, "⏳ Улучшение конуры в разработке")
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
