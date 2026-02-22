import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def exchange_command(message):
    """Команда /exchange - обмен TON на DSTN"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Загружаем данные обмена
    try:
        with open('data/exchange.json', 'r', encoding='utf-8') as f:
            exchange_data = json.load(f)
        rates = exchange_data.get("exchange", {}).get("rates", {})
        ton_rate = rates.get("ton_to_dstn", {}).get("base_rate", 2500)
        limits = exchange_data.get("exchange", {}).get("limits", {}).get("daily", {})
    except:
        ton_rate = 2500
        limits = {"ton": 100, "dstn": 250000}
    
    text = "💱 *DESTINY EXCHANGE*\n\n"
    text += f"💰 Курс: 1 TON = {ton_rate} DSTN\n"
    text += f"💎 Комиссия при обмене DSTN → TON: 5%\n\n"
    text += "Выбери действие:\n"
    text += "➡️ TON → DSTN (без комиссии)\n"
    text += "⬅️ DSTN → TON (комиссия 5%)\n\n"
    text += f"📊 Твой баланс DSTN: {character.destiny_tokens}\n"
    text += f"📋 Дневной лимит: {limits.get('ton', 100)} TON / {limits.get('dstn', 250000)} DSTN\n"
    text += "🔗 Подключи TON кошелёк для обмена"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💎 Купить DSTN за TON", callback_data="exchange:ton_to_dstn"),
        InlineKeyboardButton("💰 Продать DSTN за TON", callback_data="exchange:dstn_to_ton")
    )
    markup.add(
        InlineKeyboardButton("📊 История", callback_data="exchange:history"),
        InlineKeyboardButton("📋 Лимиты", callback_data="exchange:limits")
    )
    markup.add(InlineKeyboardButton("🔗 Подключить кошелёк", callback_data="exchange:connect"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func, exchange_data):
    """Обработка кнопок обмена"""
    data = call.data.split(':')[1]
    
    if data == "ton_to_dstn":
        bot_instance.answer_callback_query(call.id, "🔜 Скоро будет доступно")
        bot_instance.edit_message_text(
            "🔜 *Покупка DSTN за TON*\n\n"
            "Функция появится после интеграции с TON Connect.\n\n"
            "Пока ты можешь:\n"
            "✅ Копить DSTN в игре\n"
            "✅ Покупать DSTN за Telegram Stars\n"
            "✅ Участвовать в ивентах",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
    
    elif data == "dstn_to_ton":
        bot_instance.answer_callback_query(call.id, "🔜 Скоро будет доступно")
        bot_instance.edit_message_text(
            "🔜 *Продажа DSTN за TON*\n\n"
            "Функция появится после интеграции с TON Connect.\n\n"
            f"Минимальная сумма: 1000 DSTN\n"
            f"Комиссия: 5%",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
    
    elif data == "history":
        bot_instance.answer_callback_query(call.id, "📊 История обменов пока пуста")
        bot_instance.edit_message_text(
            "📊 *История обменов*\n\n"
            "У тебя пока нет совершённых обменов.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
    
    elif data == "limits":
        limits = exchange_data.get("exchange", {}).get("limits", {})
        daily = limits.get("daily", {})
        weekly = limits.get("weekly", {})
        monthly = limits.get("monthly", {})
        
        text = "📋 *Лимиты обмена*\n\n"
        text += f"📅 *Дневной лимит:*\n"
        text += f"├ {daily.get('ton', 100)} TON\n"
        text += f"└ {daily.get('dstn', 250000)} DSTN\n\n"
        text += f"📆 *Недельный лимит:*\n"
        text += f"├ {weekly.get('ton', 500)} TON\n"
        text += f"└ {weekly.get('dstn', 1250000)} DSTN\n\n"
        text += f"📅 *Месячный лимит:*\n"
        text += f"├ {monthly.get('ton', 2000)} TON\n"
        text += f"└ {monthly.get('dstn', 5000000)} DSTN"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="exchange:menu"))
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "connect":
        bot_instance.answer_callback_query(call.id, "🔗 Подключение кошелька")
        bot_instance.edit_message_text(
            "🔗 *Подключение TON кошелька*\n\n"
            "1. Установи Tonkeeper или любой другой TON кошелёк\n"
            "2. Нажми кнопку ниже\n"
            "3. Подтверди подключение в кошельке\n\n"
            "⚡ Функция в разработке",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        exchange_command(call.message)
