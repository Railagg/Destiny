# /bot/handlers/guild.py
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import time
import random
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ ГИЛЬДИЙ
# ============================================

GUILD_LEVELS = {
    1: {"max_members": 10, "exp_needed": 1000, "bonuses": {"exp": 2, "gold": 0, "luck": 0, "defense": 0, "damage": 0}},
    2: {"max_members": 20, "exp_needed": 5000, "bonuses": {"exp": 4, "gold": 2, "luck": 0, "defense": 0, "damage": 0}},
    3: {"max_members": 30, "exp_needed": 15000, "bonuses": {"exp": 6, "gold": 4, "luck": 2, "defense": 0, "damage": 0}},
    4: {"max_members": 40, "exp_needed": 30000, "bonuses": {"exp": 8, "gold": 6, "luck": 4, "defense": 2, "damage": 0}},
    5: {"max_members": 50, "exp_needed": 50000, "bonuses": {"exp": 10, "gold": 8, "luck": 6, "defense": 4, "damage": 2}}
}

GUILD_BUILDINGS = {
    "hall": {
        "name": "🏛️ Зал гильдии",
        "price": 0,
        "description": "Общий чат и банк гильдии",
        "required_level": 1
    },
    "shop": {
        "name": "🏪 Гильдейский магазин",
        "price": 50000,
        "price_dstn": 500,
        "description": "Уникальные предметы для членов гильдии",
        "required_level": 2,
        "bonus": "Скидка 5% в магазине"
    },
    "arena": {
        "name": "⚔️ Гильдейская арена",
        "price": 100000,
        "price_dstn": 1000,
        "description": "Тренировки и турниры между своими",
        "required_level": 3,
        "bonus": "+5% к урону в PvP"
    },
    "altar": {
        "name": "🔮 Алтарь гильдии",
        "price": 200000,
        "price_dstn": 2000,
        "description": "Общие баффы и усиления",
        "required_level": 4,
        "bonus": "Ежедневное благословение"
    },
    "bank": {
        "name": "🏦 Гильдейский банк",
        "price": 150000,
        "price_dstn": 1500,
        "description": "Хранилище ресурсов и процентов",
        "required_level": 3,
        "bonus": "+1% к проценту в день"
    },
    "laboratory": {
        "name": "⚗️ Гильдейская лаборатория",
        "price": 250000,
        "price_dstn": 2500,
        "description": "Исследования и крафт",
        "required_level": 4,
        "bonus": "+10% к крафту"
    },
    "tower": {
        "name": "🗼 Гильдейская башня",
        "price": 500000,
        "price_dstn": 5000,
        "description": "Слежение за врагами и разведка",
        "required_level": 5,
        "bonus": "Видит врагов на карте"
    }
}

GUILD_RANKS = {
    "leader": "👑 Лидер",
    "officer": "⚔️ Офицер",
    "veteran": "🛡️ Ветеран",
    "member": "🔰 Рядовой",
    "recruit": "🌱 Рекрут"
}

# ============================================
# ОСНОВНАЯ КОМАНДА
# ============================================

def guild_command(message, bot_instance, get_or_create_player_func):
    """Команда /guild - гильдии"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Проверяем, состоит ли игрок в гильдии
    guild_id = character.guild_id if hasattr(character, 'guild_id') else None
    
    text = "🏛️ *ГИЛЬДИИ DESTINY*\n\n"
    
    if guild_id:
        # Загружаем данные гильдии
        guild = load_guild(guild_id)
        if guild:
            # Получаем ранг игрока
            rank = get_player_rank(guild, user_id)
            rank_name = GUILD_RANKS.get(rank, "🔰 Член гильдии")
            
            text += f"Ты в гильдии: *{guild.get('name', 'Неизвестно')}*\n"
            text += f"📊 Твой ранг: {rank_name}\n"
            text += f"📈 Уровень гильдии: {guild.get('level', 1)}\n"
            text += f"👥 Участников: {len(guild.get('members', []))}/{GUILD_LEVELS[guild.get('level', 1)]['max_members']}\n"
            text += f"📊 Опыт: {guild.get('exp', 0)}/{GUILD_LEVELS[guild.get('level', 1)]['exp_needed']}\n"
            text += f"💰 Казна: {guild.get('gold', 0):,}💰 / {guild.get('dstn', 0)} DSTN\n\n"
            
            # Активные бонусы
            bonuses = GUILD_LEVELS[guild.get('level', 1)]['bonuses']
            active_bonuses = []
            if bonuses['exp'] > 0:
                active_bonuses.append(f"+{bonuses['exp']}% опыта")
            if bonuses['gold'] > 0:
                active_bonuses.append(f"+{bonuses['gold']}% золота")
            if bonuses['luck'] > 0:
                active_bonuses.append(f"+{bonuses['luck']}% удачи")
            if bonuses['defense'] > 0:
                active_bonuses.append(f"+{bonuses['defense']}% защиты")
            if bonuses['damage'] > 0:
                active_bonuses.append(f"+{bonuses['damage']}% урона")
            
            if active_bonuses:
                text += f"✨ Бонусы гильдии: {', '.join(active_bonuses)}\n"
            
            # Следующая суббота для войн
            next_saturday = get_next_saturday()
            days_left = (next_saturday - datetime.now()).days
            text += f"⚔️ Следующая война: через {days_left} дней\n"
        else:
            text += "❌ Ошибка загрузки гильдии\n"
            character.guild_id = None
            save_character(character)
    else:
        text += "Ты не состоишь в гильдии.\n\n"
        text += "✨ *Преимущества гильдий:*\n"
        text += "• 👥 Общение с единомышленниками\n"
        text += "• 📈 Общие бонусы до +10%\n"
        text += "• ⚔️ Гильдейские войны (каждую субботу)\n"
        text += "• 🏪 Уникальный гильдейский магазин\n"
        text += "• 🏦 Общий банк и хранилище\n"
        text += "• 🏗️ Строительство зданий\n\n"
        text += "💰 Создать гильдию: 5000💰 или 500 DSTN"
    
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
            InlineKeyboardButton("📊 Мой вклад", callback_data="guild:contributions"),
            InlineKeyboardButton("⚙️ Управление", callback_data="guild:management")
        )
        markup.add(
            InlineKeyboardButton("💰 Пожертвовать", callback_data="guild:donate"),
            InlineKeyboardButton("🏪 Магазин", callback_data="guild:shop")
        )
    else:
        markup.add(
            InlineKeyboardButton("📋 Список гильдий", callback_data="guild:list"),
            InlineKeyboardButton("🏗️ Создать гильдию", callback_data="guild:create")
        )
        markup.add(
            InlineKeyboardButton("ℹ️ О гильдиях", callback_data="guild:info"),
            InlineKeyboardButton("📊 Рейтинг", callback_data="guild:ranking")
        )
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# ФУНКЦИИ ЗАГРУЗКИ/СОХРАНЕНИЯ
# ============================================

def load_guild(guild_id):
    """Загрузить данные гильдии"""
    try:
        with open('data/guilds.json', 'r', encoding='utf-8') as f:
            guilds_data = json.load(f)
        return guilds_data.get("guilds", {}).get(str(guild_id))
    except:
        return None

def save_guild(guild_id, guild_data):
    """Сохранить данные гильдии"""
    try:
        with open('data/guilds.json', 'r', encoding='utf-8') as f:
            guilds_data = json.load(f)
    except:
        guilds_data = {"guilds": {}}
    
    guilds_data["guilds"][str(guild_id)] = guild_data
    
    with open('data/guilds.json', 'w', encoding='utf-8') as f:
        json.dump(guilds_data, f, indent=2, ensure_ascii=False)

def get_player_rank(guild, user_id):
    """Получить ранг игрока в гильдии"""
    if guild.get('leader_id') == user_id:
        return "leader"
    
    for officer in guild.get('officers', []):
        if officer == user_id:
            return "officer"
    
    for veteran in guild.get('veterans', []):
        if veteran == user_id:
            return "veteran"
    
    return "member"

def get_next_saturday():
    """Получить следующую субботу"""
    today = datetime.now()
    days_ahead = 5 - today.weekday()  # 5 = суббота
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)

def save_character(character):
    """Сохранить персонажа"""
    from main import save_character as main_save
    main_save(character)

# ============================================
# ФУНКЦИИ ОБРАБОТКИ
# ============================================

def show_guild_list(call, bot_instance):
    """Показать список гильдий"""
    try:
        with open('data/guilds.json', 'r', encoding='utf-8') as f:
            guilds_data = json.load(f)
        guilds = guilds_data.get("guilds", {})
    except:
        guilds = {}
    
    text = "📋 *СПИСОК ГИЛЬДИЙ*\n\n"
    
    if not guilds:
        text += "Пока нет созданных гильдий.\n"
        text += "Стань первым, кто создаст гильдию!"
    else:
        # Сортируем по уровню и опыту
        sorted_guilds = sorted(
            guilds.items(), 
            key=lambda x: (x[1].get('level', 1), x[1].get('exp', 0)), 
            reverse=True
        )[:15]
        
        for i, (gid, guild) in enumerate(sorted_guilds, 1):
            level = guild.get('level', 1)
            members = len(guild.get('members', []))
            max_members = GUILD_LEVELS[level]['max_members']
            text += f"{i}. *{guild.get('name')}* (ур.{level})\n"
            text += f"   👥 {members}/{max_members} | 👑 {guild.get('leader_name', 'Неизвестно')}\n\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def create_guild(call, bot_instance, character, get_or_create_player_func):
    """Создание гильдии"""
    if character.guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты уже в гильдии!")
        return
    
    # Проверяем ресурсы
    if character.gold < 5000 and character.dstn < 500:
        bot_instance.answer_callback_query(call.id, "❌ Недостаточно ресурсов! Нужно 5000💰 или 500 DSTN")
        return
    
    text = "🏗️ *СОЗДАНИЕ ГИЛЬДИИ*\n\n"
    text += "Отправь название гильдии (от 3 до 20 символов).\n\n"
    text += "Требования:\n"
    text += "• Только буквы и цифры\n"
    text += "• Без пробелов\n"
    text += "• Уникальное название\n\n"
    text += "Пример: `Хранители` или `DarkSouls`\n\n"
    text += "Или нажми отмену."
    
    # Здесь нужно реализовать ожидание ответа
    # Пока показываем заглушку
    bot_instance.answer_callback_query(call.id, "🔜 Функция создания гильдии появится скоро")
    
    # Сохраняем состояние ожидания
    character.waiting_for = "guild_name"
    save_character(character)

def show_guild_info(call, bot_instance):
    """Показать информацию о гильдиях"""
    text = "ℹ️ *О ГИЛЬДИЯХ*\n\n"
    text += "Гильдии — сообщества игроков с общими целями.\n\n"
    
    text += "📈 *Уровни гильдии:*\n"
    for level, data in GUILD_LEVELS.items():
        bonuses = []
        if data['bonuses']['exp'] > 0:
            bonuses.append(f"+{data['bonuses']['exp']}% опыта")
        if data['bonuses']['gold'] > 0:
            bonuses.append(f"+{data['bonuses']['gold']}% золота")
        if data['bonuses']['luck'] > 0:
            bonuses.append(f"+{data['bonuses']['luck']}% удачи")
        
        text += f"• {level} ур: {data['max_members']} членов, {', '.join(bonuses)}\n"
    text += "\n"
    
    text += "🏗️ *Здания гильдии:*\n"
    for building_id, building in GUILD_BUILDINGS.items():
        text += f"• {building['name']} (треб. {building['required_level']} ур)\n"
        text += f"  {building['description']}\n"
        text += f"  Цена: {building['price']:,}💰 / {building.get('price_dstn', 0)} DSTN\n"
    text += "\n"
    
    text += "⚔️ *Гильдейские войны* - каждую субботу\n"
    text += "🏆 *Награды:* DSTN, бонусы, титулы"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_guild_ranking(call, bot_instance):
    """Показать рейтинг гильдий"""
    try:
        with open('data/guilds.json', 'r', encoding='utf-8') as f:
            guilds_data = json.load(f)
        guilds = guilds_data.get("guilds", {})
    except:
        guilds = {}
    
    text = "📊 *РЕЙТИНГ ГИЛЬДИЙ*\n\n"
    
    if not guilds:
        text += "Пока нет созданных гильдий."
    else:
        # По опыту
        text += "*🏆 По опыту:*\n"
        sorted_exp = sorted(guilds.items(), key=lambda x: x[1].get('exp', 0), reverse=True)[:5]
        for i, (gid, guild) in enumerate(sorted_exp, 1):
            text += f"{i}. *{guild.get('name')}* - {guild.get('exp', 0)} опыта\n"
        
        # По победам в войнах
        text += "\n*⚔️ По победам:*\n"
        sorted_wins = sorted(guilds.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:5]
        for i, (gid, guild) in enumerate(sorted_wins, 1):
            text += f"{i}. *{guild.get('name')}* - {guild.get('wins', 0)} побед\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_guild_hall(call, bot_instance, guild_id):
    """Показать зал гильдии"""
    if not guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
        return
    
    guild = load_guild(guild_id)
    if not guild:
        bot_instance.answer_callback_query(call.id, "❌ Гильдия не найдена")
        return
    
    buildings = guild.get('buildings', [])
    level = guild.get('level', 1)
    exp = guild.get('exp', 0)
    exp_needed = GUILD_LEVELS[level]['exp_needed']
    
    text = f"🏛️ *ЗАЛ ГИЛЬДИИ {guild.get('name', '')}*\n\n"
    
    text += f"📊 *Уровень:* {level}\n"
    text += f"📈 *Прогресс:* {exp}/{exp_needed} опыта\n"
    progress = int((exp / exp_needed) * 10)
    text += f"  {'█' * progress}{'░' * (10 - progress)}\n"
    
    text += f"👥 *Участников:* {len(guild.get('members', []))}/{GUILD_LEVELS[level]['max_members']}\n"
    text += f"💰 *Казна:* {guild.get('gold', 0):,}💰 / {guild.get('dstn', 0)} DSTN\n\n"
    
    text += "🏗️ *Построено зданий:*\n"
    for building_id, building in GUILD_BUILDINGS.items():
        status = "✅" if building_id in buildings else "❌"
        text += f"{status} {building['name']}"
        if building_id in buildings and building.get('bonus'):
            text += f" - {building['bonus']}"
        text += "\n"
    
    text += f"\n⚔️ *Побед в войнах:* {guild.get('wins', 0)}"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📢 Объявления", callback_data="guild:announcements"),
        InlineKeyboardButton("📊 Статистика", callback_data="guild:stats")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_guild_members(call, bot_instance, guild_id, user_id, get_or_create_player_func):
    """Показать участников гильдии"""
    if not guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
        return
    
    guild = load_guild(guild_id)
    if not guild:
        bot_instance.answer_callback_query(call.id, "❌ Гильдия не найдена")
        return
    
    members = guild.get('members', [])
    leader_id = guild.get('leader_id')
    officers = guild.get('officers', [])
    veterans = guild.get('veterans', [])
    
    text = f"📋 *УЧАСТНИКИ ГИЛЬДИИ {guild.get('name', '')}*\n\n"
    
    for i, member_id in enumerate(members):
        try:
            member_user, member_char = get_or_create_player_func(member_id)
            name = member_user.first_name or f"Игрок {member_id}"
            
            if member_id == leader_id:
                rank = "👑 Лидер"
            elif member_id in officers:
                rank = "⚔️ Офицер"
            elif member_id in veterans:
                rank = "🛡️ Ветеран"
            else:
                rank = "🔰 Рядовой"
            
            level = member_char.level if member_char else 1
            contribution = getattr(member_char, 'guild_contribution', 0)
            
            text += f"{rank} *{name}* (ур.{level})\n"
            text += f"  📊 Вклад: {contribution}\n\n"
        except:
            text += f"• Игрок #{i+1}\n"
    
    # Кнопки управления для лидера и офицеров
    markup = InlineKeyboardMarkup()
    if user_id == leader_id or user_id in officers:
        markup.add(InlineKeyboardButton("👥 Управление", callback_data="guild:manage_members"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_guild_buildings(call, bot_instance, guild_id, user_id):
    """Показать здания гильдии"""
    if not guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
        return
    
    guild = load_guild(guild_id)
    if not guild:
        bot_instance.answer_callback_query(call.id, "❌ Гильдия не найдена")
        return
    
    level = guild.get('level', 1)
    buildings = guild.get('buildings', [])
    gold = guild.get('gold', 0)
    dstn = guild.get('dstn', 0)
    
    text = "🏗️ *ЗДАНИЯ ГИЛЬДИИ*\n\n"
    
    for building_id, building in GUILD_BUILDINGS.items():
        status = "✅" if building_id in buildings else "⏳"
        can_build = level >= building['required_level'] and building_id not in buildings
        
        text += f"{status} *{building['name']}* (треб. {building['required_level']} ур)\n"
        text += f"  {building['description']}\n"
        
        if building.get('bonus'):
            text += f"  ✨ Бонус: {building['bonus']}\n"
        
        if building_id not in buildings:
            text += f"  💰 Цена: {building['price']:,}💰"
            if building.get('price_dstn'):
                text += f" / {building['price_dstn']} DSTN"
            text += "\n"
            
            if can_build:
                can_afford_gold = gold >= building['price']
                can_afford_dstn = dstn >= building.get('price_dstn', 0) if building.get('price_dstn') else True
                
                if can_afford_gold and can_afford_dstn:
                    text += "  ✅ Можно построить!\n"
        
        text += "\n"
    
    # Кнопка строительства для лидера
    markup = InlineKeyboardMarkup()
    if user_id == guild.get('leader_id'):
        markup.add(InlineKeyboardButton("🏗️ Построить", callback_data="guild:construct"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_guild_wars(call, bot_instance, guild_id):
    """Показать информацию о гильдейских войнах"""
    text = "⚔️ *ГИЛЬДЕЙСКИЕ ВОЙНЫ*\n\n"
    
    # Информация о следующей войне
    next_saturday = get_next_saturday()
    days_left = (next_saturday - datetime.now()).days
    hours_left = ((next_saturday - datetime.now()).seconds // 3600)
    
    text += f"📅 *Следующая война:* через {days_left}д {hours_left}ч\n\n"
    
    text += "🏆 *Награды:*\n"
    text += "🥇 1 место: 10 000 DSTN в казну, +20% урона членам (7 дней)\n"
    text += "🥈 2 место: 5 000 DSTN в казну, +10% урона членам (7 дней)\n"
    text += "🥉 3 место: 2 000 DSTN в казну, +5% урона членам (7 дней)\n"
    text += "🎁 Участники: 200 DSTN + сундук\n\n"
    
    # Топ гильдий
    try:
        with open('data/guilds.json', 'r', encoding='utf-8') as f:
            guilds_data = json.load(f)
        guilds = guilds_data.get("guilds", {})
        
        text += "📊 *ТОП ГИЛЬДИЙ ПО ПОБЕДАМ:*\n"
        sorted_wins = sorted(guilds.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:5]
        for i, (gid, guild) in enumerate(sorted_wins, 1):
            text += f"{i}. *{guild.get('name')}* - {guild.get('wins', 0)} побед\n"
    except:
        pass
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_player_contributions(call, bot_instance, character, guild_id):
    """Показать вклад игрока"""
    if not guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
        return
    
    text = "📊 *ТВОЙ ВКЛАД В ГИЛЬДИЮ*\n\n"
    text += f"💰 Пожертвовано золота: {getattr(character, 'guild_donated_gold', 0):,}\n"
    text += f"💎 Пожертвовано DSTN: {getattr(character, 'guild_donated_dstn', 0)}\n"
    text += f"⚔️ Участий в войнах: {getattr(character, 'guild_wars', 0)}\n"
    text += f"🗓️ Дней в гильдии: {get_guild_days(character, guild_id)}\n\n"
    
    # Рейтинг в гильдии
    rank = getattr(character, 'guild_rank', 'member')
    rank_name = GUILD_RANKS.get(rank, "🔰 Рядовой")
    text += f"📈 *Твой ранг:* {rank_name}\n"
    
    # Следующее повышение
    contribution = getattr(character, 'guild_contribution', 0)
    if rank == "member" and contribution > 1000:
        text += f"🎯 До повышения: {1000 - contribution} вклада\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💰 Пожертвовать", callback_data="guild:donate"),
        InlineKeyboardButton("🔙 Назад", callback_data="guild:menu")
    )
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def get_guild_days(character, guild_id):
    """Получить количество дней в гильдии"""
    join_time = getattr(character, 'guild_join_time', 0)
    if join_time:
        return (time.time() - join_time) // 86400
    return 0

def show_guild_management(call, bot_instance, guild_id, user_id):
    """Показать меню управления гильдией"""
    if not guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
        return
    
    guild = load_guild(guild_id)
    if not guild:
        bot_instance.answer_callback_query(call.id, "❌ Гильдия не найдена")
        return
    
    is_leader = guild.get('leader_id') == user_id
    is_officer = user_id in guild.get('officers', [])
    
    text = "⚙️ *УПРАВЛЕНИЕ ГИЛЬДИЕЙ*\n\n"
    
    if is_leader:
        text += "👑 Ты лидер гильдии. Доступные действия:\n\n"
        text += "• 📢 Сделать объявление\n"
        text += "• 👥 Принять/отклонить заявки\n"
        text += "• 👑 Назначить/снять офицеров\n"
        text += "• 🏗️ Строить здания\n"
        text += "• 💰 Управлять казной\n"
        text += "• ❌ Распустить гильдию\n"
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📢 Объявление", callback_data="guild:announce"),
            InlineKeyboardButton("👥 Заявки", callback_data="guild:applications")
        )
        markup.add(
            InlineKeyboardButton("👑 Офицеры", callback_data="guild:manage_officers"),
            InlineKeyboardButton("🏗️ Строить", callback_data="guild:construct")
        )
        markup.add(
            InlineKeyboardButton("💰 Казна", callback_data="guild:treasury"),
            InlineKeyboardButton("❌ Распустить", callback_data="guild:disband")
        )
    
    elif is_officer:
        text += "⚔️ Ты офицер гильдии. Доступные действия:\n\n"
        text += "• 📢 Сделать объявление\n"
        text += "• 👥 Принять/отклонить заявки\n"
        text += "• 🚪 Исключить рядовых\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📢 Объявление", callback_data="guild:announce"),
            InlineKeyboardButton("👥 Заявки", callback_data="guild:applications")
        )
        markup.add(InlineKeyboardButton("🚪 Исключить", callback_data="guild:kick_menu"))
    
    else:
        text += "🔰 Ты рядовой член гильдии. Доступные действия:\n\n"
        text += "• 🚪 Покинуть гильдию\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚪 Покинуть", callback_data="guild:leave"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_donate_menu(call, bot_instance, character, guild_id):
    """Показать меню пожертвований"""
    if not guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
        return
    
    text = "💰 *ПОЖЕРТВОВАНИЯ ГИЛЬДИИ*\n\n"
    text += "Пожертвования идут на:\n"
    text += "• Развитие гильдии (опыт)\n"
    text += "• Строительство зданий\n"
    text += "• Казна для войн\n\n"
    
    text += f"📊 Твой баланс:\n"
    text += f"💰 Золото: {character.gold:,}\n"
    text += f"💎 DSTN: {character.dstn or 0}\n\n"
    
    text += "Выбери сумму для пожертвования:\n"
    
    markup = InlineKeyboardMarkup(row_width=3)
    
    # Золото
    gold_amounts = [1000, 5000, 10000, 50000]
    for amount in gold_amounts:
        if character.gold >= amount:
            markup.add(InlineKeyboardButton(
                f"{amount}💰",
                callback_data=f"guild:donate_gold:{amount}"
            ))
    
    # DSTN
    dstn_amounts = [100, 500, 1000]
    for amount in dstn_amounts:
        if character.dstn >= amount:
            markup.add(InlineKeyboardButton(
                f"{amount}💎",
                callback_data=f"guild:donate_dstn:{amount}"
            ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_guild_shop(call, bot_instance, guild_id, user_id):
    """Показать гильдейский магазин"""
    if not guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
        return
    
    guild = load_guild(guild_id)
    if not guild:
        bot_instance.answer_callback_query(call.id, "❌ Гильдия не найдена")
        return
    
    buildings = guild.get('buildings', [])
    
    if "shop" not in buildings:
        bot_instance.answer_callback_query(call.id, "❌ Гильдейский магазин не построен!")
        return
    
    text = "🏪 *ГИЛЬДЕЙСКИЙ МАГАЗИН*\n\n"
    text += "Уникальные предметы для членов гильдии:\n\n"
    
    # Товары гильдейского магазина
    items = [
        {"name": "📜 Свиток телепортации (5 шт)", "price_gold": 5000, "price_dstn": 50},
        {"name": "🔮 Магический кристалл (3 шт)", "price_gold": 10000, "price_dstn": 100},
        {"name": "🐉 Чешуя дракона", "price_gold": 25000, "price_dstn": 250},
        {"name": "🔥 Перо феникса", "price_gold": 50000, "price_dstn": 500},
        {"name": "💎 Радужный осколок", "price_gold": 100000, "price_dstn": 1000},
        {"name": "👑 Гильдейский плащ", "price_gold": 200000, "price_dstn": 2000, "special": True}
    ]
    
    for item in items:
        text += f"• *{item['name']}*\n"
        text += f"  💰 {item['price_gold']:,} | 💎 {item['price_dstn']}\n"
    
    text += "\n💰 5% скидка для членов гильдии!"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def confirm_leave_guild(call, bot_instance, character, guild_id):
    """Подтверждение выхода из гильдии"""
    if not guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
        return
    
    text = "🚪 *ПОКИНУТЬ ГИЛЬДИЮ*\n\n"
    text += "Ты уверен, что хочешь покинуть гильдию?\n\n"
    text += "⚠️ *Последствия:*\n"
    text += "• Потеря всех гильдейских бонусов\n"
    text += "• Вклад в гильдию обнулится\n"
    text += "• Невозможно будет вернуться 24ч\n\n"
    text += "Ты сможешь вступить в другую гильдию через 24ч."
    
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

def leave_guild(call, bot_instance, character, guild_id, get_or_create_player_func):
    """Выход из гильдии"""
    from main import save_character
    
    if not guild_id:
        bot_instance.answer_callback_query(call.id, "❌ Ты не в гильдии!")
        return
    
    guild = load_guild(guild_id)
    if not guild:
        bot_instance.answer_callback_query(call.id, "❌ Гильдия не найдена")
        return
    
    # Проверяем, не лидер ли
    if guild.get('leader_id') == character.user_id:
        bot_instance.answer_callback_query(call.id, "❌ Лидер не может покинуть гильдию! Передай лидерство или распусти гильдию.")
        return
    
    # Удаляем из гильдии
    members = guild.get('members', [])
    if character.user_id in members:
        members.remove(character.user_id)
        guild['members'] = members
    
    # Удаляем из офицеров если был
    if character.user_id in guild.get('officers', []):
        guild['officers'].remove(character.user_id)
    
    # Удаляем из ветеранов если был
    if character.user_id in guild.get('veterans', []):
        guild['veterans'].remove(character.user_id)
    
    save_guild(guild_id, guild)
    
    # Обновляем персонажа
    character.guild_id = None
    character.guild_leave_time = int(time.time())
    save_character(character)
    
    bot_instance.answer_callback_query(call.id, "✅ Ты покинул гильдию")
    guild_command(call.message, bot_instance, get_or_create_player_func)

def donate_gold(call, bot_instance, character, guild_id, amount):
    """Пожертвовать золото"""
    from main import save_character
    
    if character.gold < amount:
        bot_instance.answer_callback_query(call.id, f"❌ Недостаточно золота!")
        return
    
    guild = load_guild(guild_id)
    if not guild:
        bot_instance.answer_callback_query(call.id, "❌ Гильдия не найдена")
        return
    
    # Тратим золото
    character.gold -= amount
    character.guild_donated_gold = getattr(character, 'guild_donated_gold', 0) + amount
    character.guild_contribution = getattr(character, 'guild_contribution', 0) + amount // 100
    
    # Добавляем в казну
    guild['gold'] = guild.get('gold', 0) + amount
    
    # Добавляем опыт гильдии
    exp_gain = amount // 100
    guild['exp'] = guild.get('exp', 0) + exp_gain
    
    # Проверка на повышение уровня
    level_up_guild(guild)
    
    save_guild(guild_id, guild)
    save_character(character)
    
    bot_instance.answer_callback_query(call.id, f"✅ Пожертвовано {amount}💰! +{exp_gain} опыта гильдии")
    show_donate_menu(call, bot_instance, character, guild_id)

def donate_dstn(call, bot_instance, character, guild_id, amount):
    """Пожертвовать DSTN"""
    from main import save_character
    
    if character.dstn < amount:
        bot_instance.answer_callback_query(call.id, f"❌ Недостаточно DSTN!")
        return
    
    guild = load_guild(guild_id)
    if not guild:
        bot_instance.answer_callback_query(call.id, "❌ Гильдия не найдена")
        return
    
    # Тратим DSTN
    character.dstn -= amount
    character.guild_donated_dstn = getattr(character, 'guild_donated_dstn', 0) + amount
    character.guild_contribution = getattr(character, 'guild_contribution', 0) + amount * 2
    
    # Добавляем в казну
    guild['dstn'] = guild.get('dstn', 0) + amount
    
    # Добавляем опыт гильдии
    exp_gain = amount * 2
    guild['exp'] = guild.get('exp', 0) + exp_gain
    
    # Проверка на повышение уровня
    level_up_guild(guild)
    
    save_guild(guild_id, guild)
    save_character(character)
    
    bot_instance.answer_callback_query(call.id, f"✅ Пожертвовано {amount}💎! +{exp_gain} опыта гильдии")
    show_donate_menu(call, bot_instance, character, guild_id)

def level_up_guild(guild):
    """Повысить уровень гильдии если хватает опыта"""
    current_level = guild.get('level', 1)
    exp = guild.get('exp', 0)
    
    while current_level < 5 and exp >= GUILD_LEVELS[current_level]['exp_needed']:
        exp -= GUILD_LEVELS[current_level]['exp_needed']
        current_level += 1
        
        # Увеличиваем максимальное количество членов
        guild['max_members'] = GUILD_LEVELS[current_level]['max_members']
    
    guild['level'] = current_level
    guild['exp'] = exp

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func):
    """Обработка кнопок гильдий"""
    from main import save_character
    
    parts = call.data.split(':')
    action = parts[1] if len(parts) > 1 else "menu"
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    guild_id = character.guild_id if hasattr(character, 'guild_id') else None
    
    if action == "menu":
        guild_command(call.message, bot_instance, get_or_create_player_func)
    
    elif action == "list":
        show_guild_list(call, bot_instance)
    
    elif action == "create":
        create_guild(call, bot_instance, character, get_or_create_player_func)
    
    elif action == "info":
        show_guild_info(call, bot_instance)
    
    elif action == "ranking":
        show_guild_ranking(call, bot_instance)
    
    elif action == "hall":
        show_guild_hall(call, bot_instance, guild_id)
    
    elif action == "members":
        show_guild_members(call, bot_instance, guild_id, user_id, get_or_create_player_func)
    
    elif action == "buildings":
        show_guild_buildings(call, bot_instance, guild_id, user_id)
    
    elif action == "wars":
        show_guild_wars(call, bot_instance, guild_id)
    
    elif action == "contributions":
        show_player_contributions(call, bot_instance, character, guild_id)
    
    elif action == "management":
        show_guild_management(call, bot_instance, guild_id, user_id)
    
    elif action == "donate":
        show_donate_menu(call, bot_instance, character, guild_id)
    
    elif action == "shop":
        show_guild_shop(call, bot_instance, guild_id, user_id)
    
    elif action == "leave":
        confirm_leave_guild(call, bot_instance, character, guild_id)
    
    elif action == "confirm_leave":
        leave_guild(call, bot_instance, character, guild_id, get_or_create_player_func)
    
    elif action == "donate_gold" and len(parts) > 2:
        amount = int(parts[2])
        donate_gold(call, bot_instance, character, guild_id, amount)
    
    elif action == "donate_dstn" and len(parts) > 2:
        amount = int(parts[2])
        donate_dstn(call, bot_instance, character, guild_id, amount)
    
    # Заглушки для функций, которые ещё не реализованы
    elif action in ["announcements", "stats", "manage_members", "announce", 
                    "applications", "manage_officers", "construct", "treasury", 
                    "disband", "kick_menu"]:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")

# ============================================
# ФУНКЦИИ ДЛЯ СОВМЕСТИМОСТИ С __init__.py
# ============================================

def guild_create_command(message, bot_instance, get_or_create_player_func):
    """Команда /guild_create - создать гильдию"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if character.guild_id:
        bot_instance.send_message(
            message.chat.id,
            "❌ Ты уже состоишь в гильдии!",
            parse_mode='Markdown'
        )
        return
    
    text = "✨ *СОЗДАНИЕ ГИЛЬДИИ*\n\n"
    text += "Для создания гильдии нужно:\n"
    text += "• Уровень 20+\n"
    text += "• 10,000 золота\n"
    text += "• 500 DSTN\n\n"
    
    if character.level < 20:
        text += f"❌ Твой уровень: {character.level}/20\n"
    else:
        text += f"✅ Твой уровень: {character.level}/20\n"
    
    if character.gold < 10000:
        text += f"❌ Золото: {character.gold}/10000\n"
    else:
        text += f"✅ Золото: {character.gold}/10000\n"
    
    if character.destiny_tokens < 500:
        text += f"❌ DSTN: {character.destiny_tokens}/500\n"
    else:
        text += f"✅ DSTN: {character.destiny_tokens}/500\n"
    
    can_create = character.level >= 20 and character.gold >= 10000 and character.destiny_tokens >= 500
    
    markup = InlineKeyboardMarkup()
    if can_create:
        markup.add(InlineKeyboardButton("✅ Создать гильдию", callback_data="guild:create_confirm"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="guild:menu"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def guild_info_command(message, bot_instance, get_or_create_player_func):
    """Команда /guild_info - информация о текущей гильдии"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if not character.guild_id:
        bot_instance.send_message(
            message.chat.id,
            "❌ Ты не состоишь в гильдии!",
            parse_mode='Markdown'
        )
        return
    
    # Показываем информацию о гильдии
    guild_command(message, bot_instance, get_or_create_player_func)

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'guild_command',
    'guild_create_command',
    'guild_info_command',
    'handle_callback'
]
