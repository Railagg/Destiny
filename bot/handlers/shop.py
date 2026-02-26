# /bot/handlers/shop.py
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

logger = logging.getLogger(__name__)

def shop_command(message, bot, get_or_create_player, items_data):
    """Команда /shop - магазин"""
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    text = "🏪 *МАГАЗИН*\n\n"
    text += f"💰 Твой баланс: {character.gold} золота\n"
    text += f"💎 DSTN: {character.destiny_tokens or 0}\n"
    if hasattr(character, 'rainbow_shards') and character.rainbow_shards:
        text += f"🌈 Осколки: {character.rainbow_shards}\n"
    if hasattr(character, 'rainbow_stones') and character.rainbow_stones:
        text += f"💎 Радужные камни: {character.rainbow_stones}\n\n"
    
    text += "Выбери категорию товаров:"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Оружие", callback_data="shop:category:weapons"),
        InlineKeyboardButton("🛡️ Броня", callback_data="shop:category:armor"),
        InlineKeyboardButton("🛠️ Инструменты", callback_data="shop:category:tools"),
        InlineKeyboardButton("⚗️ Зелья", callback_data="shop:category:potions"),
        InlineKeyboardButton("🍲 Еда", callback_data="shop:category:food"),
        InlineKeyboardButton("🪱 Наживки", callback_data="shop:category:bait"),
        InlineKeyboardButton("🎁 Сундуки", callback_data="shop:category:chests"),
        InlineKeyboardButton("📦 Ресурсы", callback_data="shop:category:resources"),
        InlineKeyboardButton("✨ Расходники", callback_data="shop:category:consumables"),
        InlineKeyboardButton("👑 Премиум", callback_data="premium:menu")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def buy_command(message, bot, get_or_create_player, items_data):
    """Команда /buy - купить предмет"""
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Укажи ID предмета!\n"
            "Пример: /buy health_potion\n"
            "Список товаров: /shop",
            parse_mode='Markdown'
        )
        return
    
    item_id = args[1]
    item = items_data.get("items", {}).get(item_id)
    
    if not item:
        bot.send_message(
            message.chat.id,
            "❌ Предмет не найден!",
            parse_mode='Markdown'
        )
        return
    
    price = item.get('value', 0)
    
    if character.gold < price:
        bot.send_message(
            message.chat.id,
            f"❌ Не хватает золота! Нужно {price}💰",
            parse_mode='Markdown'
        )
        return
    
    character.gold -= price
    character.add_item(item_id)
    
    from main import save_character
    save_character(character)
    
    bot.send_message(
        message.chat.id,
        f"✅ Куплено: {item.get('name', item_id)} за {price}💰",
        parse_mode='Markdown'
    )

def shop_categories_command(message, bot, get_or_create_player, items_data):
    """Команда /shop_categories - список категорий магазина"""
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    text = "📋 *КАТЕГОРИИ МАГАЗИНА*\n\n"
    text += "⚔️ Оружие - мечи, луки, посохи\n"
    text += "🛡️ Броня - шлемы, нагрудники, поножи\n"
    text += "🛠️ Инструменты - кирки, топоры, удочки\n"
    text += "⚗️ Зелья - лечения, маны, силы\n"
    text += "🍲 Еда - восстанавливает здоровье\n"
    text += "🪱 Наживки - для рыбалки\n"
    text += "🎁 Сундуки - случайные предметы\n"
    text += "📦 Ресурсы - руда, дерево, травы\n"
    text += "✨ Расходники - свитки, зелья\n"
    text += "👑 Премиум - особые товары\n\n"
    text += "Используй /shop для просмотра товаров."
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏪 В магазин", callback_data="shop:menu"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_category(call, bot, get_or_create_player, items_data, category):
    """Показать товары в категории"""
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Определяем товары в категории
    items = []
    
    # Словарь категорий
    categories = {
        "weapons": {
            "name": "⚔️ Оружие",
            "filter": lambda item: item.get("type") == "weapon" and item.get("rarity") in ["common", "uncommon", "rare"],
            "show_price": True
        },
        "armor": {
            "name": "🛡️ Броня",
            "filter": lambda item: item.get("type") == "armor" and item.get("rarity") in ["common", "uncommon", "rare"],
            "show_price": True
        },
        "tools": {
            "name": "🛠️ Инструменты",
            "filter": lambda item: item.get("type") == "tool",
            "show_price": True
        },
        "potions": {
            "name": "⚗️ Зелья",
            "filter": lambda item: item.get("type") == "potion" and item.get("rarity") in ["common", "uncommon"],
            "show_price": True
        },
        "food": {
            "name": "🍲 Еда",
            "filter": lambda item: item.get("type") == "food",
            "show_price": True
        },
        "bait": {
            "name": "🪱 Наживки",
            "filter": lambda item: item.get("type") == "bait",
            "show_price": True
        },
        "chests": {
            "name": "🎁 Сундуки",
            "filter": lambda item: item.get("type") == "chest",
            "show_price": True
        },
        "resources": {
            "name": "📦 Ресурсы",
            "filter": lambda item: item.get("type") in ["material", "ore", "herb"],
            "show_price": True
        },
        "consumables": {
            "name": "✨ Расходники",
            "filter": lambda item: item.get("type") in ["consumable", "scroll"],
            "show_price": True
        }
    }
    
    if category not in categories:
        bot.answer_callback_query(call.id, "❌ Категория не найдена")
        return
    
    cat_info = categories[category]
    text = f"{cat_info['name']}\n\n"
    
    # Собираем подходящие предметы
    for item_id, item in items_data.get("items", {}).items():
        if cat_info["filter"](item):
            level_req = item.get("level_req", 1)
            if character.level >= level_req:
                items.append((item_id, item))
    
    if not items:
        text += "В этой категории пока нет товаров."
    else:
        for item_id, item in items[:10]:  # Показываем первые 10
            name = item.get('name', item_id)
            rarity = item.get('rarity', 'common')
            rarity_emoji = {
                'common': '⚪',
                'uncommon': '🟢',
                'rare': '🔵',
                'epic': '🟣',
                'legendary': '🟡',
                'ancient': '🔴'
            }.get(rarity, '⚪')
            
            value = item.get('value', 0)
            currency = "💰" if value > 0 else ""
            
            text += f"{rarity_emoji} *{name}*\n"
            
            # Показываем характеристики
            if item.get('damage'):
                text += f"  ⚔️ Урон: +{item['damage']}\n"
            if item.get('defense'):
                text += f"  🛡️ Защита: +{item['defense']}\n"
            if item.get('magic_damage'):
                text += f"  🔮 Маг. урон: +{item['magic_damage']}\n"
            if item.get('heal'):
                text += f"  ❤️ Лечение: {item['heal']}\n"
            if item.get('energy'):
                text += f"  ⚡ Энергия: +{item['energy']}\n"
            if item.get('durability'):
                text += f"  🔧 Прочность: {item['durability']}\n"
            if item.get('harvest_bonus'):
                text += f"  🌿 +{item['harvest_bonus']} к сбору\n"
            
            text += f"  {currency} Цена: {value} золота\n"
            text += "\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки покупки для первых 5 предметов
    for item_id, item in items[:5]:
        value = item.get('value', 0)
        if value > 0 and character.gold >= value:
            markup.add(InlineKeyboardButton(
                f"✅ Купить {item.get('name', item_id)} за {value}💰",
                callback_data=f"shop:buy:{item_id}:gold:{category}"
            ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:menu"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id)

def show_chests(call, bot, get_or_create_player, items_data):
    """Показать сундуки"""
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    text = "🎁 *СУНДУКИ*\n\n"
    text += f"💰 Твой баланс: {character.gold} золота\n"
    text += f"💎 DSTN: {character.destiny_tokens or 0}\n\n"
    
    chests = {
        "common_chest": {
            "name": "📦 Обычный сундук",
            "price_gold": 100,
            "price_dstn": 0,
            "description": "Содержит обычные ресурсы и предметы",
            "emoji": "📦"
        },
        "rare_chest": {
            "name": "🎁 Редкий сундук",
            "price_gold": 500,
            "price_dstn": 5,
            "description": "Шанс на редкие предметы",
            "emoji": "🎁"
        },
        "epic_chest": {
            "name": "🧧 Эпический сундук",
            "price_gold": 0,
            "price_dstn": 25,
            "description": "Гарантированный эпический предмет",
            "emoji": "🧧"
        },
        "legendary_chest": {
            "name": "👑 Легендарный сундук",
            "price_gold": 0,
            "price_dstn": 100,
            "description": "Шанс на легендарные предметы",
            "emoji": "👑"
        },
        "elemental_chest": {
            "name": "🌀 Сундук стихий",
            "price_gold": 0,
            "price_dstn": 50,
            "description": "Содержит элементы стихий",
            "emoji": "🌀"
        }
    }
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for chest_id, chest in chests.items():
        text += f"{chest['emoji']} *{chest['name']}*\n"
        text += f"  {chest['description']}\n"
        
        prices = []
        if chest['price_gold'] > 0:
            prices.append(f"{chest['price_gold']}💰")
        if chest['price_dstn'] > 0:
            prices.append(f"{chest['price_dstn']}💎")
        
        text += f"  Цена: {' + '.join(prices)}\n\n"
        
        # Кнопка покупки
        can_buy_gold = chest['price_gold'] > 0 and character.gold >= chest['price_gold']
        can_buy_dstn = chest['price_dstn'] > 0 and character.destiny_tokens >= chest['price_dstn']
        
        if can_buy_gold:
            markup.add(InlineKeyboardButton(
                f"💰 Купить {chest['name']} за {chest['price_gold']}💰",
                callback_data=f"shop:buy_chest:{chest_id}:gold"
            ))
        if can_buy_dstn:
            markup.add(InlineKeyboardButton(
                f"💎 Купить {chest['name']} за {chest['price_dstn']}💎",
                callback_data=f"shop:buy_chest:{chest_id}:dstn"
            ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:menu"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id)

def buy_item(call, bot, get_or_create_player, items_data, item_id, currency, category="menu"):
    """Купить предмет"""
    from main import save_character
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    item = items_data.get("items", {}).get(item_id)
    if not item:
        bot.answer_callback_query(call.id, "❌ Предмет не найден")
        return
    
    price = item.get('value', 0)
    if currency == "gold":
        if character.gold < price:
            bot.answer_callback_query(call.id, f"❌ Не хватает золота! Нужно {price}")
            return
        character.gold -= price
    elif currency == "dstn":
        if character.destiny_tokens < price:
            bot.answer_callback_query(call.id, f"❌ Не хватает DSTN! Нужно {price}")
            return
        character.destiny_tokens -= price
    else:
        bot.answer_callback_query(call.id, "❌ Неизвестная валюта")
        return
    
    character.add_item(item_id)
    save_character(character)
    
    bot.answer_callback_query(call.id, f"✅ Куплено: {item.get('name', item_id)}!")
    
    # Возвращаемся в категорию
    if category == "chests":
        show_chests(call, bot, get_or_create_player, items_data)
    else:
        show_category(call, bot, get_or_create_player, items_data, category)

def buy_chest(call, bot, get_or_create_player, items_data, chest_id, currency):
    """Купить сундук"""
    from main import save_character
    import random
    
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    chests = {
        "common_chest": {"price_gold": 100, "price_dstn": 0},
        "rare_chest": {"price_gold": 500, "price_dstn": 5},
        "epic_chest": {"price_gold": 0, "price_dstn": 25},
        "legendary_chest": {"price_gold": 0, "price_dstn": 100},
        "elemental_chest": {"price_gold": 0, "price_dstn": 50}
    }
    
    if chest_id not in chests:
        bot.answer_callback_query(call.id, "❌ Сундук не найден")
        return
    
    chest = chests[chest_id]
    price_key = f"price_{currency}"
    price = chest.get(price_key, 0)
    
    if price == 0:
        bot.answer_callback_query(call.id, "❌ Этот сундук нельзя купить за эту валюту")
        return
    
    if currency == "gold":
        if character.gold < price:
            bot.answer_callback_query(call.id, f"❌ Не хватает золота! Нужно {price}")
            return
        character.gold -= price
    elif currency == "dstn":
        if character.destiny_tokens < price:
            bot.answer_callback_query(call.id, f"❌ Не хватает DSTN! Нужно {price}")
            return
        character.destiny_tokens -= price
    else:
        bot.answer_callback_query(call.id, "❌ Неизвестная валюта")
        return
    
    # Генерируем содержимое сундука
    rewards = []
    
    if chest_id == "common_chest":
        possible = ["wood", "stone", "herb", "berry", "copper_ore"]
        for _ in range(3):
            rewards.append(random.choice(possible))
    
    elif chest_id == "rare_chest":
        possible = ["iron_ore", "gold_ore", "magic_herb", "leather", "health_potion"]
        for _ in range(2):
            rewards.append(random.choice(possible))
        if random.random() < 0.3:
            rewards.append("rare_chest_key")
    
    elif chest_id == "epic_chest":
        possible = ["mythril_ingot", "magic_crystal", "diamond", "ruby", "epic_chest_key"]
        for _ in range(2):
            rewards.append(random.choice(possible))
        if random.random() < 0.5:
            rewards.append("epic_chest_key")
    
    elif chest_id == "legendary_chest":
        possible = ["dragon_scale", "phoenix_feather", "legendary_sword", "legendary_armor", "legendary_chest_key"]
        rewards.append(random.choice(possible))
        if random.random() < 0.3:
            rewards.append("rainbow_shard")
    
    elif chest_id == "elemental_chest":
        possible = ["fire_gem", "ice_crystal", "elemental_core", "lava_core", "storm_essence"]
        for _ in range(2):
            rewards.append(random.choice(possible))
    
    # Добавляем предметы
    for item_id in rewards:
        character.add_item(item_id)
    
    save_character(character)
    
    # Показываем результат
    reward_names = []
    for item_id in rewards:
        item = items_data.get("items", {}).get(item_id, {})
        reward_names.append(item.get('name', item_id))
    
    text = f"🎉 *Ты получил из сундука:*\n\n"
    for name in reward_names:
        text += f"• {name}\n"
    
    bot.answer_callback_query(call.id, f"✅ Сундук открыт!")
    
    # Отправляем результат отдельным сообщением
    bot.send_message(
        call.message.chat.id,
        text,
        parse_mode='Markdown'
    )
    
    # Возвращаемся к сундукам
    show_chests(call, bot, get_or_create_player, items_data)

def handle_callback(call, bot, get_or_create_player, items_data):
    """Обработчик колбэков для магазина"""
    try:
        data = call.data.split(':')
        action = data[1]
        
        if action == "menu":
            shop_command(call.message, bot, get_or_create_player, items_data)
        
        elif action == "category" and len(data) > 2:
            category = data[2]
            if category == "chests":
                show_chests(call, bot, get_or_create_player, items_data)
            else:
                show_category(call, bot, get_or_create_player, items_data, category)
        
        elif action == "buy" and len(data) > 3:
            item_id = data[2]
            currency = data[3]
            category = data[4] if len(data) > 4 else "menu"
            buy_item(call, bot, get_or_create_player, items_data, item_id, currency, category)
        
        elif action == "buy_chest" and len(data) > 3:
            chest_id = data[2]
            currency = data[3]
            buy_chest(call, bot, get_or_create_player, items_data, chest_id, currency)
        
        else:
            bot.answer_callback_query(call.id, "❌ Неизвестное действие")
    
    except Exception as e:
        logging.error(f"Ошибка в shop callback: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка")

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'shop_command',
    'buy_command',
    'shop_categories_command',
    'handle_callback'
]
