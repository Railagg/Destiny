import logging
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def craft_command(message, bot, get_or_create_player, crafting_data, items_data):
    """Показать доступные рецепты"""
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    if not crafting_data:
        bot.send_message(message.chat.id, "❌ Данные крафта не загружены")
        return
    
    text = "🔨 *Мастерская*\n\n"
    text += f"⚡ Твоя энергия: {character.energy}/{character.max_energy}\n"
    text += f"🔮 Уровень крафта: {character.crafting_level or 1}\n\n"
    text += "Выбери категорию для крафта:\n\n"
    
    categories = {
        "weapons": "⚔️ Оружие",
        "shields": "🛡️ Щиты",
        "armor": "🛡️ Броня",
        "tools": "🛠️ Инструменты",
        "potions": "⚗️ Зелья",
        "food": "🍲 Еда",
        "special": "✨ Особое"
    }
    
    # Добавляем радужный крафт, если есть алтарь
    if character.house_level >= 5:
        categories["rainbow"] = "🌈 Радужный крафт"
    
    markup = InlineKeyboardMarkup(row_width=2)
    for cat_id, cat_name in categories.items():
        markup.add(InlineKeyboardButton(cat_name, callback_data=f"craft:category:{cat_id}"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_category(call, bot, get_or_create_player, crafting_data, items_data, category):
    """Показать рецепты в категории"""
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    text = f"🔨 *Доступные рецепты*\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    if category == "rainbow":
        # Специальная обработка для радужного крафта
        show_rainbow_category(call, bot, character, items_data)
        return
    elif category == "special":
        # Особые рецепты (включая радужный камень из осколков)
        show_special_category(call, bot, character, items_data)
        return
    
    category_data = crafting_data.get(category, {})
    if not category_data:
        bot.answer_callback_query(call.id, "❌ Категория пуста")
        return
    
    for subcat_id, subcat_data in category_data.items():
        if isinstance(subcat_data, dict):
            for item_id, recipe in subcat_data.items():
                level_req = recipe.get('level_req', 1)
                name = recipe.get('name', item_id)
                
                if character.level >= level_req:
                    text += f"✅ {name} (ур.{level_req})\n"
                    markup.add(InlineKeyboardButton(
                        f"📌 {name}",
                        callback_data=f"craft:recipe:{category}:{subcat_id}:{item_id}"
                    ))
                else:
                    text += f"❌ {name} (нужен ур.{level_req})\n"
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="craft:back"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id)

def show_rainbow_category(call, bot, character, items_data):
    """Показать рецепты радужного крафта"""
    text = "🌈 *Радужный крафт*\n\n"
    text += f"Твои ресурсы:\n"
    text += f"• 🌈 Осколки: {character.rainbow_shards or 0}\n"
    text += f"• 💎 Радужные камни: {character.rainbow_stones or 0}\n\n"
    
    # Проверяем, есть ли алтарь
    if character.house_level < 5:
        text += "❌ Для радужного крафта нужен Алтарь радуги (5 ур. дома)\n"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="craft:back"))
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, идёт ли крафт камня
    now = int(time.time())
    crafting = hasattr(character, 'rainbow_craft_end') and character.rainbow_craft_end > now
    
    text += "*🔮 Доступные рецепты:*\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Крафт радужного камня из осколков
    if not crafting:
        if character.rainbow_shards >= 9:
            text += f"✅ *Радужный камень* (9 осколков)\n"
            markup.add(InlineKeyboardButton(
                "🔮 Создать камень",
                callback_data="craft:rainbow:craft_stone"
            ))
        else:
            text += f"❌ *Радужный камень* (нужно 9 осколков, есть {character.rainbow_shards or 0})\n"
    else:
        remaining = character.rainbow_craft_end - now
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        text += f"⏳ *Крафт камня*: осталось {hours}ч {minutes}м\n"
    
    # Рецепты из радужных камней
    rainbow_recipes = {
        "legendary_sword": {"name": "⚔️ Легендарный меч", "cost": 1},
        "legendary_armor": {"name": "🛡️ Легендарная броня", "cost": 1},
        "legendary_staff": {"name": "🔮 Легендарный посох", "cost": 1},
        "dragon_sword": {"name": "🐉 Драконий меч", "cost": 2},
        "dragon_armor": {"name": "🐉 Драконья броня", "cost": 2},
        "phoenix_bow": {"name": "🔥 Лук феникса", "cost": 2},
        "divine_blade": {"name": "✨ Божественный клинок", "cost": 3},
        "divine_armor": {"name": "✨ Божественная броня", "cost": 3},
        "mythic_pet_egg": {"name": "🥚 Яйцо мифического питомца", "cost": 2},
        "house_teleport": {"name": "✨ Улучшенный телепорт дома", "cost": 1},
        "rainbow_aura": {"name": "🌟 Радужная аура", "cost": 2}
    }
    
    for recipe_id, recipe in rainbow_recipes.items():
        cost = recipe["cost"]
        can_afford = character.rainbow_stones >= cost
        status = "✅" if can_afford else "❌"
        text += f"{status} *{recipe['name']}* - {cost} 💎\n"
        if can_afford:
            markup.add(InlineKeyboardButton(
                f"🔨 {recipe['name']}",
                callback_data=f"craft:rainbow:recipe:{recipe_id}"
            ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="craft:back"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id)

def show_special_category(call, bot, character, items_data):
    """Показать особые рецепты"""
    text = "✨ *Особые рецепты*\n\n"
    text += f"Твои ресурсы:\n"
    text += f"• 🌈 Осколки: {character.rainbow_shards or 0}\n"
    text += f"• 💎 Радужные камни: {character.rainbow_stones or 0}\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Крафт радужного камня из осколков (доступен с 5 ур. дома)
    if character.house_level >= 5:
        now = int(time.time())
        crafting = hasattr(character, 'rainbow_craft_end') and character.rainbow_craft_end > now
        
        if not crafting:
            if character.rainbow_shards >= 9:
                text += f"✅ *Радужный камень* (9 осколков)\n"
                markup.add(InlineKeyboardButton(
                    "🔮 Создать камень",
                    callback_data="craft:rainbow:craft_stone"
                ))
            else:
                text += f"❌ *Радужный камень* (нужно 9 осколков)\n"
        else:
            remaining = character.rainbow_craft_end - now
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            text += f"⏳ *Крафт камня*: осталось {hours}ч {minutes}м\n"
    else:
        text += f"❌ *Радужный камень* (нужен 5 ур. дома)\n"
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="craft:back"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id)

def craft_rainbow_stone(call, bot, get_or_create_player):
    """Начать крафт радужного камня из осколков"""
    from main import save_character
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Проверяем уровень дома
    if character.house_level < 5:
        bot.answer_callback_query(call.id, "❌ Нужен Алтарь радуги (5 ур. дома)")
        return
    
    # Проверяем наличие осколков
    if character.rainbow_shards < 9:
        bot.answer_callback_query(call.id, f"❌ Нужно 9 осколков, есть {character.rainbow_shards}")
        return
    
    # Проверяем, не крафтится ли уже
    now = int(time.time())
    if hasattr(character, 'rainbow_craft_end') and character.rainbow_craft_end > now:
        remaining = character.rainbow_craft_end - now
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        bot.answer_callback_query(call.id, f"⏳ Уже крафтится! Осталось {hours}ч {minutes}м")
        return
    
    # Запускаем крафт
    character.rainbow_shards -= 9
    character.rainbow_craft_end = now + 86400  # 24 часа
    
    # Добавляем в историю
    if not hasattr(character, 'rainbow_history'):
        character.rainbow_history = []
    character.rainbow_history.append({
        'date': time.strftime('%Y-%m-%d %H:%M'),
        'action': 'start_craft',
        'amount': 9,
        'resource': '🌈'
    })
    
    save_character(character)
    
    bot.answer_callback_query(call.id, "✅ Крафт камня запущен! (24 часа)")
    
    # Возвращаемся в меню радужного крафта
    show_rainbow_category(call, bot, character, None)

def craft_rainbow_recipe(call, bot, get_or_create_player, recipe_id):
    """Создать предмет из радужного камня"""
    from main import save_character
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Рецепты
    rainbow_recipes = {
        "legendary_sword": {"name": "⚔️ Легендарный меч", "cost": 1, "item": "legendary_sword"},
        "legendary_armor": {"name": "🛡️ Легендарная броня", "cost": 1, "item": "legendary_armor"},
        "legendary_staff": {"name": "🔮 Легендарный посох", "cost": 1, "item": "legendary_staff"},
        "dragon_sword": {"name": "🐉 Драконий меч", "cost": 2, "item": "dragon_sword"},
        "dragon_armor": {"name": "🐉 Драконья броня", "cost": 2, "item": "dragon_armor"},
        "phoenix_bow": {"name": "🔥 Лук феникса", "cost": 2, "item": "phoenix_bow"},
        "divine_blade": {"name": "✨ Божественный клинок", "cost": 3, "item": "divine_blade"},
        "divine_armor": {"name": "✨ Божественная броня", "cost": 3, "item": "divine_armor"},
        "mythic_pet_egg": {"name": "🥚 Яйцо мифического питомца", "cost": 2, "item": "mythic_pet_egg"},
        "house_teleport": {"name": "✨ Улучшенный телепорт дома", "cost": 1, "item": "house_teleport_upgrade"},
        "rainbow_aura": {"name": "🌟 Радужная аура", "cost": 2, "aura": True}
    }
    
    recipe = rainbow_recipes.get(recipe_id)
    if not recipe:
        bot.answer_callback_query(call.id, "❌ Рецепт не найден")
        return
    
    # Проверяем наличие камней
    if character.rainbow_stones < recipe["cost"]:
        bot.answer_callback_query(call.id, f"❌ Нужно {recipe['cost']} радужных камней")
        return
    
    # Тратим камни
    character.rainbow_stones -= recipe["cost"]
    character.rainbow_stones_used = (character.rainbow_stones_used or 0) + recipe["cost"]
    
    # Добавляем предмет
    if recipe.get("item"):
        character.add_item(recipe["item"])
    
    # Добавляем ауру
    if recipe.get("aura"):
        character.profile_aura = "rainbow"
    
    # Добавляем в историю
    if not hasattr(character, 'rainbow_history'):
        character.rainbow_history = []
    character.rainbow_history.append({
        'date': time.strftime('%Y-%m-%d %H:%M'),
        'action': f'craft_{recipe_id}',
        'amount': recipe["cost"],
        'resource': '💎'
    })
    
    save_character(character)
    
    bot.answer_callback_query(call.id, f"✅ {recipe['name']} создан!")
    
    # Возвращаемся в меню радужного крафта
    show_rainbow_category(call, bot, character, None)

def show_recipe(call, bot, get_or_create_player, crafting_data, items_data, category, subcategory, item_id):
    """Показать детали рецепта и кнопку крафта"""
    from main import save_character
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    recipe = crafting_data.get(category, {}).get(subcategory, {}).get(item_id, {})
    if not recipe:
        bot.answer_callback_query(call.id, "❌ Рецепт не найден")
        return
    
    level_req = recipe.get('level_req', 1)
    if character.level < level_req:
        bot.answer_callback_query(call.id, f"❌ Нужен уровень {level_req}")
        return
    
    # Проверяем энергию
    energy_cost = recipe.get('energy_cost', 5)
    if character.energy < energy_cost:
        bot.answer_callback_query(call.id, f"❌ Нужно {energy_cost}⚡ энергии")
        return
    
    materials = recipe.get('materials', {})
    missing = []
    for material, amount in materials.items():
        count = character.count_item(material)
        if count < amount:
            material_name = items_data.get("items", {}).get(material, {}).get('name', material)
            missing.append(f"{material_name}: нужно {amount}, есть {count}")
    
    text = f"*{recipe.get('name', item_id)}*\n\n"
    text += f"📊 Требуемый уровень: {level_req}\n"
    text += f"⚡ Энергии: {energy_cost}\n"
    text += f"⏱️ Время: {recipe.get('time', 30)} сек\n\n"
    text += "*📦 Требуется:*\n"
    
    for material, amount in materials.items():
        material_name = items_data.get("items", {}).get(material, {}).get('name', material)
        count = character.count_item(material)
        status = "✅" if count >= amount else "❌"
        text += f"{status} {material_name}: {amount} шт. (есть {count})\n"
    
    markup = InlineKeyboardMarkup()
    if not missing and character.energy >= energy_cost:
        markup.add(InlineKeyboardButton("🔨 Создать", callback_data=f"craft:create:{category}:{subcategory}:{item_id}"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data=f"craft:category:{category}"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id)

def create_item(call, bot, get_or_create_player, crafting_data, items_data, category, subcategory, item_id):
    """Создать предмет"""
    from main import save_character
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    recipe = crafting_data.get(category, {}).get(subcategory, {}).get(item_id, {})
    if not recipe:
        bot.answer_callback_query(call.id, "❌ Рецепт не найден")
        return
    
    level_req = recipe.get('level_req', 1)
    if character.level < level_req:
        bot.answer_callback_query(call.id, f"❌ Нужен уровень {level_req}")
        return
    
    # Проверяем энергию
    energy_cost = recipe.get('energy_cost', 5)
    if character.energy < energy_cost:
        bot.answer_callback_query(call.id, f"❌ Нужно {energy_cost}⚡ энергии")
        return
    
    materials = recipe.get('materials', {})
    for material, amount in materials.items():
        count = character.count_item(material)
        if count < amount:
            bot.answer_callback_query(call.id, f"❌ Не хватает {material}")
            return
    
    # Тратим ресурсы
    for material, amount in materials.items():
        for _ in range(amount):
            character.remove_item(material)
    
    # Тратим энергию
    character.energy -= energy_cost
    
    # Добавляем предмет
    character.add_item(item_id)
    
    # Добавляем опыт крафта
    character.crafting_exp = (character.crafting_exp or 0) + 10
    if character.crafting_exp >= (character.crafting_level or 1) * 100:
        character.crafting_level = (character.crafting_level or 1) + 1
        character.crafting_exp = 0
    
    save_character(character)
    
    bot.answer_callback_query(call.id, "✅ Предмет создан!")
    show_recipe(call, bot, get_or_create_player, crafting_data, items_data, category, subcategory, item_id)

def handle_callback(call, bot, get_or_create_player, crafting_data, items_data):
    """Обработчик колбэков для крафта"""
    try:
        data = call.data.split(':')
        action = data[1]
        
        if action == "back":
            craft_command(call.message, bot, get_or_create_player, crafting_data, items_data)
        
        elif action == "category" and len(data) > 2:
            category = data[2]
            show_category(call, bot, get_or_create_player, crafting_data, items_data, category)
        
        elif action == "recipe" and len(data) > 4:
            category = data[2]
            subcategory = data[3]
            item_id = data[4]
            show_recipe(call, bot, get_or_create_player, crafting_data, items_data, category, subcategory, item_id)
        
        elif action == "create" and len(data) > 4:
            category = data[2]
            subcategory = data[3]
            item_id = data[4]
            create_item(call, bot, get_or_create_player, crafting_data, items_data, category, subcategory, item_id)
        
        elif action == "rainbow" and len(data) > 2:
            if data[2] == "craft_stone":
                craft_rainbow_stone(call, bot, get_or_create_player)
            elif data[2] == "recipe" and len(data) > 3:
                recipe_id = data[3]
                craft_rainbow_recipe(call, bot, get_or_create_player, recipe_id)
            else:
                show_rainbow_category(call, bot, get_or_create_player(call.from_user.id)[1], items_data)
        
        else:
            bot.answer_callback_query(call.id, "❌ Неизвестное действие")
    
    except Exception as e:
        logging.error(f"Ошибка в craft callback: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка")
