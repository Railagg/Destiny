# /bot/handlers/events.py
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import random
import time
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ ИВЕНТОВ
# ============================================

WEEKDAYS_RU = {
    "monday": "ПН",
    "tuesday": "ВТ", 
    "wednesday": "СР",
    "thursday": "ЧТ",
    "friday": "ПТ",
    "saturday": "СБ",
    "sunday": "ВС"
}

MONTHS_RU = {
    "january": "Январь",
    "february": "Февраль",
    "march": "Март",
    "april": "Апрель",
    "may": "Май",
    "june": "Июнь",
    "july": "Июль",
    "august": "Август",
    "september": "Сентябрь",
    "october": "Октябрь",
    "november": "Ноябрь",
    "december": "Декабрь"
}

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

def events_command(message, bot_instance, events_data):
    """Команда /events - ивенты"""
    weekly = events_data.get("events", {}).get("weekly", {})
    
    # Определяем сегодняшний день
    today = datetime.now().strftime("%A").lower()
    
    text = "🎪 *ИВЕНТЫ DESTINY*\n\n"
    
    # Показываем сегодняшний ивент
    if today in weekly:
        event = weekly[today]
        text += f"👉 *СЕГОДНЯ*: {event.get('name')}\n"
        text += f"{event.get('description')}\n"
        if event.get('bonuses'):
            bonuses = []
            for bonus, value in event.get('bonuses', {}).items():
                if isinstance(value, (int, float)):
                    if value > 1:
                        bonuses.append(f"{bonus} x{value}")
                    else:
                        bonuses.append(f"{bonus} +{int((value-1)*100)}%")
            if bonuses:
                text += f"✨ Бонусы: {', '.join(bonuses)}\n"
        text += "\n"
    
    # Активные ивенты
    active_events = get_active_events(events_data)
    if active_events:
        text += "🔥 *Активные ивенты:*\n"
        for event in active_events[:3]:
            remaining = get_remaining_time(event)
            text += f"• {event.get('name')} - осталось {remaining}\n"
        text += "\n"
    
    # Ближайшие ивенты
    upcoming = get_upcoming_events(events_data)
    if upcoming:
        text += "⏳ *Скоро:*\n"
        for event in upcoming[:3]:
            start = event.get('start_date', 'скоро')
            text += f"• {event.get('name')} ({start})\n"
    
    text += "\n🏆 Участвуй в ивентах, получай награды и титулы!"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📅 Неделя", callback_data="events:weekly"),
        InlineKeyboardButton("🌙 Месяц", callback_data="events:monthly"),
        InlineKeyboardButton("🍂 Сезонные", callback_data="events:seasonal"),
        InlineKeyboardButton("🏆 Достижения", callback_data="events:achievements"),
        InlineKeyboardButton("🎫 Магазин", callback_data="events:shop"),
        InlineKeyboardButton("📊 Статистика", callback_data="events:stats")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_weekly_events(call, bot_instance, events_data):
    """Показать еженедельные ивенты"""
    weekly = events_data.get("events", {}).get("weekly", {})
    today = datetime.now().strftime("%A").lower()
    
    text = "📅 *ЕЖЕНЕДЕЛЬНЫЕ ИВЕНТЫ*\n\n"
    
    for day, event in weekly.items():
        day_name = WEEKDAYS_RU.get(day, day.capitalize())
        prefix = "👉 " if day == today else "• "
        text += f"{prefix}*{day_name}:* {event.get('name')}\n"
        text += f"  {event.get('description')}\n"
        
        # Показываем конкурс, если есть
        if event.get('competition'):
            comp = event['competition']
            text += f"  🏆 Конкурс: {comp.get('name')}\n"
        
        # Бонусы
        if event.get('bonuses'):
            bonuses = []
            for bonus, value in event.get('bonuses', {}).items():
                if isinstance(value, (int, float)):
                    if value > 1:
                        bonuses.append(f"{bonus} x{value}")
                    else:
                        bonuses.append(f"{bonus} +{int((value-1)*100)}%")
            if bonuses:
                text += f"  ✨ {', '.join(bonuses)}\n"
        
        text += "\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🎯 Мои награды", callback_data="events:my_rewards"),
        InlineKeyboardButton("🔙 Назад", callback_data="events:menu")
    )
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_monthly_events(call, bot_instance, events_data):
    """Показать ежемесячные ивенты"""
    monthly = events_data.get("events", {}).get("monthly", {})
    
    text = "🌙 *ЕЖЕМЕСЯЧНЫЕ ИВЕНТЫ*\n\n"
    
    for event_id, event in monthly.items():
        text += f"• *{event.get('name')}*\n"
        text += f"  {event.get('description')}\n"
        
        if event.get('frequency'):
            text += f"  🗓️ {event.get('frequency')}"
            if event.get('day'):
                text += f" ({event.get('day')} число)"
            text += "\n"
        
        if event.get('bonuses'):
            bonuses = []
            for bonus, value in event.get('bonuses', {}).items():
                if isinstance(value, (int, float)):
                    if value > 1:
                        bonuses.append(f"{bonus} x{value}")
                    elif value < 1:
                        bonuses.append(f"{bonus} +{int((1-value)*100)}%")
            if bonuses:
                text += f"  ✨ {', '.join(bonuses)}\n"
        
        if event.get('special_mobs'):
            text += f"  👾 Особые враги: {', '.join(event['special_mobs'])}\n"
        
        text += "\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_seasonal_events(call, bot_instance, events_data):
    """Показать сезонные ивенты"""
    seasonal = events_data.get("events", {}).get("seasonal", {})
    
    text = "🍂 *СЕЗОННЫЕ ИВЕНТЫ*\n\n"
    
    # Текущий сезон
    current_month = datetime.now().strftime("%B").lower()
    current_season = get_current_season(current_month)
    
    text += f"Сейчас: *{current_season}*\n\n"
    
    for event_id, event in seasonal.items():
        season = event.get('season', '').capitalize()
        is_current = season.lower() == current_season.lower()
        
        prefix = "🌟 " if is_current else "• "
        text += f"{prefix}*{event.get('name')}*\n"
        text += f"  {event.get('description')}\n"
        text += f"  Сезон: {season}"
        if event.get('duration'):
            text += f", длительность {event['duration']} дней"
        text += "\n"
        
        if event.get('bonuses'):
            bonuses = []
            for bonus, value in event.get('bonuses', {}).items():
                if isinstance(value, (int, float)):
                    if value > 1:
                        bonuses.append(f"{bonus} x{value}")
                    else:
                        bonuses.append(f"{bonus} +{int((value-1)*100)}%")
            if bonuses:
                text += f"  ✨ {', '.join(bonuses)}\n"
        
        if event.get('activities'):
            text += f"  🎯 Активности: {', '.join(event['activities'])}\n"
        
        if event.get('rewards'):
            text += f"  🏆 Награды: {', '.join(event['rewards'].values())}\n"
        
        text += "\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_event_achievements(call, bot_instance, events_data):
    """Показать достижения за ивенты"""
    achievements = events_data.get("events", {}).get("event_achievements", {})
    
    text = "🏆 *ДОСТИЖЕНИЯ ЗА ИВЕНТЫ*\n\n"
    
    for ach_id, ach in achievements.items():
        text += f"• *{ach.get('name')}*\n"
        text += f"  {ach.get('requirement')}\n"
        
        rewards = []
        reward_data = ach.get('reward', {})
        if reward_data.get('title'):
            rewards.append(f"титул '{reward_data['title']}'")
        if reward_data.get('rainbow_shard'):
            rewards.append(f"{reward_data['rainbow_shard']}🌈")
        if reward_data.get('legendary_chest'):
            rewards.append(f"{reward_data['legendary_chest']}🎁")
        if reward_data.get('statue'):
            rewards.append("статуя 🏛️")
        
        if rewards:
            text += f"  🎁 Награда: {', '.join(rewards)}\n"
        text += "\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_event_shop(call, bot_instance, events_data):
    """Показать магазин ивентов"""
    shop = events_data.get("events", {}).get("event_shop", {})
    
    text = "🎫 *МАГАЗИН ИВЕНТОВ*\n\n"
    text += f"Валюта: {shop.get('currency', 'event_token')}\n\n"
    
    items = shop.get('items', {})
    for item_id, item_data in items.items():
        text += f"• {item_data.get('item_name', item_id)} - {item_data.get('price')} токенов\n"
    
    text += "\nТокены можно получить за участие в ивентах!"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_event_stats(call, bot_instance, events_data):
    """Показать статистику ивентов"""
    from main import get_or_create_player
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    event_stats = character.event_stats or {}
    
    text = "📊 *МОЯ СТАТИСТИКА ИВЕНТОВ*\n\n"
    
    # Еженедельные
    text += "*📅 Еженедельные:*\n"
    weekly_wins = event_stats.get('weekly_wins', {})
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        day_name = WEEKDAYS_RU.get(day, day.capitalize())
        wins = weekly_wins.get(day, 0)
        text += f"• {day_name}: {wins} побед\n"
    
    # Турниры
    text += f"\n*⚔️ PvP турниры:*\n"
    text += f"• Участий: {event_stats.get('pvp_participations', 0)}\n"
    text += f"• Побед: {event_stats.get('pvp_wins', 0)}\n"
    text += f"• Лучшее место: {event_stats.get('pvp_best', '—')}\n"
    
    # Гильдейские войны
    text += f"\n*🏛️ Гильдейские войны:*\n"
    text += f"• Участий: {event_stats.get('guild_wars', 0)}\n"
    text += f"• Побед: {event_stats.get('guild_wins', 0)}\n"
    
    # Сезонные
    text += f"\n*🍂 Сезонные ивенты:*\n"
    text += f"• Участий: {event_stats.get('seasonal_participations', 0)}\n"
    
    # Токены
    text += f"\n🎫 Токенов ивентов: {event_stats.get('event_tokens', 0)}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_my_rewards(call, bot_instance, events_data):
    """Показать мои награды за ивенты"""
    from main import get_or_create_player
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    achievements = character.event_achievements or []
    titles = character.titles or []
    
    text = "🏆 *МОИ НАГРАДЫ ЗА ИВЕНТЫ*\n\n"
    
    if achievements:
        text += "*📜 Полученные достижения:*\n"
        for ach in achievements[-5:]:  # Последние 5
            text += f"• {ach}\n"
    else:
        text += "Пока нет достижений\n"
    
    if titles:
        text += f"\n*👑 Титулы:*\n"
        for title in titles[-5:]:
            text += f"• {title}\n"
    
    text += f"\n📊 Всего достижений: {len(achievements)}"
    text += f"\n🏅 Всего титулов: {len(titles)}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_event_calendar(call, bot_instance, events_data):
    """Показать календарь ивентов"""
    calendar = events_data.get("events", {}).get("event_calendar", {})
    
    text = "📅 *КАЛЕНДАРЬ ИВЕНТОВ НА 2024*\n\n"
    
    for month, events in calendar.items():
        month_name = MONTHS_RU.get(month, month.capitalize())
        text += f"*{month_name}:*\n"
        for event in events:
            event_data = events_data.get("events", {}).get("seasonal", {}).get(event, {})
            event_name = event_data.get('name', event)
            text += f"• {event_name}\n"
        text += "\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="events:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def get_active_events(events_data):
    """Получить активные ивенты"""
    active = []
    
    # Проверяем сезонные
    seasonal = events_data.get("events", {}).get("seasonal", {})
    current_month = datetime.now().strftime("%B").lower()
    
    for event_id, event in seasonal.items():
        season = event.get('season', '').lower()
        if season == get_current_season(current_month):
            active.append(event)
    
    # Проверяем ежемесячные
    monthly = events_data.get("events", {}).get("monthly", {})
    for event_id, event in monthly.items():
        if event.get('frequency') == 'monthly':
            day = event.get('day')
            if day == 'random' or day == datetime.now().day:
                active.append(event)
    
    return active

def get_upcoming_events(events_data):
    """Получить ближайшие ивенты"""
    upcoming = []
    
    # Проверяем сезонные
    seasonal = events_data.get("events", {}).get("seasonal", {})
    current_month = datetime.now().strftime("%B").lower()
    months = list(MONTHS_RU.keys())
    current_index = months.index(current_month) if current_month in months else -1
    
    for event_id, event in seasonal.items():
        for month_name, events in events_data.get("events", {}).get("event_calendar", {}).items():
            if event_id in events:
                month_index = months.index(month_name) if month_name in months else -1
                if month_index > current_index or (month_index == current_index and month_index >= 0):
                    upcoming.append(event)
    
    return upcoming

def get_remaining_time(event):
    """Получить оставшееся время ивента"""
    duration = event.get('duration', 1)
    # В реальной игре нужно считать от начала ивента
    return f"{duration} дней"

def get_current_season(month):
    """Определить текущий сезон по месяцу"""
    spring = ["march", "april", "may"]
    summer = ["june", "july", "august"]
    autumn = ["september", "october", "november"]
    winter = ["december", "january", "february"]
    
    if month in spring:
        return "spring"
    elif month in summer:
        return "summer"
    elif month in autumn:
        return "autumn"
    else:
        return "winter"

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, events_data):
    """Обработка кнопок ивентов"""
    data = call.data.split(':')[1]
    
    if data == "menu":
        events_command(call.message, bot_instance, events_data)
    
    elif data == "weekly":
        show_weekly_events(call, bot_instance, events_data)
    
    elif data == "monthly":
        show_monthly_events(call, bot_instance, events_data)
    
    elif data == "seasonal":
        show_seasonal_events(call, bot_instance, events_data)
    
    elif data == "achievements":
        show_event_achievements(call, bot_instance, events_data)
    
    elif data == "shop":
        show_event_shop(call, bot_instance, events_data)
    
    elif data == "stats":
        show_event_stats(call, bot_instance, events_data)
    
    elif data == "my_rewards":
        show_my_rewards(call, bot_instance, events_data)
    
    elif data == "calendar":
        show_event_calendar(call, bot_instance, events_data)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'events_command',
    'handle_callback',
    'get_active_events',
    'get_upcoming_events',
    'get_current_season'
]
