import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def premium_command(message):
    """Команда /premium - премиум-подписка"""
    from main import get_or_create_player, premium_data
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    plans = premium_data.get("premium", {}).get("plans", {})
    
    text = "👑 *PREMIUM DESTINY*\n\n"
    text += "Премиум-подписка даёт невероятные бонусы!\n\n"
    
    for plan_id, plan in plans.items():
        text += f"{plan.get('name')}\n"
        text += f"├ Цена: {plan.get('price_stars')}⭐ / {plan.get('price_ton')} TON\n"
        text += f"├ Энергия: {plan.get('bonuses', {}).get('max_energy', 100)}\n"
        text += f"├ +{int((plan.get('bonuses', {}).get('gold_multiplier', 1)-1)*100)}% золота\n"
        text += f"├ +{int((plan.get('bonuses', {}).get('exp_multiplier', 1)-1)*100)}% опыта\n"
        text += f"└ Сундуков в день: +{plan.get('bonuses', {}).get('chests_per_day', 0)}\n\n"
    
    text += "🎁 *Подарок при покупке:* легендарный сундук!\n"
    text += "💎 *Первая покупка:* скидка 50% на Stars, 25% на TON!"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🟢 7 дней - 50⭐", callback_data="premium:7days"),
        InlineKeyboardButton("🔵 28 дней - 150⭐", callback_data="premium:28days"),
        InlineKeyboardButton("🟣 90 дней - 400⭐", callback_data="premium:90days"),
        InlineKeyboardButton("🟡 180 дней - 700⭐", callback_data="premium:180days"),
        InlineKeyboardButton("🔴 365 дней - 1200⭐", callback_data="premium:365days")
    )
    markup.add(
        InlineKeyboardButton("ℹ️ О премиуме", callback_data="premium:info"),
        InlineKeyboardButton("📊 Мой статус", callback_data="premium:status")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func, premium_data):
    """Обработка кнопок премиума"""
    from main import save_character
    
    data = call.data.split(':')[1]
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    plans = premium_data.get("premium", {}).get("plans", {})
    
    if data in plans:
        plan = plans[data]
        
        text = f"{plan.get('name')}\n\n"
        text += f"💰 Цена: {plan.get('price_stars')}⭐ / {plan.get('price_ton')} TON / {plan.get('price_dstn')} DSTN\n"
        text += f"📅 Длительность: {plan.get('duration')} дней\n\n"
        text += "✨ *Бонусы:*\n"
        for bonus, value in plan.get('bonuses', {}).items():
            if isinstance(value, (int, float)):
                if 'multiplier' in bonus:
                    text += f"• {bonus}: +{int((value-1)*100)}%\n"
                else:
                    text += f"• {bonus}: {value}\n"
        
        text += f"\n🎁 *Подарок:* {plan.get('gift', {}).get('legendary_chest', 0)} легендарных сундуков"
        
        first_purchase = premium_data.get("premium", {}).get("first_purchase_bonus", {})
        if first_purchase.get("enabled"):
            text += f"\n\n🎉 *Первая покупка:* скидка {first_purchase.get('stars_discount')}% на Stars!"
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("💎 Купить за Stars", callback_data=f"premium:buy_stars:{data}"),
            InlineKeyboardButton("💎 Купить за TON", callback_data=f"premium:buy_ton:{data}"),
            InlineKeyboardButton("💰 Купить за DSTN", callback_data=f"premium:buy_dstn:{data}")
        )
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="premium:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("buy_"):
        parts = data.split('_')
        payment = parts[1]
        plan_id = parts[2]
        
        plan = plans.get(plan_id, {})
        
        bot_instance.answer_callback_query(call.id, "🔜 Скоро будет доступно")
        bot_instance.edit_message_text(
            f"🔜 *Покупка {plan.get('name')}*\n\n"
            f"Оплата через {payment.upper()} появится в ближайшее время.\n\n"
            f"Цена: {plan.get(f'price_{payment}')} {payment.upper()}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
    
    elif data == "info":
        text = "ℹ️ *О премиум-подписке*\n\n"
        text += "Премиум-подписка даёт:\n\n"
        text += "⚡ *Больше энергии* - до 250\n"
        text += "💰 *Больше золота* - до +30%\n"
        text += "✨ *Больше опыта* - до +30%\n"
        text += "🎁 *Дополнительные сундуки*\n"
        text += "🏠 *Улучшенный отдых* в доме\n"
        text += "📦 *Больше слотов* в инвентаре\n"
        text += "💱 *Лучший курс* в обменнике\n"
        text += "🐾 *Бонусы для питомцев*\n\n"
        text += "🎁 *Подарки при покупке*\n"
        text += "🏆 *Бонусы за продление* (3м, 6м, 1г, 2г, 3г)"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="premium:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "status":
        # Проверяем статус премиума
        premium_until = character.premium_until if hasattr(character, 'premium_until') else None
        
        if premium_until and premium_until > datetime.utcnow():
            days_left = (premium_until - datetime.utcnow()).days
            text = f"👑 *Твой премиум статус*\n\n"
            text += f"✅ Активен\n"
            text += f"📅 Истекает через: {days_left} дней\n"
            text += f"📊 План: {character.premium_plan or 'Неизвестно'}"
        else:
            text = "👑 *Твой премиум статус*\n\n"
            text += "❌ Премиум не активен\n\n"
            text += "Купи подписку, чтобы получить бонусы!"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="premium:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        premium_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
