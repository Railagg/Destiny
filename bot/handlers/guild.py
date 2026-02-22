import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import time
import random

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def guild_command(message):
    """Команда /guild - гильдии"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Проверяем, состоит ли игрок в гильдии
    guild_id = character.guild_id if hasattr(character, 'guild_id') else None
    
    text = "🏛️ *ГИЛЬДИИ*\n\n"
    
    if guild_id:
        # Загружаем данные гильдии
        try:
            with open('data/guilds.json', 'r', encoding='utf-8') as f:
                guilds_data = json.load(f)
            guild = guilds_data.get("guilds", {}).get(str(guild_id), {})
            text += f"Ты в гильдии: *{guild.get('name', 'Неизвестно')}*\n"
            text += f"Уровень: {guild.get('level', 1)}\n"
            text += f"Участников: {len(guild.get('members', []))}/{guild.get('max_members', 10)}\n\n"
        except:
            text += "Ты в гильдии\n\n"
    else:
        text += "Ты не состоишь в гильдии.\n\n"
        text += "Гильдии позволяют:\n"
        text += "• Общаться с единомышленниками\n"
        text += "• Получать общие бонусы\n"
        text += "• Участвовать в гильдейских войнах\n"
        text += "• Иметь общий банк и хранилище\n"
        text += "• Строить гильдейские здания\n\n"
        text += "Создать гильдию: 5000💰 или 500 DSTN"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    if guild_id:
        markup.add(
            InlineKeyboardButton("🏛️ Зал гильдии", callback_data="guild:hall"),
            InlineKeyboardButton("📋 Участники", callback_data="guild:members")
        )
        markup.add(
            InlineKeyboardButton("🏗️ Здания", callback_data="guild:buildings"),
            InlineKeyboardButton("⚔️ Войны", callback_data="guild:wars")
        )
        markup.add(
            InlineKeyboardButton("📊 Вклад", callback_data="guild:contributions"),
            InlineKeyboardButton("⚙️ Управление", callback_data="guild:management")
        )
    else:
        markup.add(
            InlineKeyboardButton("📋 Список гильдий", callback_data="guild:list"),
            InlineKeyboardButton("🏗️ Создать гильдию", callback_data="guild:create")
        )
        markup.add(
            InlineKeyboardButton("ℹ️ О гильдиях", callback_data="guild:info")
        )
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func):
    """Обработка кнопок гильдий"""
    from main import save_character
    
    data = call.data.split(':')[1]
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    guild_id = character.guild_id if hasattr(character, 'guild_id') else None
    
    if data == "list":
        # Загружаем список гильдий
        try:
            with open('data/guilds.json', 'r', encoding='utf-8') as f:
                guilds_data = json.load(f)
            guilds = guilds_data.get("guilds", {})
        except:
            guilds = {}
        
        text = "📋 *Список гильдий*\n\n"
        
        if not guilds:
            text += "Пока нет созданных гильдий.\n"
            text += "Стань первым, кто создаст гильдию!"
        else:
            for gid, guild in list(guilds.items())[:10]:  # Показываем первые 10
                text += f"• *{guild.get('name')}* (ур. {guild.get('level', 1)})\n"
                text += f"  Участников: {len(guild.get('members', []))}/{guild.get('max_members', 10)}\n"
                text += f"  Лидер: {guild.get('leader_name', 'Неизвестно')}\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "create":
        if guild_id:
            bot_instance.answer_callback_query(call.id, "❌ Ты уже в гильдии!")
            return
        
        # Проверяем ресурсы
        if character.gold < 5000 and character.destiny_tokens < 500:
            bot_instance.answer_callback_query(call.id, "❌ Недостаточно ресурсов! Нужно 5000💰 или 500 DSTN")
            return
        
        text = "🏗️ *Создание гильдии*\n\n"
        text += "Отправь название гильдии (до 20 символов).\n\n"
        text += "Например: `Хранители`\n\n"
        text += "Или нажми отмену."
        
        # Здесь нужно будет реализовать ожидание ответа
        bot_instance.send_message(
            call.message.chat.id,
            text,
            parse_mode='Markdown'
        )
        
        # Временно показываем, что функция в разработке
        bot_instance.answer_callback_query(call.id, "🔜 Скоро будет доступно")
    
    elif data == "info":
        text = "ℹ️ *О гильдиях*\n\n"
        text += "Гильдии — сообщества игроков с общими целями.\n\n"
        text += "🏛️ *Зал гильдии* - центр управления\n"
        text += "📈 *Уровни гильдии* - до 5 уровня\n"
        text += "  ├ 1 ур: 10 членов, +2% опыта\n"
        text += "  ├ 2 ур: 20 членов, +4% золота\n"
        text += "  ├ 3 ур: 30 членов, +6% удачи\n"
        text += "  ├ 4 ур: 40 членов, +8% защиты\n"
        text += "  └ 5 ур: 50 членов, +10% урона\n\n"
        text += "🏗️ *Здания гильдии:*\n"
        text += "• Гильдейский зал (общий чат)\n"
        text += "• Гильдейский магазин\n"
        text += "• Гильдейская арена\n"
        text += "• Алтарь гильдии\n\n"
        text += "⚔️ *Гильдейские войны* - каждую субботу"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "hall":
        if not guild_id:
            bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
            return
        
        # Загружаем данные гильдии
        try:
            with open('data/guilds.json', 'r', encoding='utf-8') as f:
                guilds_data = json.load(f)
            guild = guilds_data.get("guilds", {}).get(str(guild_id), {})
        except:
            guild = {}
        
        text = f"🏛️ *Зал гильдии {guild.get('name', '')}*\n\n"
        text += f"📊 *Уровень:* {guild.get('level', 1)}\n"
        text += f"📈 *Опыт:* {guild.get('exp', 0)}/{guild.get('next_level_exp', 1000)}\n"
        text += f"👥 *Участников:* {len(guild.get('members', []))}/{guild.get('max_members', 10)}\n"
        text += f"💰 *Казна:* {guild.get('gold', 0)}💰 / {guild.get('dstn', 0)} DSTN\n\n"
        text += "🏗️ *Построено зданий:*\n"
        buildings = guild.get('buildings', [])
        text += f"• Зал гильдии: {'✅' if 'hall' in buildings else '❌'}\n"
        text += f"• Магазин: {'✅' if 'shop' in buildings else '❌'}\n"
        text += f"• Арена: {'✅' if 'arena' in buildings else '❌'}\n"
        text += f"• Алтарь: {'✅' if 'altar' in buildings else '❌'}\n\n"
        text += f"⚔️ *Побед в войнах:* {guild.get('wins', 0)}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "members":
        if not guild_id:
            bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
            return
        
        # Загружаем данные гильдии
        try:
            with open('data/guilds.json', 'r', encoding='utf-8') as f:
                guilds_data = json.load(f)
            guild = guilds_data.get("guilds", {}).get(str(guild_id), {})
        except:
            guild = {}
        
        members = guild.get('members', [])
        leader_id = guild.get('leader_id')
        
        text = f"📋 *Участники гильдии {guild.get('name', '')}*\n\n"
        
        for i, member_id in enumerate(members[:10]):  # Показываем первых 10
            prefix = "👑 " if member_id == leader_id else "  "
            text += f"{prefix}Участник #{i+1}\n"
        
        if len(members) > 10:
            text += f"...и ещё {len(members) - 10} участников"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "buildings":
        if not guild_id:
            bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
            return
        
        text = "🏗️ *Здания гильдии*\n\n"
        text += "• 🏛️ *Зал гильдии* (бесплатно)\n"
        text += "  Общий чат и банк\n\n"
        text += "• 🏪 *Магазин гильдии* (50 000💰)\n"
        text += "  Уникальные предметы для членов гильдии\n\n"
        text += "• ⚔️ *Арена гильдии* (100 000💰)\n"
        text += "  Тренировки и турниры между своими\n\n"
        text += "• 🔮 *Алтарь гильдии* (200 000💰)\n"
        text += "  Общие баффы и усиления"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "wars":
        if not guild_id:
            bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
            return
        
        text = "⚔️ *Гильдейские войны*\n\n"
        text += "Каждую субботу гильдии сражаются за славу!\n\n"
        text += "🏆 *Награды:*\n"
        text += "1 место: 10 000 DSTN в казну, +20% урона членам\n"
        text += "2 место: 5 000 DSTN в казну, +10% урона членам\n"
        text += "3 место: 2 000 DSTN в казну, +5% урона членам\n"
        text += "Участники: 200 DSTN + сундук\n\n"
        text += "📊 *Рейтинг гильдий:*\n"
        text += "1. Гильдия #1 - 10 побед\n"
        text += "2. Гильдия #2 - 8 побед\n"
        text += "3. Гильдия #3 - 5 побед"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "contributions":
        if not guild_id:
            bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
            return
        
        text = "📊 *Твой вклад в гильдию*\n\n"
        text += f"💰 Пожертвовано золота: {character.guild_contributed_gold or 0}\n"
        text += f"💎 Пожертвовано DSTN: {character.guild_contributed_dstn or 0}\n"
        text += f"⚔️ Участий в войнах: {character.guild_wars or 0}\n\n"
        text += "📈 *Твой рейтинг в гильдии:* {character.guild_rank or 'Рядовой'}\n\n"
        text += "Пожертвовать ресурсы можно через /guild donate"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "management":
        if not guild_id:
            bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
            return
        
        # Проверяем, является ли игрок лидером
        try:
            with open('data/guilds.json', 'r', encoding='utf-8') as f:
                guilds_data = json.load(f)
            guild = guilds_data.get("guilds", {}).get(str(guild_id), {})
            is_leader = guild.get('leader_id') == user_id
        except:
            is_leader = False
        
        text = "⚙️ *Управление гильдией*\n\n"
        
        if is_leader:
            text += "Ты лидер гильдии. Доступные действия:\n"
            text += "• 📢 Объявления\n"
            text += "• 👥 Принять/исключить\n"
            text += "• 👑 Передать лидерство\n"
            text += "• 🏗️ Строить здания\n"
            text += "• 💰 Управлять казной\n"
            text += "• ❌ Распустить гильдию"
        else:
            text += "Ты не лидер гильдии. Доступные действия:\n"
            text += "• 🚪 Покинуть гильдию"
        
        markup = InlineKeyboardMarkup()
        if is_leader:
            markup.add(
                InlineKeyboardButton("📢 Объявления", callback_data="guild:announce"),
                InlineKeyboardButton("👥 Участники", callback_data="guild:members_manage")
            )
            markup.add(
                InlineKeyboardButton("🏗️ Строить", callback_data="guild:build"),
                InlineKeyboardButton("💰 Казна", callback_data="guild:treasury")
            )
        else:
            markup.add(InlineKeyboardButton("🚪 Покинуть гильдию", callback_data="guild:leave"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "leave":
        if not guild_id:
            bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
            return
        
        text = "🚪 *Покинуть гильдию*\n\n"
        text += "Ты уверен, что хочешь покинуть гильдию?\n\n"
        text += "⚠️ Все твои вклады и достижения будут потеряны!"
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Да, покинуть", callback_data="guild:confirm_leave"),
            InlineKeyboardButton("❌ Нет, остаться", callback_data="guild:management")
        )
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "confirm_leave":
        if not guild_id:
            bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
            return
        
        # Удаляем игрока из гильдии
        character.guild_id = None
        save_character(character)
        
        bot_instance.answer_callback_query(call.id, "✅ Ты покинул гильдию")
        guild_command(call.message)
    
    elif data == "menu":
        guild_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
