# /bot/handlers/exchange.py
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ ОБМЕННИКА
# ============================================

EXCHANGE_RATES = {
    "gold_to_dstn": 0.01,  # 100 золота = 1 DSTN
    "dstn_to_gold": 100,    # 1 DSTN = 100 золота
    "stars_to_dstn": 50,     # 1 звезда = 50 DSTN
    "dstn_to_stars": 0.02,   # 50 DSTN = 1 звезда
    "ton_to_dstn": 2500,     # 1 TON = 2500 DSTN
    "dstn_to_ton": 0.0004,   # 2500 DSTN = 1 TON
}

PREMIUM_BONUSES = {
    "7days": {"ton_to_dstn": 2550, "fee_discount": 50},
    "28days": {"ton_to_dstn": 2600, "fee_discount": 75},
    "90days": {"ton_to_dstn": 2650, "fee_discount": 90},
    "180days": {"ton_to_dstn": 2700, "fee_free": True},
    "365days": {"ton_to_dstn": 2800, "fee_free": True, "priority": True}
}

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

def exchange_command(message, bot_instance, get_or_create_player_func, exchange_data):
    """Команда /exchange - обмен валют"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "💱 *Обменный пункт*\n\n"
    text += f"💰 Твой баланс:\n"
    text += f"• Золото: {character.gold} 🪙\n"
    text += f"• DSTN: {character.destiny_tokens or 0} 💫\n"
    text += f"• Stars: {character.stars or 0} ⭐\n"
    text += f"• TON: {character.ton or 0} 💎\n\n"
    
    text += "*Курсы обмена:*\n"
    text += "• 100 🪙 = 1 💫\n"
    text += "• 1 💫 = 100 🪙\n"
    text += "• 1 ⭐ = 50 💫\n"
    text += "• 50 💫 = 1 ⭐\n"
    text += "• 1 💎 = 2500 💫\n"
    text += "• 2500 💫 = 1 💎\n\n"
    
    # Премиум бонусы
    if user.premium_until and user.premium_until > datetime.utcnow():
        plan = user.premium_plan
        bonus = PREMIUM_BONUSES.get(plan, {})
        if bonus:
            text += "✨ *Твои премиум-бонусы:*\n"
            if bonus.get("ton_to_dstn"):
                text += f"• 1 💎 = {bonus['ton_to_dstn']} 💫 (+{bonus['ton_to_dstn'] - 2500})\n"
            if bonus.get("fee_discount"):
                text += f"• Скидка на комиссию: {bonus['fee_discount']}%\n"
            if bonus.get("fee_free"):
                text += "• Без комиссии за обмен\n"
            if bonus.get("priority"):
                text += "• Приоритетные операции\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🪙 → 💫", callback_data="exchange:gold_to_dstn"),
        InlineKeyboardButton("💫 → 🪙", callback_data="exchange:dstn_to_gold"),
        InlineKeyboardButton("⭐ → 💫", callback_data="exchange:stars_to_dstn"),
        InlineKeyboardButton("💫 → ⭐", callback_data="exchange:dstn_to_stars"),
        InlineKeyboardButton("💎 → 💫", callback_data="exchange:ton_to_dstn"),
        InlineKeyboardButton("💫 → 💎", callback_data="exchange:dstn_to_ton"),
        InlineKeyboardButton("📊 Курсы", callback_data="exchange:rates"),
        InlineKeyboardButton("📜 История", callback_data="exchange:history")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def rates_command(message, bot_instance, get_or_create_player_func, exchange_data):
    """Команда /rates - показать курсы обмена"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "📊 *Текущие курсы обмена*\n\n"
    
    text += "💰 *Золото (🪙) → DSTN (💫)*\n"
    text += "• 100 🪙 = 1 💫\n"
    text += "• 500 🪙 = 5 💫\n"
    text += "• 1000 🪙 = 10 💫\n\n"
    
    text += "💫 *DSTN → Золото*\n"
    text += "• 1 💫 = 100 🪙\n"
    text += "• 5 💫 = 500 🪙\n"
    text += "• 10 💫 = 1000 🪙\n\n"
    
    text += "⭐ *Stars → DSTN*\n"
    text += "• 1 ⭐ = 50 💫\n"
    text += "• 5 ⭐ = 250 💫\n"
    text += "• 10 ⭐ = 500 💫\n\n"
    
    text += "💎 *TON → DSTN*\n"
    
    # Базовый курс
    text += f"• 1 💎 = {EXCHANGE_RATES['ton_to_dstn']} 💫 (базовый)\n"
    
    # Премиум курсы
    if user.premium_until and user.premium_until > datetime.utcnow():
        plan = user.premium_plan
        bonus = PREMIUM_BONUSES.get(plan, {})
        if bonus.get("ton_to_dstn"):
            text += f"• 1 💎 = {bonus['ton_to_dstn']} 💫 (твой премиум-курс)\n"
    
    text += "\n💎 *Преимущества премиума:*\n"
    text += "• 🔵 Базовый: +100 DSTN за TON\n"
    text += "• 🟣 Продвинутый: +150 DSTN за TON\n"
    text += "• 🟡 Элитный: +200 DSTN за TON, без комиссии\n"
    text += "• 🔴 Легендарный: +300 DSTN за TON, приоритет"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 В обменник", callback_data="exchange:menu"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def convert_command(message, bot_instance, get_or_create_player_func, exchange_data):
    """Команда /convert - конвертировать валюту"""
    args = message.text.split()
    if len(args) < 4:
        bot.send_message(
            message.chat.id,
            "❌ Укажи: /convert [из] [в] [количество]\n"
            "Пример: /convert gold dstn 500\n\n"
            "Доступные валюты:\n"
            "• gold - золото 🪙\n"
            "• dstn - DSTN 💫\n"
            "• stars - звёзды ⭐\n"
            "• ton - TON 💎",
            parse_mode='Markdown'
        )
        return
    
    from_currency = args[1].lower()
    to_currency = args[2].lower()
    
    try:
        amount = float(args[3])
    except ValueError:
        bot.send_message(message.chat.id, "❌ Количество должно быть числом!")
        return
    
    if amount <= 0:
        bot.send_message(message.chat.id, "❌ Количество должно быть положительным!")
        return
    
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверяем наличие средств
    if from_currency == "gold" and character.gold < amount:
        bot.send_message(message.chat.id, f"❌ У тебя только {character.gold} золота!")
        return
    elif from_currency == "dstn" and (character.destiny_tokens or 0) < amount:
        bot.send_message(message.chat.id, f"❌ У тебя только {character.destiny_tokens or 0} DSTN!")
        return
    elif from_currency == "stars" and (character.stars or 0) < amount:
        bot.send_message(message.chat.id, f"❌ У тебя только {character.stars or 0} звёзд!")
        return
    elif from_currency == "ton" and (character.ton or 0) < amount:
        bot.send_message(message.chat.id, f"❌ У тебя только {character.ton or 0} TON!")
        return
    
    # Определяем курс
    rate = 0
    pair = f"{from_currency}_to_{to_currency}"
    
    if pair == "gold_to_dstn":
        rate = EXCHANGE_RATES["gold_to_dstn"]  # 0.01
        received = amount * rate
        character.gold -= amount
        character.destiny_tokens = (character.destiny_tokens or 0) + received
        result_text = f"✅ Обменяно {amount} 🪙 на {received} 💫"
    
    elif pair == "dstn_to_gold":
        rate = EXCHANGE_RATES["dstn_to_gold"]  # 100
        received = amount * rate
        character.destiny_tokens = (character.destiny_tokens or 0) - amount
        character.gold += received
        result_text = f"✅ Обменяно {amount} 💫 на {received} 🪙"
    
    elif pair == "stars_to_dstn":
        rate = EXCHANGE_RATES["stars_to_dstn"]  # 50
        received = amount * rate
        character.stars = (character.stars or 0) - amount
        character.destiny_tokens = (character.destiny_tokens or 0) + received
        result_text = f"✅ Обменяно {amount} ⭐ на {received} 💫"
    
    elif pair == "dstn_to_stars":
        rate = EXCHANGE_RATES["dstn_to_stars"]  # 0.02
        received = amount * rate
        character.destiny_tokens = (character.destiny_tokens or 0) - amount
        character.stars = (character.stars or 0) + received
        result_text = f"✅ Обменяно {amount} 💫 на {received} ⭐"
    
    elif pair == "ton_to_dstn":
        rate = EXCHANGE_RATES["ton_to_dstn"]  # 2500
        
        # Премиум бонус
        if user.premium_until and user.premium_until > datetime.utcnow():
            plan = user.premium_plan
            bonus = PREMIUM_BONUSES.get(plan, {})
            if bonus.get("ton_to_dstn"):
                rate = bonus["ton_to_dstn"]
        
        received = amount * rate
        character.ton = (character.ton or 0) - amount
        character.destiny_tokens = (character.destiny_tokens or 0) + received
        result_text = f"✅ Обменяно {amount} 💎 на {received} 💫"
    
    elif pair == "dstn_to_ton":
        rate = EXCHANGE_RATES["dstn_to_ton"]  # 0.0004
        received = amount * rate
        if received < 0.01:
            bot.send_message(message.chat.id, "❌ Минимальная сумма обмена: 2500 DSTN = 1 TON")
            return
        character.destiny_tokens = (character.destiny_tokens or 0) - amount
        character.ton = (character.ton or 0) + received
        result_text = f"✅ Обменяно {amount} 💫 на {received:.2f} 💎"
    
    else:
        bot.send_message(message.chat.id, "❌ Неподдерживаемая пара валют!")
        return
    
    # Сохраняем изменения
    from main import save_character
    save_character(character)
    
    # Записываем историю
    if not hasattr(character, 'exchange_history'):
        character.exchange_history = []
    
    character.exchange_history.append({
        'timestamp': datetime.utcnow().isoformat(),
        'from': from_currency,
        'to': to_currency,
        'amount': amount,
        'received': received,
        'rate': rate
    })
    save_character(character)
    
    # Показываем результат
    text = f"{result_text}\n\n"
    text += f"💰 Новый баланс:\n"
    text += f"• Золото: {character.gold} 🪙\n"
    text += f"• DSTN: {character.destiny_tokens or 0} 💫\n"
    text += f"• Stars: {character.stars or 0} ⭐\n"
    text += f"• TON: {character.ton or 0} 💎"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

def show_history(message, bot_instance, character):
    """Показать историю обменов"""
    history = character.exchange_history if hasattr(character, 'exchange_history') else []
    
    if not history:
        bot.send_message(
            message.chat.id,
            "📜 История обменов пуста",
            parse_mode='Markdown'
        )
        return
    
    text = "📜 *История обменов*\n\n"
    
    for entry in history[-10:]:  # Показываем последние 10
        timestamp = entry.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%d.%m %H:%M")
            except:
                time_str = timestamp
        else:
            time_str = "неизвестно"
        
        from_curr = entry.get('from', '?')
        to_curr = entry.get('to', '?')
        amount = entry.get('amount', 0)
        received = entry.get('received', 0)
        
        emoji_from = {"gold": "🪙", "dstn": "💫", "stars": "⭐", "ton": "💎"}.get(from_curr, "❓")
        emoji_to = {"gold": "🪙", "dstn": "💫", "stars": "⭐", "ton": "💎"}.get(to_curr, "❓")
        
        text += f"{time_str}: {amount}{emoji_from} → {received:.2f}{emoji_to}\n"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func, exchange_data):
    """Обработка кнопок обменника"""
    from main import save_character
    
    parts = call.data.split(':')
    action = parts[1] if len(parts) > 1 else "menu"
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if action == "menu":
        exchange_command(call.message, bot_instance, get_or_create_player_func, exchange_data)
    
    elif action == "rates":
        # Показать детальные курсы
        text = "📊 *Детальные курсы обмена*\n\n"
        
        text += "💰 *Золото ↔ DSTN*\n"
        text += "• 100 🪙 = 1 💫\n"
        text += "• 1 💫 = 100 🪙\n\n"
        
        text += "⭐ *Stars ↔ DSTN*\n"
        text += "• 1 ⭐ = 50 💫\n"
        text += "• 50 💫 = 1 ⭐\n\n"
        
        text += "💎 *TON ↔ DSTN*\n"
        text += f"• 1 💎 = {EXCHANGE_RATES['ton_to_dstn']} 💫\n"
        text += f"• {EXCHANGE_RATES['ton_to_dstn']} 💫 = 1 💎\n\n"
        
        if user.premium_until and user.premium_until > datetime.utcnow():
            plan = user.premium_plan
            bonus = PREMIUM_BONUSES.get(plan, {})
            if bonus.get("ton_to_dstn"):
                text += f"✨ *Твой премиум-курс:*\n"
                text += f"• 1 💎 = {bonus['ton_to_dstn']} 💫\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif action == "history":
        history = character.exchange_history if hasattr(character, 'exchange_history') else []
        
        if not history:
            text = "📜 История обменов пуста"
        else:
            text = "📜 *История обменов*\n\n"
            for entry in history[-10:]:
                timestamp = entry.get('timestamp', '')
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%d.%m %H:%M")
                except:
                    time_str = timestamp[:16] if timestamp else "?"
                
                from_curr = entry.get('from', '?')
                to_curr = entry.get('to', '?')
                amount = entry.get('amount', 0)
                received = entry.get('received', 0)
                
                emoji_from = {"gold": "🪙", "dstn": "💫", "stars": "⭐", "ton": "💎"}.get(from_curr, "❓")
                emoji_to = {"gold": "🪙", "dstn": "💫", "stars": "⭐", "ton": "💎"}.get(to_curr, "❓")
                
                text += f"{time_str}: {amount}{emoji_from} → {received:.2f}{emoji_to}\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif action == "gold_to_dstn":
        # Создаём клавиатуру с суммами
        markup = InlineKeyboardMarkup(row_width=2)
        amounts = [100, 500, 1000, 5000]
        for amount in amounts:
            markup.add(InlineKeyboardButton(
                f"{amount} 🪙 → {amount // 100} 💫",
                callback_data=f"exchange:do:gold_to_dstn:{amount}"
            ))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
        
        bot_instance.edit_message_text(
            "💰 Выбери сумму для обмена:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif action == "dstn_to_gold":
        markup = InlineKeyboardMarkup(row_width=2)
        amounts = [1, 5, 10, 50]
        for amount in amounts:
            markup.add(InlineKeyboardButton(
                f"{amount} 💫 → {amount * 100} 🪙",
                callback_data=f"exchange:do:dstn_to_gold:{amount}"
            ))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
        
        bot_instance.edit_message_text(
            "💫 Выбери сумму для обмена:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif action == "stars_to_dstn":
        markup = InlineKeyboardMarkup(row_width=2)
        amounts = [1, 5, 10, 20]
        for amount in amounts:
            markup.add(InlineKeyboardButton(
                f"{amount} ⭐ → {amount * 50} 💫",
                callback_data=f"exchange:do:stars_to_dstn:{amount}"
            ))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
        
        bot_instance.edit_message_text(
            "⭐ Выбери сумму для обмена:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif action == "dstn_to_stars":
        markup = InlineKeyboardMarkup(row_width=2)
        amounts = [50, 100, 250, 500]
        for amount in amounts:
            markup.add(InlineKeyboardButton(
                f"{amount} 💫 → {amount // 50} ⭐",
                callback_data=f"exchange:do:dstn_to_stars:{amount}"
            ))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
        
        bot_instance.edit_message_text(
            "💫 Выбери сумму для обмена:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif action == "ton_to_dstn":
        # Определяем курс
        rate = EXCHANGE_RATES["ton_to_dstn"]
        if user.premium_until and user.premium_until > datetime.utcnow():
            plan = user.premium_plan
            bonus = PREMIUM_BONUSES.get(plan, {})
            if bonus.get("ton_to_dstn"):
                rate = bonus["ton_to_dstn"]
        
        markup = InlineKeyboardMarkup(row_width=2)
        amounts = [1, 5, 10, 20]
        for amount in amounts:
            markup.add(InlineKeyboardButton(
                f"{amount} 💎 → {amount * rate} 💫",
                callback_data=f"exchange:do:ton_to_dstn:{amount}"
            ))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
        
        bot_instance.edit_message_text(
            f"💎 Выбери сумму для обмена (курс: 1💎 = {rate}💫):",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif action == "dstn_to_ton":
        rate = EXCHANGE_RATES["dstn_to_ton"]  # 0.0004
        min_amount = int(1 / rate)  # 2500
        
        markup = InlineKeyboardMarkup(row_width=2)
        amounts = [min_amount, min_amount * 2, min_amount * 5, min_amount * 10]
        for amount in amounts:
            markup.add(InlineKeyboardButton(
                f"{amount} 💫 → {amount * rate:.2f} 💎",
                callback_data=f"exchange:do:dstn_to_ton:{amount}"
            ))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
        
        bot_instance.edit_message_text(
            f"💫 Выбери сумму для обмена (минимум: {min_amount}💫 = 1💎):",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif action.startswith("do:"):
        # Выполняем обмен
        parts = action.split(':')
        pair = parts[1]
        amount = float(parts[2])
        
        if pair == "gold_to_dstn":
            if character.gold < amount:
                bot_instance.answer_callback_query(call.id, f"❌ Нужно {amount} золота!")
                return
            
            received = amount // 100
            character.gold -= amount
            character.destiny_tokens = (character.destiny_tokens or 0) + received
            
            result_text = f"✅ {amount} 🪙 → {received} 💫"
        
        elif pair == "dstn_to_gold":
            if (character.destiny_tokens or 0) < amount:
                bot_instance.answer_callback_query(call.id, f"❌ Нужно {amount} DSTN!")
                return
            
            received = amount * 100
            character.destiny_tokens = (character.destiny_tokens or 0) - amount
            character.gold += received
            
            result_text = f"✅ {amount} 💫 → {received} 🪙"
        
        elif pair == "stars_to_dstn":
            if (character.stars or 0) < amount:
                bot_instance.answer_callback_query(call.id, f"❌ Нужно {amount} звёзд!")
                return
            
            received = amount * 50
            character.stars = (character.stars or 0) - amount
            character.destiny_tokens = (character.destiny_tokens or 0) + received
            
            result_text = f"✅ {amount} ⭐ → {received} 💫"
        
        elif pair == "dstn_to_stars":
            if (character.destiny_tokens or 0) < amount:
                bot_instance.answer_callback_query(call.id, f"❌ Нужно {amount} DSTN!")
                return
            
            received = amount // 50
            character.destiny_tokens = (character.destiny_tokens or 0) - amount
            character.stars = (character.stars or 0) + received
            
            result_text = f"✅ {amount} 💫 → {received} ⭐"
        
        elif pair == "ton_to_dstn":
            if (character.ton or 0) < amount:
                bot_instance.answer_callback_query(call.id, f"❌ Нужно {amount} TON!")
                return
            
            rate = EXCHANGE_RATES["ton_to_dstn"]
            if user.premium_until and user.premium_until > datetime.utcnow():
                plan = user.premium_plan
                bonus = PREMIUM_BONUSES.get(plan, {})
                if bonus.get("ton_to_dstn"):
                    rate = bonus["ton_to_dstn"]
            
            received = amount * rate
            character.ton = (character.ton or 0) - amount
            character.destiny_tokens = (character.destiny_tokens or 0) + received
            
            result_text = f"✅ {amount} 💎 → {received} 💫"
        
        elif pair == "dstn_to_ton":
            if (character.destiny_tokens or 0) < amount:
                bot_instance.answer_callback_query(call.id, f"❌ Нужно {amount} DSTN!")
                return
            
            rate = EXCHANGE_RATES["dstn_to_ton"]  # 0.0004
            received = amount * rate
            if received < 0.01:
                bot_instance.answer_callback_query(call.id, "❌ Минимальная сумма: 2500 DSTN = 1 TON")
                return
            
            character.destiny_tokens = (character.destiny_tokens or 0) - amount
            character.ton = (character.ton or 0) + received
            
            result_text = f"✅ {amount} 💫 → {received:.2f} 💎"
        
        else:
            bot_instance.answer_callback_query(call.id, "❌ Неподдерживаемая операция")
            return
        
        # Сохраняем
        save_character(character)
        
        # Записываем историю
        if not hasattr(character, 'exchange_history'):
            character.exchange_history = []
        
        character.exchange_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'from': pair.split('_to_')[0],
            'to': pair.split('_to_')[1],
            'amount': amount,
            'received': received,
            'rate': received / amount if amount > 0 else 0
        })
        save_character(character)
        
        bot_instance.answer_callback_query(call.id, result_text)
        
        # Возвращаемся в меню
        exchange_command(call.message, bot_instance, get_or_create_player_func, exchange_data)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ В разработке")

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'exchange_command',
    'rates_command',
    'convert_command',
    'handle_callback'
]
