# /bot/handlers/rainbow.py
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import time
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ РАДУЖНОЙ СИСТЕМЫ
# ============================================

RAINBOW_INFO = {
    "shards_per_stone": 9,
    "craft_time": 86400,  # 24 часа
    "min_house_level": 5,
    "shard_sources": {
        "daily_login": {"day3": 1, "day6": 1},  # Только 3 и 6 день
        "bosses": {"chance": 10},  # 10% шанс с боссов
        "events": {"rainbow_thursday": 2.0},  # Шанс x2 в день радуги
        "achievements": {"rainbow_master": 10}  # Достижение даёт осколки
    },
    "stone_sources": {
        "craft": 9,  # 9 осколков
        "premium_shop": {"price_stars": 500, "price_ton": 9},
        "yearly_subscription": 1,
        "legendary_achievement": 1
    }
}

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

def rainbow_command(message, bot_instance, get_or_create_player_func, rainbow_data):
    """Команда /rainbow - радужные камни"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Получаем количество осколков и камней
    rainbow_shards = character.rainbow_shards if hasattr(character, 'rainbow_shards') else 0
    rainbow_stones = character.rainbow_stones if hasattr(character, 'rainbow_stones') else 0
    
    # Проверяем, есть ли активный крафт
    craft_end = character.rainbow_craft_end if hasattr(character, 'rainbow_craft_end') else 0
    now = int(time.time())
    crafting = craft_end > now
    
    text = "🌈 *СИСТЕМА РАДУЖНЫХ КАМНЕЙ*\n\n"
    text += "Собирай осколки и создавай легендарные радужные камни!\n\n"
    
    # Статистика
    text += f"📊 *Твои ресурсы:*\n"
    text += f"• 🌈 Осколки: {rainbow_shards}\n"
    text += f"• 💎 Радужные камни: {rainbow_stones}\n\n"
    
    # Информация о получении
    text += "📅 *Как получить осколки:*\n"
    text += "• 3-й день входа: +1 осколок\n"
    text += "• 6-й день входа: +1 осколок\n"
    text += "• Боссы: 10% шанс\n"
    text += "• Ивенты: повышенный шанс\n"
    text += "• Достижения: награда осколками\n\n"
    
    # Крафт камня
    text += "🔮 *Создание радужного камня:*\n"
    text += f"• {RAINBOW_INFO['shards_per_stone']} осколков = 1 💎 камень\n"
    text += f"• Время крафта: {RAINBOW_INFO['craft_time'] // 3600} часов\n"
    text += f"• Требование: {RAINBOW_INFO['min_house_level']} уровень дома\n\n"
    
    if crafting:
        remaining = craft_end - now
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        text += f"⏳ *Крафт в процессе:* осталось {hours}ч {minutes}м\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    if rainbow_shards >= RAINBOW_INFO['shards_per_stone'] and character.house_level >= RAINBOW_INFO['min_house_level'] and not crafting:
        markup.add(InlineKeyboardButton("🔮 Начать крафт", callback_data="rainbow:craft_start"))
    
    markup.add(
        InlineKeyboardButton("📜 Рецепты", callback_data="rainbow:recipes"),
        InlineKeyboardButton("🏆 Достижения", callback_data="rainbow:achievements"),
        InlineKeyboardButton("🏠 Магазин", callback_data="rainbow:shop"),
        InlineKeyboardButton("📊 История", callback_data="rainbow:history"),
        InlineKeyboardButton("ℹ️ Подробнее", callback_data="rainbow:info")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_recipes(call, bot_instance, character, rainbow_data):
    """Показать рецепты из радужных камней"""
    recipes = rainbow_data.get("rainbow", {}).get("recipes", {})
    rainbow_stones = character.rainbow_stones if hasattr(character, 'rainbow_stones') else 0
    
    text = "📜 *РЕЦЕПТЫ ИЗ РАДУЖНЫХ КАМНЕЙ*\n\n"
    text += f"У тебя: {rainbow_stones} 💎\n\n"
    
    for recipe_id, recipe in recipes.items():
        name = recipe.get('name', recipe_id)
        cost = recipe.get('cost', 1)
        description = recipe.get('description', '')
        
        can_afford = "✅" if rainbow_stones >= cost else "❌"
        text += f"{can_afford} *{name}* - {cost} 💎\n"
        text += f"  {description}\n"
        
        if recipe.get('items'):
            text += f"  🎁 Награда: {', '.join(recipe['items'])}\n"
        
        text += "\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Кнопки для крафта доступных рецептов
    for recipe_id, recipe in recipes.items():
        cost = recipe.get('cost', 1)
        if rainbow_stones >= cost:
            markup.add(InlineKeyboardButton(
                f"🔨 {recipe.get('name')}",
                callback_data=f"rainbow:craft_recipe:{recipe_id}"
            ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_achievements(call, bot_instance, character, rainbow_data):
    """Показать достижения за радужные камни"""
    achievements = rainbow_data.get("rainbow", {}).get("achievements", {})
    
    # Получаем прогресс игрока
    rainbow_shards_collected = character.rainbow_shards_collected if hasattr(character, 'rainbow_shards_collected') else 0
    rainbow_stones_used = character.rainbow_stones_used if hasattr(character, 'rainbow_stones_used') else 0
    
    text = "🏆 *ДОСТИЖЕНИЯ ЗА РАДУЖНЫЕ КАМНИ*\n\n"
    
    for ach_id, ach in achievements.items():
        name = ach.get('name', ach_id)
        requirement = ach.get('requirement', '')
        reward = ach.get('reward', {})
        
        # Проверяем, выполнено ли
        completed = ach_id in (character.event_achievements or [])
        status = "✅" if completed else "⏳"
        
        text += f"{status} *{name}*\n"
        text += f"  {requirement}\n"
        
        if reward:
            rewards = []
            if reward.get('title'):
                rewards.append(f"титул '{reward['title']}'")
            if reward.get('rainbow_shard'):
                rewards.append(f"{reward['rainbow_shard']}🌈")
            if reward.get('rainbow_stone'):
                rewards.append(f"{reward['rainbow_stone']}💎")
            if reward.get('aura'):
                rewards.append("аура")
            if rewards:
                text += f"  🎁 {', '.join(rewards)}\n"
        
        text += "\n"
    
    # Прогресс
    text += f"📊 Собрано осколков: {rainbow_shards_collected}\n"
    text += f"🔨 Использовано камней: {rainbow_stones_used}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_shop(call, bot_instance, character, rainbow_data):
    """Показать магазин радужных камней (премиум)"""
    from main import premium_data
    
    text = "🏠 *МАГАЗИН РАДУЖНЫХ КАМНЕЙ*\n\n"
    text += "Радужные камни можно приобрести только за премиум-валюту!\n\n"
    
    # Информация о курсе
    text += "💎 *Цены:*\n"
    text += "• 1 радужный камень = 500 ⭐ или 9 TON\n"
    text += "• 3 радужных камня = 1400 ⭐ (скидка 7%)\n"
    text += "• 5 радужных камней = 2200 ⭐ (скидка 12%)\n\n"
    
    text += "✨ *Также можно получить:*\n"
    text += "• Годовая подписка: +1 камень\n"
    text += "• Достижение 'Повелитель радуги': +1 камень\n"
    text += "• Крафт из 9 осколков\n\n"
    
    text += "Осколки нельзя купить за реальные деньги — только в игре!"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Проверяем, есть ли у пользователя премиум
    if hasattr(character, 'premium_tier') and character.premium_tier:
        markup.add(
            InlineKeyboardButton("💎 Купить 1", callback_data="rainbow:buy:1"),
            InlineKeyboardButton("💎💎 Купить 3", callback_data="rainbow:buy:3"),
            InlineKeyboardButton("💎💎💎 Купить 5", callback_data="rainbow:buy:5")
        )
    else:
        markup.add(InlineKeyboardButton("💎 Узнать о премиум", callback_data="premium:menu"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_history(call, bot_instance, character):
    """Показать историю операций с радужными ресурсами"""
    history = character.rainbow_history if hasattr(character, 'rainbow_history') else []
    
    text = "📊 *ИСТОРИЯ ОПЕРАЦИЙ*\n\n"
    
    if not history:
        text += "Пока нет операций с радужными ресурсами."
    else:
        for entry in history[-10:]:  # Последние 10 записей
            date = entry.get('date', '')
            action = entry.get('action', '')
            amount = entry.get('amount', 0)
            resource = entry.get('resource', '')
            text += f"• {date}: {action} {amount} {resource}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_info(call, bot_instance):
    """Показать подробную информацию о системе"""
    text = "ℹ️ *ПОДРОБНЕЕ О РАДУЖНЫХ КАМНЯХ*\n\n"
    
    text += "🌟 *Что такое радужные камни?*\n"
    text += "Радужные камни — легендарные артефакты, создаваемые из 9 осколков. "
    text += "Используются для крафта уникальных предметов и улучшений.\n\n"
    
    text += "🌈 *Радужные осколки:*\n"
    text += "• Выдаются на 3-й и 6-й день ежедневного захода\n"
    text += "• 10% шанс выпадения с боссов\n"
    text += "• Можно получить в ивентах\n"
    text += "• НЕ продаются за реальные деньги\n\n"
    
    text += "💎 *Радужные камни:*\n"
    text += "• Крафт: 9 осколков = 1 камень (24 часа)\n"
    text += "• Покупка: 500 ⭐ или 9 TON\n"
    text += "• Награда за годовую подписку\n"
    text += "• Награда за легендарные достижения\n\n"
    
    text += "🔮 *Что можно сделать с камнями:*\n"
    text += "• Легендарное оружие и броня\n"
    text += "• Уникальные улучшения дома\n"
    text += "• Особые титулы с бонусами\n"
    text += "• Превращение в легендарные предметы"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def start_crafting(call, bot_instance, character):
    """Начать крафт радужного камня"""
    from main import save_character
    
    rainbow_shards = character.rainbow_shards if hasattr(character, 'rainbow_shards') else 0
    
    if rainbow_shards < RAINBOW_INFO['shards_per_stone']:
        bot_instance.answer_callback_query(call.id, f"❌ Нужно {RAINBOW_INFO['shards_per_stone']} осколков!")
        return
    
    if character.house_level < RAINBOW_INFO['min_house_level']:
        bot_instance.answer_callback_query(call.id, f"❌ Нужен {RAINBOW_INFO['min_house_level']} уровень дома и алтарь радуги!")
        return
    
    # Проверяем, не крафтит ли уже
    now = int(time.time())
    if hasattr(character, 'rainbow_craft_end') and character.rainbow_craft_end > now:
        remaining = character.rainbow_craft_end - now
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        bot_instance.answer_callback_query(call.id, f"⏳ Уже крафтится! Осталось {hours}ч {minutes}м")
        return
    
    # Запускаем крафт
    craft_end = now + RAINBOW_INFO['craft_time']
    character.rainbow_craft_end = craft_end
    character.rainbow_shards = rainbow_shards - RAINBOW_INFO['shards_per_stone']
    
    # Добавляем в историю
    if not hasattr(character, 'rainbow_history'):
        character.rainbow_history = []
    character.rainbow_history.append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'action': 'start_craft',
        'amount': RAINBOW_INFO['shards_per_stone'],
        'resource': '🌈'
    })
    
    save_character(character)
    
    # Создаём напоминание (в реальной игре нужно через background tasks)
    text = "🔮 *КРАФТ РАДУЖНОГО КАМНЯ*\n\n"
    text += f"Крафт запущен! Камень будет готов через {RAINBOW_INFO['craft_time'] // 3600} часов.\n"
    text += "Ты получишь уведомление, когда процесс завершится."
    
    bot_instance.answer_callback_query(call.id, "✅ Крафт запущен!")
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='Markdown'
    )

def check_craft_completion(character):
    """Проверить завершение крафта (вызывать периодически)"""
    from main import save_character
    
    now = int(time.time())
    if hasattr(character, 'rainbow_craft_end') and character.rainbow_craft_end <= now and character.rainbow_craft_end > 0:
        # Крафт завершён
        character.rainbow_stones = (character.rainbow_stones or 0) + 1
        character.rainbow_craft_end = 0
        
        # Добавляем в историю
        if not hasattr(character, 'rainbow_history'):
            character.rainbow_history = []
        character.rainbow_history.append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'action': 'complete_craft',
            'amount': 1,
            'resource': '💎'
        })
        
        save_character(character)
        return True
    return False

def craft_recipe(call, bot_instance, character, recipe_id, rainbow_data):
    """Скрафтить предмет из радужного камня"""
    from main import save_character
    
    recipes = rainbow_data.get("rainbow", {}).get("recipes", {})
    recipe = recipes.get(recipe_id)
    
    if not recipe:
        bot_instance.answer_callback_query(call.id, "❌ Рецепт не найден")
        return
    
    cost = recipe.get('cost', 1)
    rainbow_stones = character.rainbow_stones if hasattr(character, 'rainbow_stones') else 0
    
    if rainbow_stones < cost:
        bot_instance.answer_callback_query(call.id, f"❌ Нужно {cost} радужных камней!")
        return
    
    # Тратим камни
    character.rainbow_stones = rainbow_stones - cost
    character.rainbow_stones_used = (character.rainbow_stones_used or 0) + cost
    
    # Добавляем предметы
    items = recipe.get('items', [])
    for item in items:
        if isinstance(item, list) and len(item) == 2:
            item_id, count = item
            for _ in range(count):
                character.add_item(item_id)
        else:
            character.add_item(item)
    
    # Добавляем титул если есть
    if recipe.get('title'):
        if not character.titles:
            character.titles = []
        character.titles.append(recipe['title'])
    
    # Добавляем в историю
    if not hasattr(character, 'rainbow_history'):
        character.rainbow_history = []
    character.rainbow_history.append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'action': f'craft_{recipe_id}',
        'amount': cost,
        'resource': '💎'
    })
    
    save_character(character)
    
    bot_instance.answer_callback_query(call.id, f"✅ {recipe.get('name')} создан!")
    show_recipes(call, bot_instance, character, rainbow_data)

def buy_stones(call, bot_instance, character, amount):
    """Купить радужные камни за премиум-валюту"""
    from main import save_character, premium_data
    
    # Здесь должна быть интеграция с платежной системой
    # Пока просто показываем заглушку
    
    text = "💎 *ПОКУПКА РАДУЖНЫХ КАМНЕЙ*\n\n"
    text += f"Ты хочешь купить {amount} радужных камней.\n\n"
    text += "💰 *Цена:*\n"
    
    prices = {
        1: "500 ⭐ или 9 TON",
        3: "1400 ⭐ (скидка 7%)",
        5: "2200 ⭐ (скидка 12%)"
    }
    
    text += prices.get(amount, "—") + "\n\n"
    text += "Для оплаты используй команду /pay или обратись в поддержку."
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:shop"))
    
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

def add_rainbow_shard(character, source="other", amount=1):
    """Добавить радужный осколок (вызывается из других хендлеров)"""
    from main import save_character
    
    if not hasattr(character, 'rainbow_shards'):
        character.rainbow_shards = 0
    if not hasattr(character, 'rainbow_shards_collected'):
        character.rainbow_shards_collected = 0
    if not hasattr(character, 'rainbow_history'):
        character.rainbow_history = []
    
    character.rainbow_shards += amount
    character.rainbow_shards_collected += amount
    
    character.rainbow_history.append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'action': f'add_{source}',
        'amount': amount,
        'resource': '🌈'
    })
    
    save_character(character)
    
    # Проверяем достижения
    check_rainbow_achievements(character)
    
    return True

def check_rainbow_achievements(character):
    """Проверить достижения за радужные камни"""
    from main import save_character
    
    collected = character.rainbow_shards_collected or 0
    used = character.rainbow_stones_used or 0
    
    achievements_earned = []
    
    # Достижение за 100 осколков
    if collected >= 100 and not hasattr(character, 'achievement_rainbow_100'):
        character.achievement_rainbow_100 = True
        if not character.event_achievements:
            character.event_achievements = []
        character.event_achievements.append("rainbow_master")
        if not character.titles:
            character.titles = []
        character.titles.append("Повелитель радуги")
        achievements_earned.append("Повелитель радуги")
    
    # Достижение за 10 камней
    if used >= 10 and not hasattr(character, 'achievement_rainbow_10'):
        character.achievement_rainbow_10 = True
        if not character.event_achievements:
            character.event_achievements = []
        character.event_achievements.append("rainbow_collector")
        if not character.titles:
            character.titles = []
        character.titles.append("Хранитель радуги")
        achievements_earned.append("Хранитель радуги")
    
    if achievements_earned:
        save_character(character)
    
    return achievements_earned

# ============================================
# ФУНКЦИИ ДЛЯ СОВМЕСТИМОСТИ С __init__.py
# ============================================

def rainbow_status_command(message, bot_instance, get_or_create_player_func, rainbow_data):
    """Команда /rainbow_status - показать статус радужной системы"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    rainbow_shards = character.rainbow_shards if hasattr(character, 'rainbow_shards') else 0
    rainbow_stones = character.rainbow_stones if hasattr(character, 'rainbow_stones') else 0
    
    craft_end = character.rainbow_craft_end if hasattr(character, 'rainbow_craft_end') else 0
    now = int(time.time())
    crafting = craft_end > now
    
    text = "🌈 *СТАТУС РАДУЖНОЙ СИСТЕМЫ*\n\n"
    text += f"📊 *Твои ресурсы:*\n"
    text += f"• 🌈 Осколки: {rainbow_shards}\n"
    text += f"• 💎 Радужные камни: {rainbow_stones}\n\n"
    
    if crafting:
        remaining = craft_end - now
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        text += f"⏳ *Крафт в процессе:* осталось {hours}ч {minutes}м\n\n"
    
    text += "📅 *Получено осколков:*\n"
    text += f"• Собрано всего: {character.rainbow_shards_collected or 0}\n"
    text += f"• Использовано камней: {character.rainbow_stones_used or 0}\n"
    
    # Достижения
    achievements = []
    if hasattr(character, 'achievement_rainbow_100'):
        achievements.append("Повелитель радуги")
    if hasattr(character, 'achievement_rainbow_10'):
        achievements.append("Хранитель радуги")
    
    if achievements:
        text += f"\n🏆 *Достижения:*\n"
        for ach in achievements:
            text += f"• {ach}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def activate_rainbow_command(message, bot_instance, get_or_create_player_func, rainbow_data):
    """Команда /activate_rainbow - начать крафт радужного камня"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    rainbow_shards = character.rainbow_shards if hasattr(character, 'rainbow_shards') else 0
    
    if rainbow_shards < RAINBOW_INFO['shards_per_stone']:
        bot_instance.send_message(
            message.chat.id,
            f"❌ Нужно {RAINBOW_INFO['shards_per_stone']} радужных осколков!\n"
            f"У тебя: {rainbow_shards}",
            parse_mode='Markdown'
        )
        return
    
    if character.house_level < RAINBOW_INFO['min_house_level']:
        bot_instance.send_message(
            message.chat.id,
            f"❌ Нужен {RAINBOW_INFO['min_house_level']} уровень дома!",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, не крафтит ли уже
    now = int(time.time())
    if hasattr(character, 'rainbow_craft_end') and character.rainbow_craft_end > now:
        remaining = character.rainbow_craft_end - now
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        bot_instance.send_message(
            message.chat.id,
            f"⏳ Крафт уже запущен! Осталось {hours}ч {minutes}м",
            parse_mode='Markdown'
        )
        return
    
    # Запускаем крафт
    craft_end = now + RAINBOW_INFO['craft_time']
    character.rainbow_craft_end = craft_end
    character.rainbow_shards = rainbow_shards - RAINBOW_INFO['shards_per_stone']
    
    # Добавляем в историю
    if not hasattr(character, 'rainbow_history'):
        character.rainbow_history = []
    character.rainbow_history.append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'action': 'start_craft',
        'amount': RAINBOW_INFO['shards_per_stone'],
        'resource': '🌈'
    })
    
    from main import save_character
    save_character(character)
    
    bot_instance.send_message(
        message.chat.id,
        f"🔮 *КРАФТ ЗАПУЩЕН!*\n\n"
        f"Радужный камень будет готов через {RAINBOW_INFO['craft_time'] // 3600} часов.\n"
        f"Использовано: {RAINBOW_INFO['shards_per_stone']} 🌈\n"
        f"Осталось осколков: {character.rainbow_shards}",
        parse_mode='Markdown'
    )

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func, rainbow_data):
    """Обработка кнопок радужной системы"""
    from main import save_character
    
    parts = call.data.split(':')
    action = parts[1] if len(parts) > 1 else "menu"
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверяем завершение крафта
    check_craft_completion(character)
    
    if action == "menu":
        rainbow_command(call.message, bot_instance, get_or_create_player_func, rainbow_data)
    
    elif action == "craft_start":
        start_crafting(call, bot_instance, character)
    
    elif action == "recipes":
        show_recipes(call, bot_instance, character, rainbow_data)
    
    elif action == "achievements":
        show_achievements(call, bot_instance, character, rainbow_data)
    
    elif action == "shop":
        show_shop(call, bot_instance, character, rainbow_data)
    
    elif action == "history":
        show_history(call, bot_instance, character)
    
    elif action == "info":
        show_info(call, bot_instance)
    
    elif action.startswith("craft_recipe:"):
        recipe_id = action.split(':')[2]
        craft_recipe(call, bot_instance, character, recipe_id, rainbow_data)
    
    elif action.startswith("buy:"):
        amount = int(action.split(':')[2])
        buy_stones(call, bot_instance, character, amount)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'rainbow_command',
    'rainbow_status_command',
    'activate_rainbow_command',
    'handle_callback',
    'add_rainbow_shard',
    'check_rainbow_achievements'
]
