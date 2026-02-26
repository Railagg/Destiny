# /bot/handlers/inventory.py - ПОЛНЫЙ ФАЙЛ ДЛЯ ТЕЛЕГРАМ БОТА
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

def inventory_command(message, bot, get_or_create_player_func, items_data):
    """Команда /inventory - показать инвентарь"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    inventory = character.inventory or []
    
    if not inventory:
        text = "📦 *Инвентарь пуст*\n\n"
        text += "Отправляйся в бой или выполняй квесты, чтобы получить предметы!"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⚔️ В бой", callback_data="combat:choose"))
        keyboard.add(InlineKeyboardButton("🔙 В меню", callback_data="start:menu"))
        
        bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')
        return
    
    # Группируем предметы
    items = {}
    for item_id in inventory:
        if item_id in items:
            items[item_id] += 1
        else:
            items[item_id] = 1
    
    max_slots = 100 + (character.inventory_slots_bonus or 0)
    text = f"📦 *Инвентарь* ({len(inventory)}/{max_slots})\n\n"
    
    # Сортируем по редкости
    rarity_order = {"legendary": "🔴", "epic": "🟣", "rare": "🔵", "uncommon": "🟢", "common": "⚪"}
    
    for item_id, count in items.items():
        item = items_data.get("items", {}).get(item_id, {})
        name = item.get('name', item_id)
        icon = item.get('icon', '📦')
        rarity = item.get('rarity', 'common')
        emoji = rarity_order.get(rarity, '📦')
        
        # Отметка, если предмет надет
        equipped = ""
        if item_id == character.equipped_weapon:
            equipped = " [⚔️ В руке]"
        elif item_id == character.equipped_armor:
            equipped = " [🛡️ Надето]"
        
        text += f"{emoji} {icon} **{name}** x{count}{equipped}\n"
        
        # Добавляем краткое описание для редких предметов
        if rarity in ['legendary', 'epic'] and item.get('description'):
            desc = item['description'][:50] + "..." if len(item['description']) > 50 else item['description']
            text += f"  └ {desc}\n"
    
    # Информация об экипировке
    text += "\n**⚔️ Экипировка:**\n"
    
    if character.equipped_weapon:
        weapon = items_data.get("items", {}).get(character.equipped_weapon, {})
        weapon_name = weapon.get('name', character.equipped_weapon)
        weapon_damage = weapon.get('damage', 0)
        text += f"• Оружие: {weapon_name} (⚔️ {weapon_damage})\n"
    else:
        text += "• Оружие: пусто\n"
    
    if character.equipped_armor:
        armor = items_data.get("items", {}).get(character.equipped_armor, {})
        armor_name = armor.get('name', character.equipped_armor)
        armor_defense = armor.get('defense', 0)
        text += f"• Броня: {armor_name} (🛡️ {armor_defense})\n"
    else:
        text += "• Броня: пусто\n"
    
    # Клавиатура
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🔧 Использовать", callback_data="inventory:use"),
        InlineKeyboardButton("⚔️ Экипировать", callback_data="inventory:equip_list"),
        InlineKeyboardButton("💊 Зелья", callback_data="inventory:potions"),
        InlineKeyboardButton("📦 Сундуки", callback_data="inventory:chests"),
        InlineKeyboardButton("💰 Продать", callback_data="inventory:sell"),
        InlineKeyboardButton("🔙 В меню", callback_data="start:menu")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='Markdown')

def use_item_command(message, bot, get_or_create_player_func, items_data):
    """Команда /use_item - использовать предмет"""
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Укажи ID предмета\n"
            "Пример: /use_item health_potion\n"
            "Список предметов: /inventory",
            parse_mode='Markdown'
        )
        return
    
    item_id = args[1]
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    inventory = character.inventory or []
    
    if item_id not in inventory:
        bot.send_message(message.chat.id, "❌ У тебя нет такого предмета!")
        return
    
    item = items_data.get("items", {}).get(item_id, {})
    
    if not item:
        bot.send_message(message.chat.id, "❌ Предмет не найден в базе данных!")
        return
    
    item_type = item.get('type', 'unknown')
    item_name = item.get('name', item_id)
    
    # Обработка разных типов предметов
    if item_type == 'potion' or 'health' in item_id.lower():
        # Зелье здоровья
        heal_amount = item.get('heal', 50)
        old_health = character.health
        character.health = min(character.max_health, character.health + heal_amount)
        healed = character.health - old_health
        
        # Удаляем предмет
        inventory.remove(item_id)
        character.inventory = inventory
        
        from main import save_character
        save_character(character)
        
        bot.send_message(
            message.chat.id,
            f"✅ Использовано **{item_name}**!\n"
            f"❤️ Восстановлено **{healed}** здоровья.\n"
            f"❤️ Текущее здоровье: {character.health}/{character.max_health}",
            parse_mode='Markdown'
        )
    
    elif item_type == 'mana_potion' or 'mana' in item_id.lower():
        # Зелье маны
        mana_amount = item.get('mana', 30)
        old_mana = character.mana
        character.mana = min(character.max_mana, character.mana + mana_amount)
        restored = character.mana - old_mana
        
        inventory.remove(item_id)
        character.inventory = inventory
        
        from main import save_character
        save_character(character)
        
        bot.send_message(
            message.chat.id,
            f"✅ Использовано **{item_name}**!\n"
            f"💙 Восстановлено **{restored}** маны.\n"
            f"💙 Текущая мана: {character.mana}/{character.max_mana}",
            parse_mode='Markdown'
        )
    
    elif item_type == 'food':
        # Еда (можно использовать или покормить питомца)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("👤 Съесть самому", callback_data=f"item:eat:{item_id}"),
            InlineKeyboardButton("🐾 Покормить питомца", callback_data=f"pet:feed:{item_id}")
        )
        
        bot.send_message(
            message.chat.id,
            f"🍖 **{item_name}**\n"
            f"Что хочешь сделать?",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif item_type == 'key' or 'chest_key' in item_id.lower():
        # Ключ от сундука
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(
            "🎁 Открыть сундук", 
            callback_data=f"chest:open:{item_id}"
        ))
        
        bot.send_message(
            message.chat.id,
            f"🔑 У тебя есть **{item_name}**!\n"
            f"Хочешь открыть сундук?",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif item_type == 'scroll':
        # Свиток
        effect = item.get('effect', 'teleport')
        
        if effect == 'teleport':
            # Свиток телепортации
            from utils import locations_data
            locations = locations_data.get("locations", {})
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            for loc_id, loc in list(locations.items())[:6]:
                loc_name = loc.get('name', loc_id)
                keyboard.add(InlineKeyboardButton(
                    f"📍 {loc_name}", 
                    callback_data=f"teleport:{item_id}:{loc_id}"
                ))
            
            bot.send_message(
                message.chat.id,
                f"📜 **{item_name}**\n"
                f"Куда хотите телепортироваться?",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                message.chat.id,
                f"📜 Свиток активирован!",
                parse_mode='Markdown'
            )
            # Удаляем свиток
            inventory.remove(item_id)
            character.inventory = inventory
            save_character(character)
    
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Предмет '{item_name}' нельзя использовать напрямую.\n"
            f"Тип предмета: {item_type}",
            parse_mode='Markdown'
        )

def equip_item_command(message, bot, get_or_create_player_func, items_data):
    """Команда /equip_item - надеть предмет"""
    args = message.text.split()
    if len(args) < 3:
        bot.send_message(
            message.chat.id,
            "❌ Укажи ID предмета и слот\n"
            "Пример: /equip_item sword_iron weapon\n"
            "Слоты: weapon (оружие), armor (броня)",
            parse_mode='Markdown'
        )
        return
    
    item_id = args[1]
    slot = args[2].lower()
    
    if slot not in ["weapon", "armor"]:
        bot.send_message(message.chat.id, "❌ Неверный слот. Используй: weapon или armor")
        return
    
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    inventory = character.inventory or []
    
    if item_id not in inventory:
        bot.send_message(message.chat.id, "❌ У тебя нет такого предмета!")
        return
    
    item = items_data.get("items", {}).get(item_id, {})
    
    if not item:
        bot.send_message(message.chat.id, "❌ Предмет не найден!")
        return
    
    item_type = item.get('type')
    item_name = item.get('name', item_id)
    
    # Проверяем тип предмета
    if slot == "weapon" and item_type != "weapon":
        bot.send_message(message.chat.id, f"❌ {item_name} не является оружием!")
        return
    
    if slot == "armor" and item_type != "armor":
        bot.send_message(message.chat.id, f"❌ {item_name} не является броней!")
        return
    
    # Снимаем старый предмет (он возвращается в инвентарь)
    old_item = None
    if slot == "weapon" and character.equipped_weapon:
        old_item = character.equipped_weapon
        character.equipped_weapon = None
    elif slot == "armor" and character.equipped_armor:
        old_item = character.equipped_armor
        character.equipped_armor = None
    
    # Надеваем новый
    if slot == "weapon":
        character.equipped_weapon = item_id
    elif slot == "armor":
        character.equipped_armor = item_id
    
    # Удаляем предмет из инвентаря (он теперь надет)
    inventory.remove(item_id)
    
    # Если был старый предмет, возвращаем его в инвентарь
    if old_item:
        inventory.append(old_item)
    
    character.inventory = inventory
    
    from main import save_character
    save_character(character)
    
    old_item_text = f"\n📦 Старый предмет снят и вернулся в инвентарь." if old_item else ""
    
    bot.send_message(
        message.chat.id,
        f"✅ **{item_name}** надет в слот {slot}!{old_item_text}",
        parse_mode='Markdown'
    )

def unequip_item_command(message, bot, get_or_create_player_func, items_data):
    """Команда /unequip_item - снять предмет"""
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Укажи слот\n"
            "Пример: /unequip_item weapon\n"
            "Слоты: weapon, armor",
            parse_mode='Markdown'
        )
        return
    
    slot = args[1].lower()
    
    if slot not in ["weapon", "armor"]:
        bot.send_message(message.chat.id, "❌ Неверный слот. Используй: weapon или armor")
        return
    
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    old_item = None
    if slot == "weapon" and character.equipped_weapon:
        old_item = character.equipped_weapon
        character.equipped_weapon = None
    elif slot == "armor" and character.equipped_armor:
        old_item = character.equipped_armor
        character.equipped_armor = None
    else:
        bot.send_message(message.chat.id, f"❌ В слоте {slot} нет предмета!")
        return
    
    # Возвращаем предмет в инвентарь
    inventory = character.inventory or []
    inventory.append(old_item)
    character.inventory = inventory
    
    from main import save_character
    save_character(character)
    
    item = items_data.get("items", {}).get(old_item, {})
    item_name = item.get('name', old_item)
    
    bot.send_message(
        message.chat.id,
        f"✅ **{item_name}** снят со слота {slot} и возвращён в инвентарь!",
        parse_mode='Markdown'
    )

def sell_item_command(message, bot, get_or_create_player_func, items_data):
    """Команда /sell_item - продать предмет"""
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Укажи ID предмета\n"
            "Пример: /sell_item health_potion\n"
            "Пример с количеством: /sell_item health_potion 5",
            parse_mode='Markdown'
        )
        return
    
    item_id = args[1]
    count = 1
    if len(args) >= 3:
        try:
            count = int(args[2])
        except ValueError:
            bot.send_message(message.chat.id, "❌ Количество должно быть числом!")
            return
    
    if count < 1:
        bot.send_message(message.chat.id, "❌ Количество должно быть положительным!")
        return
    
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    inventory = character.inventory or []
    
    # Проверяем, сколько предметов есть
    item_count = inventory.count(item_id)
    if item_count < count:
        bot.send_message(
            message.chat.id,
            f"❌ У тебя только {item_count} предметов {item_id}!",
            parse_mode='Markdown'
        )
        return
    
    item = items_data.get("items", {}).get(item_id, {})
    item_name = item.get('name', item_id)
    item_value = item.get('value', 10)  # Базовая цена продажи
    
    # Проверяем, не надет ли предмет
    is_equipped = (item_id == character.equipped_weapon or item_id == character.equipped_armor)
    if is_equipped and count > 0:
        bot.send_message(
            message.chat.id,
            f"❌ Нельзя продать надетый предмет! Сначала сними его командой /unequip_item",
            parse_mode='Markdown'
        )
        return
    
    total_gold = item_value * count
    
    # Удаляем предметы
    removed = 0
    new_inventory = []
    for inv_item in inventory:
        if inv_item == item_id and removed < count:
            removed += 1
        else:
            new_inventory.append(inv_item)
    
    character.inventory = new_inventory
    character.gold += total_gold
    
    from main import save_character
    save_character(character)
    
    bot.send_message(
        message.chat.id,
        f"💰 Продано **{item_name}** x{count} за **{total_gold}** золота!\n"
        f"💰 Текущее золото: {character.gold}",
        parse_mode='Markdown'
    )

def potions_list(message, bot, get_or_create_player_func, items_data):
    """Показать список зелий в инвентаре"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    inventory = character.inventory or []
    
    # Собираем все зелья
    potions = {}
    for item_id in inventory:
        item = items_data.get("items", {}).get(item_id, {})
        if item.get('type') == 'potion' or 'potion' in item_id.lower() or 'health' in item_id.lower() or 'mana' in item_id.lower():
            if item_id in potions:
                potions[item_id] += 1
            else:
                potions[item_id] = 1
    
    if not potions:
        bot.send_message(
            message.chat.id,
            "🧪 У тебя нет зелий в инвентаре!",
            parse_mode='Markdown'
        )
        return
    
    text = "🧪 *Твои зелья*\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for item_id, count in potions.items():
        item = items_data.get("items", {}).get(item_id, {})
        name = item.get('name', item_id)
        icon = item.get('icon', '🧪')
        heal = item.get('heal', 0)
        mana = item.get('mana', 0)
        
        effect = ""
        if heal > 0:
            effect = f"❤️ +{heal}"
        elif mana > 0:
            effect = f"💙 +{mana}"
        
        text += f"{icon} **{name}** x{count} {effect}\n"
        
        keyboard.add(InlineKeyboardButton(
            f"{icon} {name} x{count}", 
            callback_data=f"item:use:{item_id}"
        ))
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="inventory:back"))
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

def chests_list(message, bot, get_or_create_player_func, items_data):
    """Показать список ключей и сундуков"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    inventory = character.inventory or []
    
    # Собираем ключи
    keys = {}
    for item_id in inventory:
        item = items_data.get("items", {}).get(item_id, {})
        if item.get('type') == 'key' or 'key' in item_id.lower() or 'chest' in item_id.lower():
            if item_id in keys:
                keys[item_id] += 1
            else:
                keys[item_id] = 1
    
    if not keys:
        bot.send_message(
            message.chat.id,
            "🔑 У тебя нет ключей или сундуков!",
            parse_mode='Markdown'
        )
        return
    
    text = "🔑 *Ключи и сундуки*\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for item_id, count in keys.items():
        item = items_data.get("items", {}).get(item_id, {})
        name = item.get('name', item_id)
        icon = item.get('icon', '🔑')
        
        text += f"{icon} **{name}** x{count}\n"
        
        keyboard.add(InlineKeyboardButton(
            f"{icon} {name} x{count}", 
            callback_data=f"item:use:{item_id}"
        ))
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="inventory:back"))
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

def handle_callback(call, bot, get_or_create_player_func, items_data):
    """Обработчик callback-запросов для инвентаря"""
    data = call.data
    
    if data == "inventory:back":
        inventory_command(call.message, bot, get_or_create_player_func, items_data)
    
    elif data == "inventory:use":
        user_id = call.from_user.id
        user, character = get_or_create_player_func(user_id)
        
        inventory = character.inventory or []
        
        if not inventory:
            bot.answer_callback_query(call.id, "❌ Инвентарь пуст!")
            return
        
        # Группируем предметы
        items = {}
        for item_id in inventory:
            if item_id in items:
                items[item_id] += 1
            else:
                items[item_id] = 1
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for item_id, count in list(items.items())[:10]:  # Показываем первые 10
            item = items_data.get("items", {}).get(item_id, {})
            name = item.get('name', item_id)
            icon = item.get('icon', '📦')
            
            keyboard.add(InlineKeyboardButton(
                f"{icon} {name} x{count}", 
                callback_data=f"item:use:{item_id}"
            ))
        
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="inventory:back"))
        
        bot.edit_message_text(
            "🔧 Выбери предмет для использования:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif data == "inventory:equip_list":
        user_id = call.from_user.id
        user, character = get_or_create_player_func(user_id)
        
        inventory = character.inventory or []
        
        if not inventory:
            bot.answer_callback_query(call.id, "❌ Инвентарь пуст!")
            return
        
        # Группируем предметы
        items = {}
        for item_id in inventory:
            item = items_data.get("items", {}).get(item_id, {})
            item_type = item.get('type', 'unknown')
            
            # Показываем только оружие и броню
            if item_type in ['weapon', 'armor']:
                if item_id in items:
                    items[item_id] += 1
                else:
                    items[item_id] = 1
        
        if not items:
            bot.answer_callback_query(call.id, "❌ Нет предметов для экипировки!")
            return
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for item_id, count in items.items():
            item = items_data.get("items", {}).get(item_id, {})
            name = item.get('name', item_id)
            icon = item.get('icon', '📦')
            item_type = item.get('type', 'unknown')
            type_icon = "⚔️" if item_type == 'weapon' else "🛡️"
            
            keyboard.add(InlineKeyboardButton(
                f"{type_icon} {icon} {name} x{count}", 
                callback_data=f"item:equip:{item_id}"
            ))
        
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="inventory:back"))
        
        bot.edit_message_text(
            "⚔️ Выбери предмет для экипировки:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif data == "inventory:potions":
        potions_list(call.message, bot, get_or_create_player_func, items_data)
    
    elif data == "inventory:chests":
        chests_list(call.message, bot, get_or_create_player_func, items_data)
    
    elif data == "inventory:sell":
        user_id = call.from_user.id
        user, character = get_or_create_player_func(user_id)
        
        inventory = character.inventory or []
        
        if not inventory:
            bot.answer_callback_query(call.id, "❌ Инвентарь пуст!")
            return
        
        # Группируем предметы
        items = {}
        for item_id in inventory:
            if item_id in items:
                items[item_id] += 1
            else:
                items[item_id] = 1
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for item_id, count in list(items.items())[:10]:  # Показываем первые 10
            item = items_data.get("items", {}).get(item_id, {})
            name = item.get('name', item_id)
            icon = item.get('icon', '📦')
            value = item.get('value', 10)
            
            keyboard.add(InlineKeyboardButton(
                f"{icon} {name} x{count} (💰 {value} за шт.)", 
                callback_data=f"item:sell:{item_id}"
            ))
        
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="inventory:back"))
        
        bot.edit_message_text(
            "💰 Выбери предмет для продажи:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif data.startswith("item:use:"):
        item_id = data.split(':')[2]
        
        # Создаём контекст с аргументами
        class Context:
            args = [item_id]
            text = f"/use_item {item_id}"
        
        use_item_command(Context(), bot, get_or_create_player_func, items_data)
    
    elif data.startswith("item:equip:"):
        item_id = data.split(':')[2]
        
        # Определяем тип предмета
        item = items_data.get("items", {}).get(item_id, {})
        item_type = item.get('type', 'unknown')
        slot = 'weapon' if item_type == 'weapon' else 'armor'
        
        # Создаём контекст с аргументами
        class Context:
            args = [item_id, slot]
            text = f"/equip_item {item_id} {slot}"
        
        equip_item_command(Context(), bot, get_or_create_player_func, items_data)
    
    elif data.startswith("item:sell:"):
        item_id = data.split(':')[2]
        
        # Создаём контекст с аргументами
        class Context:
            args = [item_id, "1"]
            text = f"/sell_item {item_id} 1"
        
        sell_item_command(Context(), bot, get_or_create_player_func, items_data)
    
    elif data.startswith("item:eat:"):
        item_id = data.split(':')[2]
        
        # Используем как еду (восстанавливает немного здоровья)
        user_id = call.from_user.id
        user, character = get_or_create_player_func(user_id)
        
        inventory = character.inventory or []
        if item_id not in inventory:
            bot.answer_callback_query(call.id, "❌ Предмет не найден!")
            return
        
        item = items_data.get("items", {}).get(item_id, {})
        item_name = item.get('name', item_id)
        heal_amount = item.get('heal', 10)
        
        old_health = character.health
        character.health = min(character.max_health, character.health + heal_amount)
        healed = character.health - old_health
        
        inventory.remove(item_id)
        character.inventory = inventory
        
        from main import save_character
        save_character(character)
        
        bot.answer_callback_query(call.id, f"🍖 Съел {item_name}, +{healed}❤️")
        
        # Обновляем инвентарь
        inventory_command(call.message, bot, get_or_create_player_func, items_data)
    
    else:
        bot.answer_callback_query(call.id, "⏳ В разработке")

# ========== ЭКСПОРТ ==========

__all__ = [
    'inventory_command',
    'use_item_command',
    'equip_item_command',
    'unequip_item_command',
    'sell_item_command',
    'potions_list',
    'chests_list',
    'handle_callback'
]
