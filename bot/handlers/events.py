import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
from datetime import datetime

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def events_command(message):
    """Команда /events - ивенты"""
    from main import events_data
    
    weekly = events_data.get("events", {}).get("weekly", {})
    
    # Определяем сегодняшний день
    today = datetime.now().strftime("%A").lower()
    
    text = "🎪 *ЕЖЕНЕДЕЛЬНЫЕ ИВЕНТЫ*\n\n"
    
    for day, event in weekly.items():
        prefix = "👉 *СЕГОДНЯ*: " if day == today else "• "
        text += f"{prefix}{event.get('name')}\n"
        text += f"  {event.get('description')}\n"
        if event.get('bonuses'):
            bonuses = []
            for bonus, value in event.get('bonuses', {}).items():
                if value > 1:
                    bonuses.append(f"{bonus} x{value}")
            if bonuses:
                text += f"  Бонусы: {', '.join(bonuses)}\n"
        text += "\n"
    
    text += "🏆 *Достижения за ивенты* доступны в энциклопедии!"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📅 Календарь", callback_data="events:calendar"),
        InlineKeyboardButton("🏆 Мои награды", callback_data="events:rewards")
    )
    markup.add(
        InlineKeyboardButton("🌙 Ежемесячные", callback_data="events:monthly"),
        InlineKeyboardButton("🍂 Сезонные", callback_data="events:seasonal")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, events_data):
    """Обработка кнопок ивентов"""
    data = call.data.split(':')[1]
    
    if data == "calendar":
        text = "📅 *КАЛЕНДАРЬ ИВЕНТОВ*\n\n"
        text += "🗓️ *Еженедельные:*\n"
        text += "ПН: ⛏️ Шахтёрский день\n"
        text += "ВТ: 🏹 Охотничий день\n"
        text += "СР: 🎣 Рыбный день\n"
        text += "ЧТ: 🌈 День радуги\n"
        text += "ПТ: ⚔️ PvP турнир\n"
        text += "СБ: 🏛️ Гильдейские войны\n"
        text += "ВС: 🙏 Благословение\n\n"
        text += "🌙 *Ежемесячные:*\n"
        text += "• Полнолуние (15 число)\n"
        text += "• Метеоритный дождь\n"
        text += "• Торговая караван\n\n"
        text += "🍂 *Сезонные:*\n"
        text += "• Весенний фестиваль\n"
        text += "• Летнее солнцестояние\n"
        text += "• Праздник урожая\n"
        text += "• Зимний фестиваль\n"
        text += "• Новый год\n"
        text += "• Хэллоуин"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "rewards":
        # Здесь нужно загружать реальные награды игрока
        text = "🏆 *МОИ НАГРАДЫ ЗА ИВЕНТЫ*\n\n"
        text += "Шахтёрский день: 3 победы 🏅\n"
        text += "Охотничий день: 1 победа 🏅\n"
        text += "Рыбный день: 0 побед\n"
        text += "День радуги: 0 побед\n"
        text += "PvP турнир: участие (100 DSTN)\n"
        text += "Гильдейские войны: 2 победы 🏅\n"
        text += "Благословение: 5 участий\n\n"
        text += "Получено титулов: 2\n"
        text += "• Король шахты\n"
        text += "• Герой гильдии"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "monthly":
        monthly = events_data.get("events", {}).get("monthly", {})
        
        text = "🌙 *ЕЖЕМЕСЯЧНЫЕ ИВЕНТЫ*\n\n"
        
        for event_id, event in monthly.items():
            text += f"• *{event.get('name')}*\n"
            text += f"  {event.get('description')}\n"
            if event.get('bonuses'):
                text += f"  Бонусы: {event.get('bonuses')}\n"
            text += f"  Частота: {event.get('frequency')}\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "seasonal":
        seasonal = events_data.get("events", {}).get("seasonal", {})
        
        text = "🍂 *СЕЗОННЫЕ ИВЕНТЫ*\n\n"
        
        for event_id, event in seasonal.items():
            text += f"• *{event.get('name')}*\n"
            text += f"  {event.get('description')}\n"
            text += f"  Сезон: {event.get('season')}\n"
            text += f"  Длительность: {event.get('duration')} дней\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        events_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
