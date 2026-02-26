# /bot/handlers/house.py
import logging
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

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
        
        # Показываем характеристики дома
        storage = house_info.get('storage', 20 + (house_level * 10))
        rest_energy = house_info.get('rest', {}).get('energy_gain', 20 + (house_level * 10))
        rest_health = house_info.get('rest', {}).get('health_gain', 10 + (house_level * 5))
        
        text += f"📦 Вместимость сундука: {storage}\n"
        text += f"🛏️ Отдых: +{rest_energy}⚡, +{rest_health}❤️\n\n"
        
        text += "⚡ *Возможности:*\n"
        text += "• 📦 Сундук для хранения\n"
        text += "• 🛏️ Отдых восстанавливает силы\n"
        
        if house_level >= 2:
            text += "• 🔥 Мангал для готовки\n"
        if house_level >= 3:
            text += "• 🪟 Печь для стекла\n"
        if house_level >= 4:
            text += "• ✨ Телепорт\n"
        if house_level >= 5:
            text += "• 🏠 Баня и теплица\n"
            text += "• 🐕 Домик для питомцев\n"
        
        # Показываем алтарь радуги (для крафта камней)
        if house_level >= 5:
            text += f"\n🔮 *Алтарь радуги*\n"
            text += f"🌈 Осколков: {character.rainbow_shards or 0}/9\n"
            if hasattr(character, 'rainbow_craft_end') and character.rainbow_craft_end > int(time.time()):
                remaining = character.rainbow_craft_end - int(time.time())
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                text += f"⏳ Крафт камня: {hours}ч {minutes}м\n"
        
        # Информация об улучшении
        if next_level:
            text += f"\n🔨 *Для улучшения до {house_level + 1} уровня нужно:*\n"
            materials = next_level.get('materials', {})
            if not materials:
                # Если в данных нет материалов, используем стандартные
                materials = {
                    "wood": 200 * house_level,
                    "stone": 200 * house_level,
                    "iron_ingot": 30 * house_level,
                    "glass": 15 * house_level
                }
            
            for material, amount in materials.items():
                # Проверяем, сколько есть
                if hasattr(character, 'inventory'):
                    has_amount = character.inventory.count(material) if character.inventory else 0
                    emoji = "✅" if has_amount >= amount else "❌"
                    text += f"{emoji} • {material}: {has_amount}/{amount}\n"
                else:
                    text += f"• {material}: {amount}\n"
        
        # Кнопки
        markup = InlineKeyboardMarkup(row_width=2)
        
        # Основные кнопки
        markup.add(
            InlineKeyboardButton("📦 Сундук", callback_data="house:storage"),
            InlineKeyboardButton("🛏️ Отдохнуть", callback_data="house:rest")
        )
        
        # Кнопка инвентаря - ВСЕГДА доступна в доме!
        markup.add(InlineKeyboardButton("🎒 Инвентарь", callback_data="game:inventory"))
        
        # Дополнительные кнопки в зависимости от уровня
        additional_buttons = []
        if house_level >= 2:
            additional_buttons.append(InlineKeyboardButton("🔥 Мангал", callback_data="house:grill"))
        if house_level >= 3:
            additional_buttons.append(InlineKeyboardButton("🪟 Печь", callback_data="house:furnace"))
        if house_level >= 4:
            additional_buttons.append(InlineKeyboardButton("✨ Телепорт", callback_data="house:teleport"))
        if house_level >= 5:
            additional_buttons.append(InlineKeyboardButton("🏠 Баня", callback_data="house:bath"))
            additional_buttons.append(InlineKeyboardButton("🌱 Теплица", callback_data="house:greenhouse"))
            additional_buttons.append(InlineKeyboardButton("🐕 Питомцы", callback_data="house:pets"))
        
        # Добавляем кнопки парами
        for i in range(0, len(additional_buttons), 2):
            if i + 1 < len(additional_buttons):
                markup.add(additional_buttons[i], additional_buttons[i+1])
            else:
                markup.add(additional_buttons[i])
        
        # Кнопка улучшения
        if next_level:
            markup.add(InlineKeyboardButton("🔨 Улучшить", callback_data="house:upgrade"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def build_house(message, bot, get_or_create_player, house_data, items_data):
    """Построить домик"""
    from main import save_character
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    required = {
        "wood": 100,
        "stone": 100,
        "iron_ingot": 20,
        "glass": 10
    }
    
    missing = []
    for material, amount in required.items():
        count = character.inventory.count(material) if character.inventory else 0
        if count < amount:
            material_name = items_data.get("items", {}).get(material, {}).get('name', material)
            missing.append(f"{material_name}: нужно {amount}, есть {count}")
    
    if missing:
        text = "❌ *Не хватает ресурсов:*\n\n" + "\n".join(missing)
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return
    
    # Тратим ресурсы
    for material, amount in required.items():
        for _ in range(amount):
            character.remove_item(material)
    
    character.house_level = 1
    character.house_furniture = []
    character.house_buildings = {}
    save_character(character)
    
    text = "🎉 *Домик построен!*\n\n"
    text += "Теперь у тебя есть свой уголок на берегу озера.\n"
    text += "В домике ты можешь:\n"
    text += "• 🛏️ Отдыхать и восстанавливать силы\n"
    text += "• 📦 Хранить предметы в сундуке\n"
    text += "• 🎒 Открывать инвентарь"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏠 Войти в домик", callback_data="house:enter"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_storage(call, bot, get_or_create_player, items_data):
    """Показать содержимое сундука"""
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    storage = character.house_furniture if character.house_furniture else []
    
    if not storage:
        text = "📦 *Сундук пуст*\n\n"
        text += "Положи предметы, чтобы освободить инвентарь!"
    else:
        text = "📦 *Содержимое сундука:*\n\n"
        items_count = {}
        for item_id in storage:
            items_count[item_id] = items_count.get(item_id, 0) + 1
        
        for item_id, count in items_count.items():
            item_data = items_data.get("items", {}).get(item_id, {})
            item_name = item_data.get('name', item_id)
            rarity = item_data.get('rarity', 'common')
            rarity_emoji = {
                'common': '⚪',
                'uncommon': '🟢',
                'rare': '🔵',
                'epic': '🟣',
                'legendary': '🟡',
                'ancient': '🔴'
            }.get(rarity, '⚪')
            
            text += f"• {rarity_emoji} {item_name} x{count}\n"
    
    text += f"\n📊 Всего предметов: {len(storage)}"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📥 Положить", callback_data="house:storage_deposit"),
        InlineKeyboardButton("📤 Взять", callback_data="house:storage_withdraw"),
        InlineKeyboardButton("🎒 Инвентарь", callback_data="game:inventory")
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
    from main import save_character
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Проверяем кулдаун
    cooldown = 3600  # 1 час
    now = int(time.time())
    last_rest = character.last_rest_time or 0
    
    if now - last_rest < cooldown:
        remaining = cooldown - (now - last_rest)
        minutes = remaining // 60
        bot.answer_callback_query(call.id, f"⏳ Отдых ещё не доступен. Подожди {minutes} мин.")
        return
    
    house_level = character.house_level or 1
    
    # Базовое восстановление
    energy_gain = 20 + (house_level * 10)
    health_gain = 10 + (house_level * 5)
    
    # Бонус от премиума
    if hasattr(character, 'house_rest_multiplier') and character.house_rest_multiplier > 1:
        energy_gain = int(energy_gain * character.house_rest_multiplier)
        health_gain = int(health_gain * character.house_rest_multiplier)
    
    character.energy = min(character.energy + energy_gain, character.max_energy)
    character.health = min(character.health + health_gain, character.max_health)
    character.last_rest_time = now
    
    save_character(character)
    
    bot.answer_callback_query(call.id, f"✅ Отдохнул! +{energy_gain}⚡, +{health_gain}❤️")

def upgrade_house(call, bot, get_or_create_player, house_data, items_data):
    """Улучшить домик"""
    from main import save_character
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    current_level = character.house_level or 1
    next_level = current_level + 1
    
    level_data = house_data.get("house", {}).get("levels", {}).get(str(next_level), {})
    
    if not level_data:
        bot.answer_callback_query(call.id, "❌ Достигнут максимальный уровень")
        return
    
    # Получаем требуемые материалы
    materials = level_data.get('materials', {})
    if not materials:
        # Стандартные требования
        materials = {
            "wood": 200 * current_level,
            "stone": 200 * current_level,
            "iron_ingot": 30 * current_level,
            "glass": 15 * current_level
        }
    
    # Проверяем наличие
    missing = []
    for material, amount in materials.items():
        count = character.inventory.count(material) if character.inventory else 0
        if count < amount:
            material_name = items_data.get("items", {}).get(material, {}).get('name', material)
            missing.append(f"{material_name}: нужно {amount}, есть {count}")
    
    if missing:
        text = "❌ *Не хватает ресурсов:*\n\n" + "\n".join(missing)
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        return
    
    # Тратим ресурсы
    for material, amount in materials.items():
        for _ in range(amount):
            character.remove_item(material)
    
    character.house_level = next_level
    save_character(character)
    
    bot.answer_callback_query(call.id, f"✅ Домик улучшен до {next_level} уровня!")
    
    # Обновляем отображение
    house_command(call.message, bot, get_or_create_player, house_data)

def storage_deposit(call, bot, get_or_create_player, items_data):
    """Положить предмет в сундук"""
    # TODO: Реализовать выбор предмета из инвентаря
    bot.answer_callback_query(call.id, "⏳ Функция в разработке")

def storage_withdraw(call, bot, get_or_create_player, items_data):
    """Взять предмет из сундука"""
    # TODO: Реализовать выбор предмета из сундука
    bot.answer_callback_query(call.id, "⏳ Функция в разработке")

def handle_callback(call, bot, get_or_create_player, house_data, items_data):
    """Обработчик колбэков для домика"""
    try:
        data = call.data.split(':')
        action = data[1]
        
        if action == "back":
            house_command(call.message, bot, get_or_create_player, house_data)
        
        elif action == "build":
            build_house(call.message, bot, get_or_create_player, house_data, items_data)
        
        elif action == "storage":
            show_storage(call, bot, get_or_create_player, items_data)
        
        elif action == "rest":
            house_rest(call, bot, get_or_create_player)
        
        elif action == "upgrade":
            upgrade_house(call, bot, get_or_create_player, house_data, items_data)
        
        elif action == "enter":
            house_command(call.message, bot, get_or_create_player, house_data)
        
        elif action == "storage_deposit":
            storage_deposit(call, bot, get_or_create_player, items_data)
        
        elif action == "storage_withdraw":
            storage_withdraw(call, bot, get_or_create_player, items_data)
        
        elif action in ["grill", "furnace", "teleport", "bath", "greenhouse", "pets"]:
            bot.answer_callback_query(call.id, f"⏳ {action} в разработке")
        
        else:
            bot.answer_callback_query(call.id, "❌ Неизвестное действие")
    
    except Exception as e:
        logging.error(f"Ошибка в house callback: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка")

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'house_command',
    'handle_callback'
]
