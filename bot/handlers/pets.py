import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import random
import time

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def pets_command(message):
    """Команда /pets - питомцы"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Получаем список питомцев игрока
    pets = character.get_pets() if hasattr(character, 'get_pets') else []
    
    text = "🐾 *Твои питомцы*\n\n"
    
    if not pets:
        text += "У тебя пока нет питомцев.\n"
        text += "Питомцев можно найти:\n"
        text += "• В лесу (волчонок, медвежонок)\n"
        text += "• У озера (выдра, лягушка)\n"
        text += "• В деревне (кошка, собака)\n"
        text += "• В особых событиях"
    else:
        for pet_id in pets[:5]:  # Показываем первых 5
            text += f"• {pet_id}\n"
        
        if len(pets) > 5:
            text += f"...и ещё {len(pets) - 5} питомцев"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📋 Список питомцев", callback_data="pets:list"),
        InlineKeyboardButton("🍖 Корм", callback_data="pets:food")
    )
    markup.add(
        InlineKeyboardButton("🏠 В конуру", callback_data="pets:house"),
        InlineKeyboardButton("❓ Помощь", callback_data="pets:help")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func, pets_data):
    """Обработка кнопок питомцев"""
    from main import save_character
    
    data = call.data.split(':')[1]
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if data == "list":
        pets = character.get_pets() if hasattr(character, 'get_pets') else []
        
        if not pets:
            text = "🐾 *У тебя нет питомцев*\n\n"
            text += "Где найти питомца:\n"
            text += "🐺 Волчонок - в лесу (редкий дроп с волчицы)\n"
            text += "🐻 Медвежонок - в горах\n"
            text += "🐱 Кошка - в деревне\n"
            text += "🐕 Собака - в деревне\n"
            text += "🦊 Лисёнок - в лесу\n"
            text += "🐉 Дракончик - особое событие"
        else:
            text = "🐾 *Твои питомцы*\n\n"
            for pet_id in pets:
                if pet_id in pets_data.get("pets", {}).get("common", {}):
                    pet = pets_data["pets"]["common"][pet_id]
                    text += f"• {pet.get('name', pet_id)}\n"
                    text += f"  Уровень: {pet.get('level', 1)} | Счастье: {pet.get('happiness', 100)}%\n"
                elif pet_id in pets_data.get("pets", {}).get("rare", {}):
                    pet = pets_data["pets"]["rare"][pet_id]
                    text += f"• {pet.get('name', pet_id)}\n"
                    text += f"  Уровень: {pet.get('level', 1)} | Счастье: {pet.get('happiness', 100)}%\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "food":
        text = "🍖 *Корм для питомцев*\n\n"
        text += "Корм можно:\n"
        text += "• Купить у торговца\n"
        text += "• Приготовить самому\n"
        text += "• Найти в сундуках\n\n"
        text += "Виды корма:\n"
        text += "• Мясо - +10 опыта\n"
        text += "• Рыба - +15 опыта\n"
        text += "• Ягоды - +5 опыта\n"
        text += "• Волшебный корм - +50 опыта\n"
        text += "• Лакомство - +20 счастья"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "house":
        house_level = character.house_level or 0
        
        if house_level < 5:
            text = "🏠 *Домик для питомцев*\n\n"
            text += "Домик для питомцев доступен на 5 уровне усадьбы.\n\n"
            text += f"Твой уровень дома: {house_level}\n"
            text += "До 5 уровня осталось улучшений!"
        else:
            text = "🏠 *Домик для питомцев*\n\n"
            text += "В твоей усадьбе есть место для питомцев!\n"
            text += "Вместимость: 2 питомца\n"
            text += "Бонусы:\n"
            text += "• +20% к счастью\n"
            text += "• +10% к опыту"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "help":
        text = "🐾 *Система питомцев*\n\n"
        text += "Питомцы — верные друзья, которые помогают в приключениях.\n\n"
        text += "📊 *Характеристики:*\n"
        text += "• Уровень - растёт от кормления\n"
        text += "• Счастье - падает со временем, растёт от игр\n"
        text += "• Способности - открываются на уровнях\n\n"
        text += "🎯 *Бонусы:*\n"
        text += "• Кошка - +3% к удаче\n"
        text += "• Собака - предупреждает об опасности\n"
        text += "• Лиса - +5% к поиску сокровищ\n"
        text += "• Волк - +10% к урону\n"
        text += "• Дракончик - +15% ко всему\n\n"
        text += "🍖 Кормить: /pet feed [имя]\n"
        text += "🎮 Играть: /pet play [имя]"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pets:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        pets_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
