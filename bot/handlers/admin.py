import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
from datetime import datetime

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# Список администраторов (ID Telegram)
ADMIN_IDS = [2083128064]  # Замени на свой ID

def admin_command(message):
    """Команда /admin - админ-панель"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ У тебя нет прав администратора!")
        return
    
    text = "👨‍💻 *АДМИН-ПАНЕЛЬ*\n\n"
    text += "Выбери действие:\n\n"
    text += "📊 Статистика\n"
    text += "👥 Управление игроками\n"
    text += "🎁 Выдача предметов\n"
    text += "📢 Рассылка\n"
    text += "⚙️ Настройки"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin:stats"),
        InlineKeyboardButton("👥 Игроки", callback_data="admin:players"),
        InlineKeyboardButton("🎁 Выдать", callback_data="admin:give"),
        InlineKeyboardButton("📢 Рассылка", callback_data="admin:broadcast"),
        InlineKeyboardButton("⚙️ Настройки", callback_data="admin:settings")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func):
    """Обработка админ-кнопок"""
    from main import save_character
    
    user_id = call.from_user.id
    
    if user_id not in ADMIN_IDS:
        bot_instance.answer_callback_query(call.id, "❌ Нет прав!")
        return
    
    data = call.data.split(':')[1]
    
    if data == "stats":
        text = "📊 *СТАТИСТИКА СЕРВЕРА*\n\n"
        text += "👥 Всего игроков: 1,234\n"
        text += "🟢 Онлайн: 56\n"
        text += "📈 Активных сегодня: 234\n"
        text += "📅 Активных за неделю: 1,023\n\n"
        text += "💰 Всего золота: 45,678,901\n"
        text += "💎 Всего DSTN: 12,345,678\n"
        text += "🏠 Построено домов: 567\n"
        text += "🐾 Заведено питомцев: 890\n\n"
        text += "⚔️ Всего боёв: 23,456\n"
        text += "🏛️ Гильдий создано: 45\n"
        text += "🎁 Сундуков открыто: 12,345"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "players":
        text = "👥 *УПРАВЛЕНИЕ ИГРОКАМИ*\n\n"
        text += "Отправь команду:\n"
        text += "`/admin info [id]` - информация об игроке\n"
        text += "`/admin give [id] [item] [count]` - выдать предмет\n"
        text += "`/admin gold [id] [amount]` - выдать золото\n"
        text += "`/admin dstn [id] [amount]` - выдать DSTN\n"
        text += "`/admin level [id] [level]` - установить уровень\n"
        text += "`/admin ban [id]` - забанить игрока"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "give":
        text = "🎁 *ВЫДАЧА ПРЕДМЕТОВ*\n\n"
        text += "Выбери тип предмета для выдачи:\n\n"
        text += "⚔️ Оружие\n"
        text += "🛡️ Броня\n"
        text += "💎 Ресурсы\n"
        text += "🧪 Зелья\n"
        text += "🎁 Сундуки\n"
        text += "🌈 Радужные осколки"
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("⚔️ Оружие", callback_data="admin:give_weapons"),
            InlineKeyboardButton("🛡️ Броня", callback_data="admin:give_armor"),
            InlineKeyboardButton("💎 Ресурсы", callback_data="admin:give_resources"),
            InlineKeyboardButton("🧪 Зелья", callback_data="admin:give_potions"),
            InlineKeyboardButton("🎁 Сундуки", callback_data="admin:give_chests"),
            InlineKeyboardButton("🌈 Осколки", callback_data="admin:give_rainbow")
        )
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "give_rainbow":
        text = "🌈 *ВЫДАЧА РАДУЖНЫХ ОСКОЛКОВ*\n\n"
        text += "Отправь команду:\n"
        text += "`/admin give [id] rainbow_shard [количество]`\n\n"
        text += "Например:\n"
        text += "`/admin give 123456789 rainbow_shard 9`\n"
        text += "`/admin give 123456789 rainbow_stone 1`"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin:give"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "broadcast":
        text = "📢 *РАССЫЛКА*\n\n"
        text += "Отправь сообщение для рассылки всем игрокам:\n\n"
        text += "Формат: `/broadcast [текст]`\n\n"
        text += "Например:\n"
        text += "`/broadcast Внимание! Сегодня двойной опыт!`"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "settings":
        text = "⚙️ *НАСТРОЙКИ*\n\n"
        text += "• Режим обслуживания: ❌\n"
        text += "• Двойной опыт: ❌\n"
        text += "• Двойное золото: ❌\n"
        text += "• Ивент режим: ❌\n\n"
        text += "Изменить настройки можно в конфиге."
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        admin_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
