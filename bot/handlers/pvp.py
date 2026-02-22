import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import random
import time

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def pvp_command(message):
    """Команда /pvp - PvP арена"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Получаем или создаём рейтинг
    pvp_rating = character.pvp_rating if hasattr(character, 'pvp_rating') else 1000
    pvp_wins = character.pvp_wins if hasattr(character, 'pvp_wins') else 0
    pvp_losses = character.pvp_losses if hasattr(character, 'pvp_losses') else 0
    
    text = "⚔️ *PvP АРЕНА*\n\n"
    text += f"📊 Твой рейтинг: {pvp_rating}\n"
    text += f"🏆 Побед: {pvp_wins} | Поражений: {pvp_losses}\n\n"
    text += "🥊 *Тренировочная арена* - без рейтинга, 0💰\n"
    text += "🏆 *Рейтинговая арена* - за рейтинг, 10💰\n"
    text += "👑 *Турнирная арена* - по выходным, 100💰\n\n"
    text += "Выбери режим:"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🥊 Тренировка", callback_data="pvp:training"),
        InlineKeyboardButton("🏆 Рейтинг", callback_data="pvp:ranked")
    )
    markup.add(
        InlineKeyboardButton("👑 Турнир", callback_data="pvp:tournament_info"),
        InlineKeyboardButton("📊 Рейтинг игроков", callback_data="pvp:leaderboard")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func):
    """Обработка кнопок PvP"""
    from main import save_character
    
    data = call.data.split(':')[1]
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    pvp_rating = character.pvp_rating if hasattr(character, 'pvp_rating') else 1000
    
    if data == "training":
        text = "🥊 *Тренировочная арена*\n\n"
        text += "Здесь можно тренироваться без риска для рейтинга.\n"
        text += "Награда: небольшой опыт и золото.\n\n"
        text += "Начать тренировочный бой?"
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("⚔️ Начать бой", callback_data="pvp:fight:training"),
            InlineKeyboardButton("🔙 Назад", callback_data="pvp:menu")
        )
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "ranked":
        if character.gold < 10:
            bot_instance.answer_callback_query(call.id, "❌ Недостаточно золота! Нужно 10💰")
            return
        
        text = "🏆 *Рейтинговая арена*\n\n"
        text += "Бой за рейтинг и ценные награды.\n"
        text += "Вход: 10💰\n"
        text += f"Твой рейтинг: {pvp_rating}\n\n"
        text += "Начать поиск соперника?"
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("⚔️ Искать бой", callback_data="pvp:fight:ranked"),
            InlineKeyboardButton("🔙 Назад", callback_data="pvp:menu")
        )
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("fight:"):
        mode = data.split(':')[1]
        
        # Списываем плату за вход
        if mode == "ranked":
            character.gold -= 10
            save_character(character)
        
        # Генерируем результат боя
        result = random.choice(["win", "lose", "draw"])
        
        if result == "win":
            exp_gain = random.randint(20, 50)
            gold_gain = random.randint(5, 20)
            rating_change = random.randint(10, 25) if mode == "ranked" else 0
            
            character.exp += exp_gain
            character.gold += gold_gain
            if mode == "ranked":
                character.pvp_rating = pvp_rating + rating_change
                character.pvp_wins = (character.pvp_wins or 0) + 1
            
            text = "🎉 *ПОБЕДА!*\n\n"
            text += f"✨ Опыт: +{exp_gain}\n"
            text += f"💰 Золото: +{gold_gain}\n"
            if mode == "ranked":
                text += f"📈 Рейтинг: +{rating_change}\n"
        
        elif result == "lose":
            exp_gain = random.randint(10, 25)
            gold_gain = 0
            rating_change = random.randint(-15, -5) if mode == "ranked" else 0
            
            character.exp += exp_gain
            if mode == "ranked":
                character.pvp_rating = max(0, pvp_rating + rating_change)
                character.pvp_losses = (character.pvp_losses or 0) + 1
            
            text = "💔 *ПОРАЖЕНИЕ*\n\n"
            text += f"✨ Опыт: +{exp_gain}\n"
            if mode == "ranked":
                text += f"📉 Рейтинг: {rating_change}\n"
        
        else:  # draw
            exp_gain = random.randint(15, 30)
            gold_gain = random.randint(3, 10)
            
            character.exp += exp_gain
            character.gold += gold_gain
            
            text = "🤝 *НИЧЬЯ*\n\n"
            text += f"✨ Опыт: +{exp_gain}\n"
            text += f"💰 Золото: +{gold_gain}\n"
        
        save_character(character)
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("⚔️ Ещё бой", callback_data=f"pvp:{mode}"),
            InlineKeyboardButton("🔙 В меню", callback_data="pvp:menu")
        )
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "tournament_info":
        text = "👑 *Турнирная арена*\n\n"
        text += "Турниры проходят каждую пятницу и субботу!\n\n"
        text += "📅 *Расписание:*\n"
        text += "Пятница 20:00 - отборочные\n"
        text += "Суббота 20:00 - финалы\n\n"
        text += "💰 *Взнос:* 100 DSTN\n"
        text += "🏆 *Призы:*\n"
        text += "1 место: 5000 DSTN + титул\n"
        text += "2 место: 2000 DSTN + скин\n"
        text += "3 место: 1000 DSTN + сундук\n"
        text += "4-8 места: 500 DSTN\n"
        text += "9-16 места: 200 DSTN\n"
        text += "Участники: 100 DSTN\n\n"
        text += "Следующий турнир: через 3 дня"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pvp:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "leaderboard":
        # Здесь должен быть запрос к базе данных
        text = "📊 *Топ-10 PvP игроков*\n\n"
        text += "1. Игрок1 - 2500 рейтинга\n"
        text += "2. Игрок2 - 2450 рейтинга\n"
        text += "3. Игрок3 - 2400 рейтинга\n"
        text += "4. Игрок4 - 2350 рейтинга\n"
        text += "5. Игрок5 - 2300 рейтинга\n"
        text += "6. Игрок6 - 2250 рейтинга\n"
        text += "7. Игрок7 - 2200 рейтинга\n"
        text += "8. Игрок8 - 2150 рейтинга\n"
        text += "9. Игрок9 - 2100 рейтинга\n"
        text += "10. Игрок10 - 2050 рейтинга\n\n"
        text += f"Твой рейтинг: {pvp_rating}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pvp:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        pvp_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
