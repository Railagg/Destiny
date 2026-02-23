import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def craft_command(message, bot, get_or_create_player, crafting_data, items_data):
    """Показать доступные рецепты"""
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    if not crafting_data:
        bot.send_message(message.chat.id, "❌ Данные крафта не загружены")
        return
    
    text = "🔨 *Мастерская*\n\n"
    text += "Выбери категорию для крафта:\n\n"
    
    categories = {
        "weapons": "⚔️ Оружие",
        "shields": "🛡️ Щиты",
        "armor": "🛡️ Броня",
        "tools": "🛠️ Инструменты",
        "potions": "⚗️ Зелья",
        "food": "🍲 Еда"
    }
    
    markup = InlineKeyboardMarkup(row_width=2)
    for cat_id, cat_name in categories.items():
        if cat_id in crafting_data:
            markup.add(InlineKeyboardButton(cat_name, callback_data=f"craft:category:{cat_id}"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_category(call, bot, get_or_create_player, crafting_data, items_data, category):
    """Показать рецепты в категории"""
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    category_data = crafting_data.get(category, {})
    if not category_data:
        bot.answer_callback_query(call.id, "❌ Категория пуста")
        return
    
    text = f"🔨 *Доступные рецепты:*\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
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

def show_recipe(call, bot, get_or_create_player, crafting_data, items_data, category, subcategory, item_id):
    """Показать детали рецепта и кнопку крафта"""
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
    
    materials = recipe.get('materials', {})
    missing = []
    for material, amount in materials.items():
        count = character.inventory.count(material)
        if count < amount:
            material_name = items_data.get("items", {}).get(material, {}).get('name', material)
            missing.append(f"{material_name}: нужно {amount}, есть {count}")
    
    text = f"*{recipe.get('name', item_id)}*\n\n"
    text += f"📊 Уровень: {level_req}\n"
    text += f"⚡ Время: {recipe.get('time', 30)} сек\n\n"
    text += "*📦 Требуется:*\n"
    
    for material, amount in materials.items():
        material_name = items_data.get("items", {}).get(material, {}).get('name', material)
        count = character.inventory.count(material)
        status = "✅" if count >= amount else "❌"
        text += f"{status} {material_name}: {amount} шт. (есть {count})\n"
    
    markup = InlineKeyboardMarkup()
    if not missing:
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
    
    materials = recipe.get('materials', {})
    for material, amount in materials.items():
        for _ in range(amount):
            character.remove_item(material)
    
    character.add_item(item_id)
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
        
        else:
            bot.answer_callback_query(call.id, "❌ Неизвестное действие")
    
    except Exception as e:
        logging.error(f"Ошибка в craft callback: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка")
