import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def house_command(message, bot, get_or_create_player, house_data):
    """Показать информацию о домике"""
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    house_level = character.house_level or 0
    
    if house_level == 0:
        text = "🏗️ *У тебя пока нет домика*\n\n"
        text += "Отправляйся на Берег озера, чтобы построить его!\n"
        text += "Требуется: 100🪵, 100🪨, 20🔩, 10🪟"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏗️ Построить", callback_data="house:build"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
        
    else:
        house_info = house_data.get("house", {}).get("levels", {}).get(str(house_level), {})
        next_level = house_data.get("house", {}).get("levels", {}).get(str(house_level + 1), {})
        
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
        
        if next_level:
            text += f"\n🔨 *Для улучшения до {house_level + 1} уровня нужно:*\n"
            for material, amount in next_level.get('materials', {}).items():
                text += f"• {material}: {amount}\n"
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📦 Сундук", callback_data="house:storage"),
            InlineKeyboardButton("🛏️ Отдохнуть", callback_data="house:rest")
        )
        if next_level:
            markup.add(InlineKeyboardButton("🔨 Улучшить", callback_data="house:upgrade"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def build_house(message, bot, get_or_create_player, house_data, items_data):
    """Построить домик"""
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Проверяем ресурсы
    required = {
        "wood": 100,
        "stone": 100,
        "iron_ingot": 20,
        "glass": 10
    }
    
    missing = []
    for material, amount in required.items():
        count = character.inventory.count(material)
        if count < amount:
            material_name = items_data.get("items", {}).get(material, {}).get('name', material)
            missing.append(f"{material_name}: нужно {amount}, есть {count}")
    
    if missing:
        text = "❌ *Не хватает ресурсов:*\n\n" + "\n".join(missing)
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return
    
    # Забираем ресурсы
    for material, amount in required.items():
        for _ in range(amount):
            character.remove_item(material)
    
    character.house_level = 1
    from main import save_character
    save_character(character)
    
    text = "🎉 *Домик построен!*\n\n"
    text += "Теперь у тебя есть свой уголок на берегу озера."
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏠 Войти в домик", callback_data="house:enter"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_storage(call, bot, get_or_create_player, items_data):
    """Показать содержимое сундука"""
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Временное хранилище (потом добавим отдельное поле в БД)
    storage = character.house_furniture if character.house_furniture else []
    
    if not storage:
        text = "📦 *Сундук пуст*"
    else:
        text = "📦 *Содержимое сундука:*\n\n"
        
        # Группируем предметы
        items_count = {}
        for item_id in storage:
            items_count[item_id] = items_count.get(item_id, 0) + 1
        
        for item_id, count in items_count.items():
            item_name = items_data.get("items", {}).get(item_id, {}).get('name', item_id)
            text += f"• {item_name} x{count}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📥 Положить", callback_data="house:storage_deposit"),
        InlineKeyboardButton("📤 Взять", callback_data="house:storage_withdraw")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="house:back"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id)

def house_rest(call, bot, get_or_create_player):
    """Отдохнуть в домике"""
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Бонусы зависят от уровня дома
    house_level = character.house_level or 0
    energy_gain = 30 + house_level * 10
    health_gain = 20 + house_level * 5
    
    character.energy = min(character.energy + energy_gain, character.max_energy)
    character.health = min(character.health + health_gain, character.max_health)
    
    from main import save_character
    save_character(character)
    
    bot.answer_callback_query(call.id, f"✅ Отдохнул! +{energy_gain}⚡, +{health_gain}❤️")

def handle_callback(call, bot, get_or_create_player, house_data, items_data):
    """Обработчик колбэков для домика"""
    try:
        data = call.data.split(':')
        action = data[1]
        
        if action == "back":
            from main import house_command
            house_command(call.message, bot, get_or_create_player, house_data)
        
        elif action == "build":
            build_house(call.message, bot, get_or_create_player, house_data, items_data)
        
        elif action == "storage":
            show_storage(call, bot, get_or_create_player, items_data)
        
        elif action == "rest":
            house_rest(call, bot, get_or_create_player)
        
        elif action == "upgrade":
            bot.answer_callback_query(call.id, "⏳ Улучшение пока в разработке")
        
        elif action == "enter":
            bot.answer_callback_query(call.id, "🚪 Ты вошёл в домик")
        
        else:
            bot.answer_callback_query(call.id, "❌ Неизвестное действие")
    
    except Exception as e:
        logging.error(f"Ошибка в house callback: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка")
