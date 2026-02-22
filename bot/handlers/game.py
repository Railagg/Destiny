import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import random

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def profile_command(message):
    """Команда /profile - профиль игрока"""
    from main import get_or_create_player, refresh_energy, refresh_magic
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    text = f"👤 *Профиль игрока*\n\n"
    text += f"🆔 ID: {user.telegram_id}\n"
    text += f"📛 Имя: {user.first_name}\n"
    if user.username:
        text += f"📧 Username: @{user.username}\n"
    text += f"\n📊 *Характеристики:*\n"
    text += f"📈 Уровень: {character.level}\n"
    text += f"✨ Опыт: {character.experience}\n"
    if character.player_class:
        text += f"🎭 Класс: {character.player_class} (ур. {character.class_level})\n"
    text += f"📅 В игре с: {user.created_at.strftime('%d.%m.%Y')}\n"
    text += f"📅 Стрик входа: {character.login_streak or 0} дней"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def status_command(message):
    """Команда /status - статус персонажа"""
    from main import get_or_create_player, refresh_energy, refresh_magic, calculate_damage, calculate_defense
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    damage = calculate_damage(character)
    defense = calculate_defense(character)
    
    text = f"⚔️ *Статус персонажа*\n\n"
    text += f"❤️ Здоровье: {character.health}/{character.max_health}\n"
    text += f"⚡ Энергия: {character.energy}/{character.max_energy}\n"
    text += f"🔮 Магия: {character.magic}/{character.max_magic}\n"
    text += f"💰 Золото: {character.gold}\n"
    text += f"🪙 DSTN: {character.destiny_tokens}\n"
    text += f"\n⚔️ Урон: {damage}\n"
    text += f"🛡️ Защита: {defense}\n"
    text += f"🎯 Удача: {character.luck or 0}%\n"
    text += f"⚡ Крит: {character.crit_chance or 0}% (x{character.crit_multiplier or 2})\n"
    text += f"💨 Уклонение: {character.dodge_chance or 0}%\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def inventory_command(message):
    """Команда /inventory - инвентарь"""
    from main import get_or_create_player, items_data
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    inventory = character.get_inventory()
    
    if not inventory:
        text = "🎒 *Инвентарь пуст*"
    else:
        text = "🎒 *Твой инвентарь:*\n\n"
        
        # Группируем предметы
        items_count = {}
        for item_id in inventory:
            if item_id in items_count:
                items_count[item_id] += 1
            else:
                items_count[item_id] = 1
        
        # Показываем с количеством
        for item_id, count in items_count.items():
            if item_id in items_data.get("items", {}):
                item = items_data["items"][item_id]
                text += f"• {item.get('name', item_id)}"
                if count > 1:
                    text += f" x{count}"
                if item.get('rarity'):
                    text += f" ({item['rarity']})"
                text += "\n"
        
        text += f"\n📦 Всего предметов: {len(inventory)}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def location_command(message):
    """Команда /location - текущая локация"""
    from main import get_or_create_player, refresh_energy, refresh_magic, locations_data
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    location_id = character.location
    location = locations_data.get("locations", {}).get(location_id, {})
    
    if not location:
        location = {
            "name": "Неизвестная локация",
            "description": "Ты находишься в неизвестном месте."
        }
    
    text = f"📍 *{location.get('name', 'Локация')}*\n\n"
    text += location.get('description', '')
    text += f"\n\n⚡ Энергия: {character.energy}/{character.max_energy}"
    
    # Добавляем информацию о монстрах
    if location.get('mobs'):
        text += f"\n\n👾 Враги: {', '.join(location['mobs'])}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🗺️ Карта мира", callback_data="game:map"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def map_command(message):
    """Команда /map - карта мира"""
    text = "🗺️ *Карта мира*\n\n"
    text += "🌲 *Начальные локации (1-10)*\n"
    text += "├ Лесная опушка\n"
    text += "├ Деревенская площадь\n"
    text += "└ Берег озера\n\n"
    text += "⛰️ *Средние локации (10-20)*\n"
    text += "├ Горная тропа\n"
    text += "├ Шахта\n"
    text += "└ Древние руины\n\n"
    text += "🔥 *Сложные локации (20-30)*\n"
    text += "├ Жерло вулкана\n"
    text += "├ Логово дракона\n"
    text += "└ Лабиринт\n\n"
    text += "🏜️ *Биомы (30-50)*\n"
    text += "├ Пустыня забвения\n"
    text += "├ Болото туманов\n"
    text += "└ Ледяные равнины"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📍 Текущая локация", callback_data="game:location"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def class_command(message):
    """Команда /class - выбор класса"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    if character.player_class:
        bot.reply_to(message, f"❌ Ты уже выбрал класс: {character.player_class}")
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Мечник", callback_data="game:class:warrior"),
        InlineKeyboardButton("🏹 Лучник", callback_data="game:class:archer"),
        InlineKeyboardButton("🔮 Маг", callback_data="game:class:mage"),
        InlineKeyboardButton("🛡️ Страж", callback_data="game:class:guardian")
    )
    
    bot.send_message(
        message.chat.id,
        "🌟 *Выбери свой класс:*\n\n"
        "⚔️ *Мечник* - высокий урон, криты\n"
        "🏹 *Лучник* - дальний бой, уклонение\n"
        "🔮 *Маг* - магический урон, много маны\n"
        "🛡️ *Страж* - защита, много здоровья",
        reply_markup=markup,
        parse_mode='Markdown'
    )

def craft_command(message):
    """Команда /craft - крафт"""
    text = "🔨 *Крафт предметов*\n\n"
    text += "Выбери категорию:\n\n"
    text += "⚔️ Оружие\n"
    text += "🛡️ Броня\n"
    text += "🛠️ Инструменты\n"
    text += "⚗️ Зелья\n"
    text += "🍲 Еда\n"
    text += "🪱 Наживки"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Оружие", callback_data="game:craft:weapons"),
        InlineKeyboardButton("🛡️ Броня", callback_data="game:craft:armor"),
        InlineKeyboardButton("🛠️ Инструменты", callback_data="game:craft:tools"),
        InlineKeyboardButton("⚗️ Зелья", callback_data="game:craft:potions"),
        InlineKeyboardButton("🍲 Еда", callback_data="game:craft:food"),
        InlineKeyboardButton("🪱 Наживки", callback_data="game:craft:bait")
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
    else:
        house_info = house_data.get("house", {}).get("levels", {}).get(str(house_level), {})
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
    
    markup = InlineKeyboardMarkup()
    if house_level == 0:
        markup.add(InlineKeyboardButton("🏗️ Построить", callback_data="game:house:build"))
    else:
        markup.add(InlineKeyboardButton("🚪 Войти в домик", callback_data="game:house:enter"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func, items_data):
    """Обработка игровых кнопок"""
    from main import save_character, refresh_energy, refresh_magic, calculate_damage, calculate_defense
    
    data = call.data.split(':')
    action = data[1] if len(data) > 1 else ""
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    refresh_energy(character)
    refresh_magic(character)
    
    if action == "back_to_start":
        from .start import start_command
        start_command(call.message)
    
    elif action == "status":
        status_command(call.message)
    
    elif action == "inventory":
        inventory_command(call.message)
    
    elif action == "map":
        map_command(call.message)
    
    elif action == "location":
        location_command(call.message)
    
    elif action.startswith("class:"):
        class_name = action.split(':')[1]
        
        if character.player_class:
            bot_instance.answer_callback_query(call.id, "❌ Ты уже выбрал класс")
            return
        
        character.player_class = class_name
        if class_name == "warrior":
            character.strength = 3
            character.base_damage += 2
        elif class_name == "archer":
            character.dexterity = 3
            character.dodge_chance += 5
        elif class_name == "mage":
            character.intelligence = 3
            character.max_magic += 30
            character.magic += 30
        elif class_name == "guardian":
            character.vitality = 3
            character.max_health += 30
            character.health += 30
            character.defense_bonus += 5
        
        save_character(character)
        bot_instance.answer_callback_query(call.id, f"✅ Ты стал {class_name}!")
        bot_instance.delete_message(call.message.chat.id, call.message.message_id)
        from .start import start_command
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
        
        if craft_type == "weapons":
            items = crafting_data.get("crafting", {}).get("weapons", {}).get("swords", {})
            for item_id, item in items.items():
                if item.get("level_req", 0) <= character.level:
                    text += f"• {item.get('name')} (ур. {item.get('level_req')})\n"
                    mats = item.get('materials', {})
                    text += f"  Требуется: {', '.join([f'{v} {k}' for k, v in mats.items()])}\n"
                    text += f"  ⏱️ {item.get('time', 0)} сек\n\n"
        elif craft_type == "bait":
            items = crafting_data.get("crafting", {}).get("bait", {})
            for item_id, item in items.items():
                text += f"• {item.get('name')}\n"
                if item.get('materials'):
                    mats = item.get('materials', {})
                    text += f"  Требуется: {', '.join([f'{v} {k}' for k, v in mats.items()])}\n"
                else:
                    text += f"  {item.get('description')}\n"
                text += f"  ⏱️ {item.get('time', 0)} сек\n\n"
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
        
        elif house_action == "enter":
            # Вход в домик
            text = f"🏠 *Твой домик (уровень {character.house_level})*\n\n"
            text += "🛏️ *Отдохнуть* - восстановить энергию\n"
            text += "📦 *Сундук* - хранить предметы\n"
            if character.house_level >= 2:
                text += "🔥 *Мангал* - готовить еду\n"
            if character.house_level >= 3:
                text += "🪟 *Печь* - делать стекло\n"
            
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("🛏️ Отдохнуть", callback_data="game:house:rest"),
                InlineKeyboardButton("📦 Сундук", callback_data="game:house:storage")
            )
            if character.house_level >= 2:
                markup.add(InlineKeyboardButton("🔥 Мангал", callback_data="game:house:grill"))
            if character.house_level >= 3:
                markup.add(InlineKeyboardButton("🪟 Печь", callback_data="game:house:furnace"))
            markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:house"))
            
            bot_instance.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        
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
            
            energy_gain = 20 + (character.house_level * 10)
            health_gain = 10 * character.house_level
            
            character.energy = min(character.energy + energy_gain, character.max_energy)
            character.health = min(character.health + health_gain, character.max_health)
            character.last_rest_time = now
            save_character(character)
            
            bot_instance.answer_callback_query(call.id, f"✅ Ты отдохнул! +{energy_gain}⚡, +{health_gain}❤️")
            house_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
