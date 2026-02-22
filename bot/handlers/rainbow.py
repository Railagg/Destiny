import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import time

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def rainbow_command(message):
    """Команда /rainbow - радужные камни"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Получаем количество осколков и камней
    rainbow_shards = character.rainbow_shards if hasattr(character, 'rainbow_shards') else 0
    rainbow_stones = character.rainbow_stones if hasattr(character, 'rainbow_stones') else 0
    
    text = "🌈 *Радужные камни*\n\n"
    text += "Собирай осколки и создавай легендарные предметы!\n\n"
    text += f"📊 Твои осколки: {rainbow_shards}/9\n"
    text += f"💎 Твои камни: {rainbow_stones}\n\n"
    text += "📅 *4-й день входа* - 1 осколок (100%)\n"
    text += "🔥 *Боссы* - шанс 10-60%\n"
    text += "🎁 *Легендарные сундуки* - шанс 25%\n\n"
    text += "🔮 *Крафт камня*: 9 осколков = 1 🌈 камень\n"
    text += "🏠 *Требование*: Алтарь радуги (5 ур. дома)"
    
    markup = InlineKeyboardMarkup(row_width=2)
    if rainbow_shards >= 9:
        markup.add(InlineKeyboardButton("🔮 Скрафтить камень", callback_data="rainbow:craft"))
    markup.add(
        InlineKeyboardButton("📜 Рецепты", callback_data="rainbow:recipes"),
        InlineKeyboardButton("🏆 Титулы", callback_data="rainbow:titles")
    )
    markup.add(
        InlineKeyboardButton("🏠 Улучшения дома", callback_data="rainbow:house"),
        InlineKeyboardButton("ℹ️ О радуге", callback_data="rainbow:info")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func, rainbow_data):
    """Обработка кнопок радужных камней"""
    from main import save_character
    
    data = call.data.split(':')[1]
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Получаем количество осколков и камней
    rainbow_shards = character.rainbow_shards if hasattr(character, 'rainbow_shards') else 0
    rainbow_stones = character.rainbow_stones if hasattr(character, 'rainbow_stones') else 0
    
    if data == "craft":
        if rainbow_shards < 9:
            bot_instance.answer_callback_query(call.id, "❌ Нужно 9 осколков!")
            return
        
        if character.house_level < 5:
            bot_instance.answer_callback_query(call.id, "❌ Нужен 5 уровень дома и алтарь радуги!")
            return
        
        # Запускаем крафт
        craft_time = rainbow_data.get("rainbow", {}).get("craft", {}).get("rainbow_stone", {}).get("craft_time", 86400)
        
        text = "🔮 *Крафт радужного камня*\n\n"
        text += "Ты запустил создание радужного камня!\n"
        text += f"⏳ Время: {craft_time // 3600} часов\n\n"
        text += "Когда камень будет готов, ты получишь уведомление."
        
        # Здесь нужно добавить систему очереди крафта
        # Пока просто тратим ресурсы
        character.rainbow_shards = rainbow_shards - 9
        save_character(character)
        
        bot_instance.answer_callback_query(call.id, "✅ Крафт запущен!")
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
    
    elif data == "recipes":
        uses = rainbow_data.get("rainbow", {}).get("uses", {})
        
        text = "📜 *Рецепты из радужных камней*\n\n"
        for item_id, item in uses.items():
            text += f"• {item.get('name')}\n"
            text += f"  Стоимость: {item.get('cost')} 💎\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "titles":
        titles = rainbow_data.get("rainbow", {}).get("titles", {})
        
        text = "🏆 *Титулы за радужные камни*\n\n"
        for num, title in titles.items():
            text += f"• {title.get('name')} - {title.get('cost')} 💎\n"
            text += f"  {title.get('bonus')}\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "house":
        upgrades = rainbow_data.get("rainbow", {}).get("house_upgrades", {})
        
        text = "🏠 *Улучшения дома за радужные камни*\n\n"
        for item_id, item in upgrades.items():
            text += f"• {item.get('name')} - {item.get('cost')} 💎\n"
            text += f"  {item.get('bonus')}\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "info":
        text = "ℹ️ *О радужных камнях*\n\n"
        text += "Радужные камни — легендарные артефакты, "
        text += "хранящие силу всех стихий.\n\n"
        text += "✨ *Как получить осколки:*\n"
        text += "• 4-й день входа (гарантия)\n"
        text += "• Боссы (10-60%)\n"
        text += "• Легендарные сундуки (25%)\n"
        text += "• Ивенты\n\n"
        text += "💎 *Что можно сделать:*\n"
        text += "• Легендарное оружие\n"
        text += "• Драконье оружие\n"
        text += "• Летающий остров\n"
        text += "• Яйцо дракона\n"
        text += "• Титулы\n"
        text += "• Улучшения дома"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="rainbow:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        rainbow_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
