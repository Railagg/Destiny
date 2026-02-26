import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ ОБМЕНА
# ============================================

# Базовый курс
BASE_TON_TO_DSTN = 2500

# Недельные лимиты DSTN по уровням игрока
WEEKLY_LIMITS = [
    {"level_min": 1, "level_max": 5, "limit": 50, "name": "🌱 Новичок"},
    {"level_min": 6, "level_max": 10, "limit": 100, "name": "🌿 Подмастерье"},
    {"level_min": 11, "level_max": 15, "limit": 250, "name": "⚔️ Воин"},
    {"level_min": 16, "level_max": 20, "limit": 500, "name": "🛡️ Ветеран"},
    {"level_min": 21, "level_max": 25, "limit": 1000, "name": "🔰 Элитный воин"},
    {"level_min": 26, "level_max": 30, "limit": 2500, "name": "⚡ Мастер"},
    {"level_min": 31, "level_max": 35, "limit": 5000, "name": "✨ Герой"},
    {"level_min": 36, "level_max": 40, "limit": 7500, "name": "👑 Легенда"},
    {"level_min": 41, "level_max": 45, "limit": 10000, "name": "🌟 Полубог"},
    {"level_min": 46, "level_max": 50, "limit": 15000, "name": "💫 Бог"},
    {"level_min": 51, "level_max": 55, "limit": 25000, "name": "🌌 Титан"},
    {"level_min": 56, "level_max": 60, "limit": 50000, "name": "∞ Бессмертный"}
]

# Бонусы премиум-подписки
PREMIUM_BONUSES = {
    "7days": {
        "name": "🟢 Стартовый",
        "ton_to_dstn": 2550,
        "fee_discount": 50,
        "limit_multiplier": 1.5,
        "priority": False
    },
    "28days": {
        "name": "🔵 Базовый",
        "ton_to_dstn": 2600,
        "fee_discount": 75,
        "limit_multiplier": 2.0,
        "priority": False
    },
    "90days": {
        "name": "🟣 Продвинутый",
        "ton_to_dstn": 2650,
        "fee_discount": 90,
        "limit_multiplier": 2.5,
        "priority": False
    },
    "180days": {
        "name": "🟡 Элитный",
        "ton_to_dstn": 2700,
        "fee_discount": 100,
        "fee_free": True,
        "limit_multiplier": 3.0,
        "priority": True
    },
    "365days": {
        "name": "🔴 Легендарный",
        "ton_to_dstn": 2800,
        "fee_discount": 100,
        "fee_free": True,
        "limit_multiplier": 5.0,
        "priority": True,
        "express": True
    }
}

# ============================================
# ФУНКЦИИ ДЛЯ РАСЧЁТА
# ============================================

def get_weekly_limit(character):
    """Получить недельный лимит DSTN по уровню игрока"""
    player_level = character.level
    
    for limit_info in WEEKLY_LIMITS:
        if limit_info["level_min"] <= player_level <= limit_info["level_max"]:
            base_limit = limit_info["limit"]
            
            # Бонус за премиум
            limit_multiplier = 1.0
            if hasattr(character, 'premium_plan') and character.premium_plan:
                premium_info = PREMIUM_BONUSES.get(character.premium_plan, {})
                limit_multiplier = premium_info.get("limit_multiplier", 1.0)
            
            return {
                "limit": int(base_limit * limit_multiplier),
                "name": limit_info["name"],
                "level_range": f"{limit_info['level_min']}-{limit_info['level_max']}",
                "base_limit": base_limit,
                "multiplier": limit_multiplier
            }
    
    # Для уровней выше 60
    return {
        "limit": 100000,
        "name": "∞ Абсолют",
        "level_range": "60+",
        "base_limit": 100000,
        "multiplier": 1.0
    }

def get_exchange_rate(character, direction="ton_to_dstn"):
    """Получить актуальный курс обмена с учётом бонусов"""
    base_rate = BASE_TON_TO_DSTN
    
    # Базовая комиссия (только для DSTN → TON)
    fee_percent = 5
    fee_free = False
    
    # Бонусы за премиум
    premium_bonus = 0
    fee_discount = 0
    
    if hasattr(character, 'premium_plan') and character.premium_plan:
        premium_info = PREMIUM_BONUSES.get(character.premium_plan, {})
        
        # Улучшенный курс для TON → DSTN
        if direction == "ton_to_dstn":
            premium_bonus = premium_info.get("ton_to_dstn", base_rate) - base_rate
        
        # Скидка на комиссию
        fee_discount = premium_info.get("fee_discount", 0)
        
        # Бесплатная комиссия
        if premium_info.get("fee_free", False):
            fee_free = True
    
    # Итоговый курс
    final_rate = base_rate + premium_bonus
    
    # Итоговая комиссия
    final_fee = 0 if fee_free else max(0, fee_percent - (fee_percent * fee_discount / 100))
    
    return {
        "rate": final_rate,
        "fee_percent": final_fee,
        "premium_bonus": premium_bonus,
        "fee_discount": fee_discount,
        "fee_free": fee_free,
        "base_rate": base_rate
    }

def get_used_this_week(character):
    """Получить использованный лимит за неделю"""
    if not hasattr(character, 'exchange_used_week'):
        return 0
    
    # Проверяем, не прошла ли неделя
    last_reset = getattr(character, 'exchange_last_reset', 0)
    now = datetime.utcnow()
    
    if last_reset and (now - last_reset).days >= 7:
        return 0
    
    return character.exchange_used_week

def update_used_limit(character, amount):
    """Обновить использованный лимит"""
    from main import save_character
    
    now = datetime.utcnow()
    
    # Сбрасываем если прошла неделя
    if hasattr(character, 'exchange_last_reset'):
        last = character.exchange_last_reset
        if last and (now - last).days >= 7:
            character.exchange_used_week = 0
    
    character.exchange_used_week = get_used_this_week(character) + amount
    character.exchange_last_reset = now
    save_character(character)

# ============================================
# ОСНОВНАЯ КОМАНДА
# ============================================

def exchange_command(message, bot_instance, get_or_create_player_func, exchange_data):
    """Команда /exchange - обмен TON на DSTN и обратно"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Получаем данные обмена
    exchange_settings = exchange_data.get("exchange", {})
    limits = exchange_settings.get("limits", {}).get("daily", {})
    
    # Получаем курс и лимиты
    rate_info = get_exchange_rate(character)
    limit_info = get_weekly_limit(character)
    used_this_week = get_used_this_week(character)
    remaining = limit_info["limit"] - used_this_week
    
    text = "💱 *DESTINY EXCHANGE*\n\n"
    text += f"💰 *Курс:* 1 TON = {rate_info['rate']} DSTN\n"
    
    if rate_info['premium_bonus'] > 0:
        text += f"  ✨ Премиум бонус: +{rate_info['premium_bonus']} DSTN\n"
    
    text += f"💎 *Комиссия:* {rate_info['fee_percent']}% (только DSTN → TON)\n"
    
    if rate_info['fee_free']:
        text += "  ✅ Бесплатный обмен для премиум\n"
    elif rate_info['fee_discount'] > 0:
        text += f"  📉 Скидка {rate_info['fee_discount']}% для премиум\n"
    
    text += f"\n📊 *Твой баланс:* {character.dstn or 0} DSTN\n"
    text += f"📈 *Уровень:* {character.level}\n"
    text += f"🎭 *Статус:* {limit_info['name']}\n"
    text += f"📊 *Недельный лимит:* {limit_info['limit']} DSTN\n"
    text += f"📉 *Использовано:* {used_this_week} DSTN\n"
    text += f"📈 *Осталось:* {remaining} DSTN\n\n"
    
    if limit_info['multiplier'] > 1:
        text += f"✨ Премиум бонус: x{limit_info['multiplier']} к лимиту\n"
    
    text += "📋 *Лимиты по уровням:*\n"
    
    # Показываем ближайшие уровни
    for l in WEEKLY_LIMITS[:5]:
        emoji = "✅" if l["level_min"] <= character.level <= l["level_max"] else "⏳"
        text += f"{emoji} Ур.{l['level_min']}-{l['level_max']}: {l['limit']} DSTN/нед\n"
    
    text += "\n🔗 Подключи TON кошелёк для обмена"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Кнопки обмена
    markup.add(
        InlineKeyboardButton("💎 Купить DSTN за TON", callback_data="exchange:buy"),
        InlineKeyboardButton("💰 Продать DSTN за TON", callback_data="exchange:sell")
    )
    
    # Информационные кнопки
    markup.add(
        InlineKeyboardButton("📊 Все лимиты", callback_data="exchange:all_limits"),
        InlineKeyboardButton("📋 Мои операции", callback_data="exchange:history")
    )
    
    # Премиум и настройки
    if hasattr(character, 'premium_plan') and character.premium_plan:
        premium_name = PREMIUM_BONUSES.get(character.premium_plan, {}).get("name", "Премиум")
        markup.add(InlineKeyboardButton(f"✨ {premium_name} активен", callback_data="premium:status"))
    else:
        markup.add(InlineKeyboardButton("👑 Купить премиум", callback_data="premium:menu"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_buy_menu(call, bot_instance, character, exchange_data):
    """Показать меню покупки DSTN за TON"""
    rate_info = get_exchange_rate(character, "ton_to_dstn")
    limit_info = get_weekly_limit(character)
    used = get_used_this_week(character)
    remaining = limit_info["limit"] - used
    
    text = "💎 *Покупка DSTN за TON*\n\n"
    text += f"💰 Курс: 1 TON = {rate_info['rate']} DSTN\n"
    text += f"📊 Доступно: {remaining} DSTN из {limit_info['limit']}\n\n"
    
    # Предустановленные суммы
    amounts = [10, 50, 100, 500, 1000]
    
    text += "Выбери сумму в TON:\n"
    for amount in amounts:
        dstn = amount * rate_info['rate']
        if dstn <= remaining:
            text += f"• {amount} TON = {dstn} DSTN\n"
    
    text += "\n🔜 Функция появится после интеграции с TON Connect"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_sell_menu(call, bot_instance, character, exchange_data):
    """Показать меню продажи DSTN за TON"""
    rate_info = get_exchange_rate(character, "dstn_to_ton")
    
    # С учётом комиссии
    effective_rate = rate_info['rate'] * (1 - rate_info['fee_percent'] / 100)
    
    text = "💰 *Продажа DSTN за TON*\n\n"
    text += f"💰 Курс: {rate_info['rate']} DSTN = 1 TON\n"
    text += f"📉 Комиссия: {rate_info['fee_percent']}%\n"
    text += f"💎 Итоговый курс: {int(effective_rate)} DSTN = 1 TON\n\n"
    
    if rate_info['fee_free']:
        text += "✅ Премиум: комиссия 0%\n"
    
    text += f"📊 Твой баланс: {character.dstn or 0} DSTN\n"
    text += f"📈 Минимальная сумма: 1000 DSTN\n\n"
    
    text += "🔜 Функция появится после интеграции с TON Connect"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_all_limits(call, bot_instance, character):
    """Показать все лимиты по уровням"""
    text = "📊 *НЕДЕЛЬНЫЕ ЛИМИТЫ ПО УРОВНЯМ*\n\n"
    text += "Количество DSTN, которое можно обменять за неделю:\n\n"
    
    current_level = character.level
    
    for limit in WEEKLY_LIMITS:
        # Отметка текущего диапазона
        if limit["level_min"] <= current_level <= limit["level_max"]:
            marker = "👉 "
            status = "ТВОЙ ТЕКУЩИЙ"
        else:
            marker = "  "
            status = ""
        
        text += f"{marker}*Ур.{limit['level_min']}-{limit['level_max']}:* {limit['limit']} DSTN/нед"
        if status:
            text += f" ⬅️ {status}"
        text += "\n"
    
    # Информация о премиум бонусе
    text += "\n✨ *Премиум бонус:*\n"
    text += "• 🟢 Стартовый: x1.5 к лимиту\n"
    text += "• 🔵 Базовый: x2.0 к лимиту\n"
    text += "• 🟣 Продвинутый: x2.5 к лимиту\n"
    text += "• 🟡 Элитный: x3.0 к лимиту\n"
    text += "• 🔴 Легендарный: x5.0 к лимиту\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_history(call, bot_instance, character):
    """Показать историю обменов"""
    history = getattr(character, 'exchange_history', [])
    
    text = "📋 *ИСТОРИЯ ОБМЕНОВ*\n\n"
    
    if not history:
        text += "У тебя пока нет совершённых обменов."
    else:
        for entry in history[-10:]:  # Последние 10
            date = entry.get('date', '')
            type = entry.get('type', '')
            amount = entry.get('amount', 0)
            result = entry.get('result', 0)
            text += f"• {date}: {type} {amount} → {result}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def process_exchange(character, direction, amount, exchange_data):
    """Обработать обмен (внутренняя функция)"""
    from main import save_character
    
    rate_info = get_exchange_rate(character, direction)
    limit_info = get_weekly_limit(character)
    used = get_used_this_week(character)
    
    if direction == "ton_to_dstn":
        # TON → DSTN
        dstn_amount = amount * rate_info['rate']
        
        # Проверка лимита
        if used + dstn_amount > limit_info['limit']:
            return False, "Превышение недельного лимита"
        
        character.dstn = (character.dstn or 0) + dstn_amount
        update_used_limit(character, dstn_amount)
        
        # Запись в историю
        if not hasattr(character, 'exchange_history'):
            character.exchange_history = []
        character.exchange_history.append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'type': 'TON → DSTN',
            'amount': amount,
            'result': dstn_amount
        })
        
        save_character(character)
        return True, dstn_amount
    
    else:
        # DSTN → TON
        if character.dstn < amount:
            return False, "Недостаточно DSTN"
        
        if amount < 1000:
            return False, "Минимальная сумма 1000 DSTN"
        
        ton_amount = amount / rate_info['rate']
        
        # Применяем комиссию
        if not rate_info['fee_free']:
            fee = ton_amount * (rate_info['fee_percent'] / 100)
            ton_amount -= fee
        
        character.dstn -= amount
        update_used_limit(character, amount)
        
        # Запись в историю
        if not hasattr(character, 'exchange_history'):
            character.exchange_history = []
        character.exchange_history.append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'type': 'DSTN → TON',
            'amount': amount,
            'result': round(ton_amount, 2)
        })
        
        save_character(character)
        return True, round(ton_amount, 2)

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func, exchange_data):
    """Обработка кнопок обмена"""
    parts = call.data.split(':')
    action = parts[1] if len(parts) > 1 else "menu"
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if action == "menu":
        exchange_command(call.message, bot_instance, get_or_create_player_func, exchange_data)
    
    elif action == "buy":
        show_buy_menu(call, bot_instance, character, exchange_data)
    
    elif action == "sell":
        show_sell_menu(call, bot_instance, character, exchange_data)
    
    elif action == "all_limits":
        show_all_limits(call, bot_instance, character)
    
    elif action == "history":
        show_history(call, bot_instance, character)
    
    elif action.startswith("exchange:"):
        # Обработка конкретных сумм (будет позже)
        bot_instance.answer_callback_query(call.id, "🔜 Функция в разработке")
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
