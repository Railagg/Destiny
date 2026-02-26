import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ NFT
# ============================================

NFT_SHARDS = {
    "red": {
        "name": "🔴 Осколок огня",
        "emoji": "🔴",
        "color": "red",
        "element": "🔥 Огонь",
        "total_supply": 10,
        "price_stars": 500,
        "price_ton": 9,
        "price_dstn": 25000,
        "description": "Осколок, хранящий силу первозданного огня. Даёт власть над пламенем.",
        "bonuses": [
            "🔥 +15% к огненному урону",
            "🛡️ +10% к защите от огня",
            "⚡ Шанс поджечь врага: 10%"
        ],
        "ability": {
            "name": "🔥 Огненный взрыв",
            "description": "Наносит 200% огненного урона всем врагам",
            "cooldown": "24 часа"
        },
        "house_item": "🪔 Огненный алтарь"
    },
    "blue": {
        "name": "🔵 Осколок льда",
        "emoji": "🔵",
        "color": "blue",
        "element": "❄️ Лёд",
        "total_supply": 10,
        "price_stars": 500,
        "price_ton": 9,
        "price_dstn": 25000,
        "description": "Осколок вечной мерзлоты, хранящий холод северных земель.",
        "bonuses": [
            "❄️ +15% к ледяному урону",
            "🛡️ +10% к защите от холода",
            "⏸️ Шанс заморозить врага: 10%"
        ],
        "ability": {
            "name": "❄️ Ледяная глыба",
            "description": "Замораживает всех врагов на 2 хода",
            "cooldown": "24 часа"
        },
        "house_item": "🧊 Ледяной алтарь"
    },
    "green": {
        "name": "🟢 Осколок природы",
        "emoji": "🟢",
        "color": "green",
        "element": "🌿 Природа",
        "total_supply": 10,
        "price_stars": 500,
        "price_ton": 9,
        "price_dstn": 25000,
        "description": "Осколок, наполненный жизненной силой лесов и полей.",
        "bonuses": [
            "💚 +20% к силе лечения",
            "🌱 +15% к сбору трав",
            "🔄 Шанс восстановить здоровье: 10%"
        ],
        "ability": {
            "name": "🌿 Благословение природы",
            "description": "Восстанавливает 50% здоровья всей группе",
            "cooldown": "24 часа"
        },
        "house_item": "🌱 Алтарь природы"
    },
    "yellow": {
        "name": "🟡 Осколок молнии",
        "emoji": "🟡",
        "color": "yellow",
        "element": "⚡ Молния",
        "total_supply": 10,
        "price_stars": 500,
        "price_ton": 9,
        "price_dstn": 25000,
        "description": "Осколок, искрящийся энергией грозовых туч.",
        "bonuses": [
            "⚡ +20% к скорости атаки",
            "🎯 +15% к шансу крита",
            "💨 +10% к уклонению"
        ],
        "ability": {
            "name": "⚡ Цепная молния",
            "description": "Атакует всех врагов с 150% урона",
            "cooldown": "24 часа"
        },
        "house_item": "⚡ Алтарь молний"
    },
    "purple": {
        "name": "🟣 Осколок тьмы",
        "emoji": "🟣",
        "color": "purple",
        "element": "🌑 Тьма",
        "total_supply": 10,
        "price_stars": 500,
        "price_ton": 9,
        "price_dstn": 25000,
        "description": "Осколок, впитавший силу теней и ночи.",
        "bonuses": [
            "🌑 +15% к урону тьмой",
            "👻 +15% к вампиризму",
            "😈 Шанс наложить страх: 10%"
        ],
        "ability": {
            "name": "🌑 Объятия тьмы",
            "description": "Накладывает немоту и страх на всех врагов",
            "cooldown": "24 часа"
        },
        "house_item": "🌑 Алтарь тьмы"
    }
}

SET_BONUSES = {
    "2": {
        "name": "⚡ Пробуждение",
        "bonus": "+2% ко всем характеристикам"
    },
    "3": {
        "name": "🔥 Сочетание",
        "bonus": "+3% ко всем характеристикам"
    },
    "4": {
        "name": "✨ Гармония",
        "bonus": "+4% ко всем характеристикам, +2% к шансу крита"
    },
    "5": {
        "name": "🌟 Абсолют",
        "bonus": "+5% ко всем характеристикам, радужный ник, аура"
    }
}

# ============================================
# ОСНОВНАЯ КОМАНДА
# ============================================

def nft_command(message, bot_instance, get_or_create_player_func, nft_data):
    """Команда /nft - NFT осколки"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    # Получаем коллекцию игрока
    collection = character.nft_collection if hasattr(character, 'nft_collection') else []
    collection_count = len(collection)
    
    text = "💎 *NFT-ОСКОЛКИ СТИХИЙ*\n\n"
    text += "Уникальные NFT на блокчейне TON, выпущенные ограниченным тиражом.\n"
    text += "Каждый осколок даёт постоянные бонусы и уникальную способность.\n\n"
    
    text += f"📊 *Твоя коллекция:* {collection_count}/5 осколков\n"
    
    if collection_count in SET_BONUSES:
        set_bonus = SET_BONUSES[str(collection_count)]
        text += f"🎯 *Активный сет:* {set_bonus['name']} — {set_bonus['bonus']}\n"
    text += "\n"
    
    for shard_id, shard in NFT_SHARDS.items():
        owned = shard_id in collection
        status = "✅" if owned else "⏳"
        
        text += f"{status} {shard['name']}\n"
        text += f"├ {shard['element']}\n"
        text += f"├ Цена: {shard['price_stars']}⭐ / {shard['price_ton']} TON\n"
        text += f"└ Осталось: {shard['total_supply'] - collection.count(shard_id)}/{shard['total_supply']}\n\n"
    
    text += "🏆 *Сетовые бонусы:*\n"
    text += "2 осколка: +2% ко всем характеристикам\n"
    text += "3 осколка: +3% ко всем характеристикам\n"
    text += "4 осколка: +4% ко всем характеристикам, +2% крит\n"
    text += "5 осколков: +5% + радужный ник + аура"
    
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("🔴 Красный", callback_data="nft:red"),
        InlineKeyboardButton("🔵 Синий", callback_data="nft:blue"),
        InlineKeyboardButton("🟢 Зелёный", callback_data="nft:green")
    )
    markup.add(
        InlineKeyboardButton("🟡 Жёлтый", callback_data="nft:yellow"),
        InlineKeyboardButton("🟣 Фиолетовый", callback_data="nft:purple")
    )
    markup.add(
        InlineKeyboardButton("ℹ️ О NFT", callback_data="nft:info"),
        InlineKeyboardButton("🏆 Моя коллекция", callback_data="nft:collection")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_shard_detail(call, bot_instance, character, shard_id):
    """Показать детали осколка"""
    shard = NFT_SHARDS.get(shard_id)
    
    if not shard:
        bot_instance.answer_callback_query(call.id, "❌ Осколок не найден")
        return
    
    collection = character.nft_collection if hasattr(character, 'nft_collection') else []
    owned = shard_id in collection
    
    text = f"{shard['name']}\n\n"
    text += f"{shard['description']}\n\n"
    text += f"✨ *Элемент:* {shard['element']}\n\n"
    
    text += "📊 *Бонусы:*\n"
    for bonus in shard['bonuses']:
        text += f"• {bonus}\n"
    
    text += f"\n⚡ *Способность:*\n"
    text += f"• {shard['ability']['name']}: {shard['ability']['description']}\n"
    text += f"• ⏱️ Перезарядка: {shard['ability']['cooldown']}\n\n"
    
    text += f"🏠 *Предмет для дома:* {shard['house_item']}\n\n"
    
    text += f"📊 *Тираж:* {shard['total_supply']} шт\n"
    text += f"💰 *Цена:* {shard['price_stars']}⭐ / {shard['price_ton']} TON / {shard['price_dstn']} DSTN\n"
    
    if owned:
        text += f"\n✅ *У тебя уже есть этот осколок!*"
    
    markup = InlineKeyboardMarkup()
    
    if not owned:
        # Кнопки покупки
        markup.row(
            InlineKeyboardButton(f"{shard['price_stars']}⭐ Stars", callback_data=f"nft:buy_stars:{shard_id}"),
            InlineKeyboardButton(f"{shard['price_ton']} TON", callback_data=f"nft:buy_ton:{shard_id}")
        )
        markup.add(InlineKeyboardButton(f"{shard['price_dstn']}💎 DSTN", callback_data=f"nft:buy_dstn:{shard_id}"))
    else:
        # Информация о владении
        markup.add(InlineKeyboardButton("✅ В коллекции", callback_data="nft:noop"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="nft:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_collection(call, bot_instance, character):
    """Показать коллекцию игрока"""
    collection = character.nft_collection if hasattr(character, 'nft_collection') else []
    collection_count = len(collection)
    
    text = "🏆 *Твоя NFT коллекция*\n\n"
    
    if not collection:
        text += "У тебя пока нет NFT осколков.\n\n"
        text += "Купи осколки, чтобы получить:\n"
        text += "• Постоянные бонусы к характеристикам\n"
        text += "• Уникальные способности\n"
        text += "• Сетовые бонусы\n"
        text += "• Особый цвет ника\n"
        text += "• Ауру вокруг персонажа"
    else:
        for shard_id in collection:
            if shard_id in NFT_SHARDS:
                shard = NFT_SHARDS[shard_id]
                text += f"• {shard['name']}\n"
        
        text += f"\n📊 *Всего осколков:* {collection_count}/5\n"
        
        if collection_count in SET_BONUSES:
            set_bonus = SET_BONUSES[str(collection_count)]
            text += f"\n🎯 *Активный сетовый бонус:*\n"
            text += f"{set_bonus['name']}: {set_bonus['bonus']}"
            
            # Применяем бонусы к персонажу
            apply_set_bonuses(character, collection_count)
        
        # Применяем индивидуальные бонусы
        apply_nft_bonuses(character, collection)
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="nft:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_info(call, bot_instance):
    """Показать информацию о NFT"""
    text = "ℹ️ *О NFT ОСКОЛКАХ*\n\n"
    text += "NFT осколки — уникальные цифровые предметы на блокчейне TON.\n\n"
    
    text += "✨ *Что дают:*\n"
    text += "• 📊 Постоянные бонусы к характеристикам\n"
    text += "• ⚡ Уникальные способности (активируются в бою)\n"
    text += "• 🏠 Эксклюзивные предметы для дома\n"
    text += "• 🎨 Особый цвет ника\n"
    text += "• ✨ Ауру вокруг персонажа\n"
    text += "• 🖼️ Рамку для аватарки\n\n"
    
    text += "🎯 *Сетовые бонусы:*\n"
    text += "• 2 осколка: +2% ко всем характеристикам\n"
    text += "• 3 осколка: +3% ко всем характеристикам\n"
    text += "• 4 осколка: +4% ко всем характеристикам, +2% крит\n"
    text += "• 5 осколков: +5% ко всем, радужный ник, аура\n\n"
    
    text += "📊 *Всего выпущено:* 50 NFT (по 10 каждого цвета)\n"
    text += "💎 *Купить можно за Stars, TON или DSTN\n"
    text += "🔗 После покупки осколок привязывается к аккаунту"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="nft:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def buy_nft(call, bot_instance, character, shard_id, currency):
    """Купить NFT осколок"""
    from main import save_character
    
    shard = NFT_SHARDS.get(shard_id)
    
    if not shard:
        bot_instance.answer_callback_query(call.id, "❌ Осколок не найден")
        return
    
    collection = character.nft_collection if hasattr(character, 'nft_collection') else []
    
    if shard_id in collection:
        bot_instance.answer_callback_query(call.id, "❌ Осколок уже есть в коллекции")
        return
    
    # Проверяем цену
    if currency == "stars":
        price = shard['price_stars']
        # Здесь должна быть интеграция со Stars
        bot_instance.answer_callback_query(call.id, "🔜 Покупка за Stars появится скоро")
        return
    
    elif currency == "ton":
        price = shard['price_ton']
        # Интеграция с TON Connect
        bot_instance.answer_callback_query(call.id, "🔜 Покупка за TON появится скоро")
        return
    
    elif currency == "dstn":
        price = shard['price_dstn']
        
        if character.dstn < price:
            bot_instance.answer_callback_query(call.id, f"❌ Нужно {price} DSTN")
            return
        
        # Покупаем за DSTN
        character.dstn -= price
        
        # Добавляем в коллекцию
        if not hasattr(character, 'nft_collection'):
            character.nft_collection = []
        character.nft_collection.append(shard_id)
        
        # Добавляем предмет для дома
        if shard.get('house_item'):
            character.add_item(f"nft_altar_{shard_id}")
        
        save_character(character)
        
        bot_instance.answer_callback_query(call.id, f"✅ {shard['name']} куплен!")
        
        # Показываем обновлённую коллекцию
        show_collection(call, bot_instance, character)
    
    else:
        bot_instance.answer_callback_query(call.id, "❌ Неизвестная валюта")

def apply_nft_bonuses(character, collection):
    """Применить бонусы от NFT осколков"""
    from main import save_character
    
    if not collection:
        return
    
    # Сбрасываем временные бонусы
    character.fire_damage_bonus = 0
    character.ice_damage_bonus = 0
    character.heal_power_bonus = 0
    character.speed_bonus = 0
    character.shadow_damage_bonus = 0
    
    for shard_id in collection:
        if shard_id == "red":
            character.fire_damage_bonus = 15
            character.fire_resist_bonus = 10
        elif shard_id == "blue":
            character.ice_damage_bonus = 15
            character.cold_resist_bonus = 10
        elif shard_id == "green":
            character.heal_power_bonus = 20
            character.herb_gathering_bonus = 15
        elif shard_id == "yellow":
            character.speed_bonus = 20
            character.crit_chance_bonus = 15
            character.dodge_bonus = 10
        elif shard_id == "purple":
            character.shadow_damage_bonus = 15
            character.life_steal_bonus = 15
    
    save_character(character)

def apply_set_bonuses(character, count):
    """Применить сетовые бонусы"""
    if count >= 2:
        character.all_stats_bonus = 2
    if count >= 3:
        character.all_stats_bonus = 3
    if count >= 4:
        character.all_stats_bonus = 4
        character.crit_chance_bonus = (character.crit_chance_bonus or 0) + 2
    if count >= 5:
        character.all_stats_bonus = 5
        character.rainbow_nick = True
        character.rainbow_aura = True

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func, nft_data):
    """Обработка кнопок NFT"""
    from main import save_character
    
    parts = call.data.split(':')
    action = parts[1] if len(parts) > 1 else "menu"
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if action == "menu":
        nft_command(call.message, bot_instance, get_or_create_player_func, nft_data)
    
    elif action in NFT_SHARDS:
        show_shard_detail(call, bot_instance, character, action)
    
    elif action == "collection":
        show_collection(call, bot_instance, character)
    
    elif action == "info":
        show_info(call, bot_instance)
    
    elif action.startswith("buy_"):
        parts = action.split('_')
        currency = parts[1]
        shard_id = parts[2]
        buy_nft(call, bot_instance, character, shard_id, currency)
    
    elif action == "noop":
        bot_instance.answer_callback_query(call.id)
    
    else:
        # ============================================
# ФУНКЦИИ ДЛЯ СОВМЕСТИМОСТИ С __init__.py
# ============================================

def nft_list_command(message, bot_instance, get_or_create_player_func, nft_data):
    """Команда /nft_list - список доступных NFT"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "📋 *ДОСТУПНЫЕ NFT ОСКОЛКИ*\n\n"
    
    for shard_id, shard in NFT_SHARDS.items():
        text += f"{shard['name']}\n"
        text += f"├ {shard['element']}\n"
        text += f"├ Цена: {shard['price_stars']}⭐ / {shard['price_ton']} TON / {shard['price_dstn']} DSTN\n"
        text += f"└ Осталось: {shard['total_supply']}/10\n\n"
    
    text += "\nПодробнее о каждом: /nft"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="nft:menu"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def nft_owned_command(message, bot_instance, get_or_create_player_func, nft_data):
    """Команда /nft_owned - мои NFT"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    collection = character.nft_collection if hasattr(character, 'nft_collection') else []
    
    if not collection:
        text = "📦 *У тебя пока нет NFT осколков*\n\n"
        text += "Купи осколки в магазине: /nft"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="nft:menu"))
        
        bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')
        return
    
    text = f"📦 *ТВОИ NFT ОСКОЛКИ* ({len(collection)}/5)\n\n"
    
    for shard_id in collection:
        if shard_id in NFT_SHARDS:
            shard = NFT_SHARDS[shard_id]
            text += f"• {shard['name']}\n"
            text += f"  ├ {shard['element']}\n"
            for bonus in shard['bonuses'][:2]:
                text += f"  ├ {bonus}\n"
            text += f"  └ Способность: {shard['ability']['name']}\n\n"
    
    # Сетовые бонусы
    if len(collection) in SET_BONUSES:
        set_bonus = SET_BONUSES[str(len(collection))]
        text += f"\n🎯 *Активный сет:* {set_bonus['name']}\n"
        text += f"  └ {set_bonus['bonus']}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="nft:menu"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'nft_command',
    'nft_list_command',
    'nft_owned_command',
    'handle_callback'
]
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
