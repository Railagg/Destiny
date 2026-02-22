import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def top_command(message):
    """Команда /top - рейтинги"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    text = "🏆 *РЕЙТИНГИ*\n\n"
    text += "Выбери категорию:\n\n"
    text += "📊 По уровню\n"
    text += "💰 По богатству\n"
    text += "⚔️ По PvP рейтингу\n"
    text += "🏛️ По гильдиям\n"
    text += "📈 По достижениям\n"
    text += "⛏️ По добыче"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 По уровню", callback_data="top:level"),
        InlineKeyboardButton("💰 По богатству", callback_data="top:gold"),
        InlineKeyboardButton("⚔️ PvP рейтинг", callback_data="top:pvp"),
        InlineKeyboardButton("🏛️ Гильдии", callback_data="top:guilds"),
        InlineKeyboardButton("📈 Достижения", callback_data="top:achievements"),
        InlineKeyboardButton("⛏️ Добыча", callback_data="top:mining")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func):
    """Обработка кнопок рейтингов"""
    from main import save_character
    
    data = call.data.split(':')[1]
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if data == "level":
        # Здесь должен быть запрос к базе данных
        text = "📊 *ТОП-10 ПО УРОВНЮ*\n\n"
        text += "1. Игрок1 - уровень 50 (престиж 5)\n"
        text += "2. Игрок2 - уровень 48 (престиж 4)\n"
        text += "3. Игрок3 - уровень 47 (престиж 4)\n"
        text += "4. Игрок4 - уровень 45 (престиж 3)\n"
        text += "5. Игрок5 - уровень 44 (престиж 3)\n"
        text += "6. Игрок6 - уровень 42 (престиж 2)\n"
        text += "7. Игрок7 - уровень 41 (престиж 2)\n"
        text += "8. Игрок8 - уровень 40 (престиж 2)\n"
        text += "9. Игрок9 - уровень 38 (престиж 1)\n"
        text += "10. Игрок10 - уровень 37 (престиж 1)\n\n"
        text += f"Твоё место: #{character.level} с уровнем {character.level}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="top:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "gold":
        text = "💰 *ТОП-10 ПО БОГАТСТВУ*\n\n"
        text += "1. Игрок1 - 5,234,567💰\n"
        text += "2. Игрок2 - 4,123,456💰\n"
        text += "3. Игрок3 - 3,456,789💰\n"
        text += "4. Игрок4 - 2,987,654💰\n"
        text += "5. Игрок5 - 2,345,678💰\n"
        text += "6. Игрок6 - 1,876,543💰\n"
        text += "7. Игрок7 - 1,543,210💰\n"
        text += "8. Игрок8 - 1,234,567💰\n"
        text += "9. Игрок9 - 987,654💰\n"
        text += "10. Игрок10 - 765,432💰\n\n"
        text += f"Твоё золото: {character.gold}💰"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="top:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "pvp":
        pvp_rating = character.pvp_rating if hasattr(character, 'pvp_rating') else 1000
        
        text = "⚔️ *ТОП-10 ПО PvP РЕЙТИНГУ*\n\n"
        text += "1. Игрок1 - 2850 рейтинга\n"
        text += "2. Игрок2 - 2740 рейтинга\n"
        text += "3. Игрок3 - 2630 рейтинга\n"
        text += "4. Игрок4 - 2520 рейтинга\n"
        text += "5. Игрок5 - 2410 рейтинга\n"
        text += "6. Игрок6 - 2300 рейтинга\n"
        text += "7. Игрок7 - 2190 рейтинга\n"
        text += "8. Игрок8 - 2080 рейтинга\n"
        text += "9. Игрок9 - 1970 рейтинга\n"
        text += "10. Игрок10 - 1860 рейтинга\n\n"
        text += f"Твой рейтинг: {pvp_rating}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="top:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "guilds":
        text = "🏛️ *ТОП-10 ГИЛЬДИЙ*\n\n"
        text += "1. Легенда - уровень 5 (48 участников)\n"
        text += "2. Хранители - уровень 5 (45 участников)\n"
        text += "3. Воины света - уровень 4 (38 участников)\n"
        text += "4. Тёмная стая - уровень 4 (35 участников)\n"
        text += "5. Серебряные драконы - уровень 3 (30 участников)\n"
        text += "6. Охотники - уровень 3 (28 участников)\n"
        text += "7. Маги стихий - уровень 2 (22 участника)\n"
        text += "8. Кузнецы судьбы - уровень 2 (20 участников)\n"
        text += "9. Странники - уровень 1 (15 участников)\n"
        text += "10. Избранные - уровень 1 (12 участников)"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="top:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "achievements":
        text = "📈 *ТОП-10 ПО ДОСТИЖЕНИЯМ*\n\n"
        text += "1. Игрок1 - 87 достижений\n"
        text += "2. Игрок2 - 82 достижения\n"
        text += "3. Игрок3 - 78 достижений\n"
        text += "4. Игрок4 - 75 достижений\n"
        text += "5. Игрок5 - 71 достижение\n"
        text += "6. Игрок6 - 68 достижений\n"
        text += "7. Игрок7 - 64 достижения\n"
        text += "8. Игрок8 - 61 достижение\n"
        text += "9. Игрок9 - 58 достижений\n"
        text += "10. Игрок10 - 55 достижений\n\n"
        achievements_count = character.achievements_count if hasattr(character, 'achievements_count') else 0
        text += f"Твои достижения: {achievements_count}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="top:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "mining":
        text = "⛏️ *ТОП-10 ПО ДОБЫЧЕ*\n\n"
        text += "1. Игрок1 - 45,678 руды\n"
        text += "2. Игрок2 - 43,210 руды\n"
        text += "3. Игрок3 - 38,765 руды\n"
        text += "4. Игрок4 - 34,567 руды\n"
        text += "5. Игрок5 - 31,234 руды\n"
        text += "6. Игрок6 - 28,901 руды\n"
        text += "7. Игрок7 - 25,678 руды\n"
        text += "8. Игрок8 - 23,456 руды\n"
        text += "9. Игрок9 - 21,234 руды\n"
        text += "10. Игрок10 - 19,012 руды\n\n"
        ore_mined = character.ore_mined if hasattr(character, 'ore_mined') else 0
        text += f"Твоя добыча: {ore_mined} руды"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="top:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        top_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
