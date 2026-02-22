import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def shop_command(message):
    """Команда /shop - магазин"""
    from main import get_or_create_player
    
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    text = "🏪 *МАГАЗИН*\n\n"
    text += f"💰 Твой баланс: {character.gold} золота, {character.destiny_tokens} DSTN\n\n"
    text += "Выбери категорию:\n\n"
    text += "⚔️ Оружие\n"
    text += "🛡️ Броня\n"
    text += "🛠️ Инструменты\n"
    text += "⚗️ Зелья\n"
    text += "🍲 Еда\n"
    text += "🪱 Наживки\n"
    text += "🎁 Сундуки\n"
    text += "👑 Премиум"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Оружие", callback_data="shop:weapons"),
        InlineKeyboardButton("🛡️ Броня", callback_data="shop:armor"),
        InlineKeyboardButton("🛠️ Инструменты", callback_data="shop:tools"),
        InlineKeyboardButton("⚗️ Зелья", callback_data="shop:potions"),
        InlineKeyboardButton("🍲 Еда", callback_data="shop:food"),
        InlineKeyboardButton("🪱 Наживки", callback_data="shop:bait"),
        InlineKeyboardButton("🎁 Сундуки", callback_data="shop:chests"),
        InlineKeyboardButton("👑 Премиум", callback_data="premium:menu")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func, items_data):
    """Обработка кнопок магазина"""
    from main import save_character
    
    data = call.data.split(':')[1]
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if data == "weapons":
        text = "⚔️ *ОРУЖИЕ*\n\n"
        text += "Доступные мечи:\n\n"
        
        weapons = []
        for item_id, item in items_data.get("items", {}).items():
            if item.get("type") == "weapon" and item.get("class") == "warrior":
                if item.get("rarity") in ["common", "uncommon"] and item.get("level_req", 0) <= character.level:
                    weapons.append(item)
        
        for item in weapons[:10]:
            text += f"• *{item.get('name')}*\n"
            text += f"  Урон: +{item.get('damage', 0)}\n"
            text += f"  Требуется уровень: {item.get('level_req', 1)}\n"
            text += f"  Цена: {item.get('value', 0)}💰\n\n"
        
        text += "Остальное оружие можно скрафтить!"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "armor":
        text = "🛡️ *БРОНЯ*\n\n"
        text += "Доступная броня:\n\n"
        
        armors = []
        for item_id, item in items_data.get("items", {}).items():
            if item.get("type") == "armor" and item.get("rarity") in ["common", "uncommon"]:
                if item.get("level_req", 0) <= character.level:
                    armors.append(item)
        
        for item in armors[:10]:
            text += f"• *{item.get('name')}*\n"
            text += f"  Защита: +{item.get('defense', 0)} | ❤️ +{item.get('health', 0)}\n"
            text += f"  Требуется уровень: {item.get('level_req', 1)}\n"
            text += f"  Цена: {item.get('value', 0)}💰\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "tools":
        text = "🛠️ *ИНСТРУМЕНТЫ*\n\n"
        text += "• ⛏️ *Кирки* - для добычи руды\n"
        text += "• 🪣 *Удочки* - для рыбалки\n"
        text += "• 🌿 *Серпы* - для сбора трав\n"
        text += "• 🥕 *Мотыги* - для огорода\n\n"
        text += "Выбери тип инструментов:"
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("⛏️ Кирки", callback_data="shop:pickaxes"),
            InlineKeyboardButton("🎣 Удочки", callback_data="shop:fishing_rods"),
            InlineKeyboardButton("🌿 Серпы", callback_data="shop:sickles"),
            InlineKeyboardButton("🥕 Мотыги", callback_data="shop:hoes")
        )
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "pickaxes":
        text = "⛏️ *КИРКИ*\n\n"
        
        pickaxes = []
        for item_id, item in items_data.get("items", {}).items():
            if "pickaxe" in item_id:
                pickaxes.append(item)
        
        for item in pickaxes:
            text += f"• *{item.get('name')}*\n"
            text += f"  Прочность: {item.get('durability', 0)}\n"
            text += f"  Цена: {item.get('value', 0)}💰\n"
            if item.get('rarity') in ['rare', 'epic']:
                text += f"  ✨ {item.get('description', '')}\n"
            text += "\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:tools"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "fishing_rods":
        text = "🎣 *УДОЧКИ*\n\n"
        
        rods = []
        for item_id, item in items_data.get("items", {}).items():
            if "fishing_rod" in item_id:
                rods.append(item)
        
        for item in rods:
            text += f"• *{item.get('name')}*\n"
            text += f"  Прочность: {item.get('durability', 0)}\n"
            if item.get('bait_bonus'):
                text += f"  🎣 Бонус: +{item.get('bait_bonus')}% к редкой рыбе\n"
            text += f"  Цена: {item.get('value', 0)}💰\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:tools"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "sickles":
        text = "🌿 *СЕРПЫ*\n\n"
        
        sickles = []
        for item_id, item in items_data.get("items", {}).items():
            if "sickle" in item_id:
                sickles.append(item)
        
        for item in sickles:
            text += f"• *{item.get('name')}*\n"
            text += f"  Прочность: {item.get('durability', 0)}\n"
            if item.get('harvest_bonus'):
                text += f"  🌱 +{item.get('harvest_bonus')} травы за сбор\n"
            if item.get('rare_chance'):
                text += f"  ✨ {item.get('rare_chance')}% шанс на редкую траву\n"
            text += f"  Цена: {item.get('value', 0)}💰\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:tools"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "hoes":
        text = "🥕 *МОТЫГИ*\n\n"
        
        hoes = []
        for item_id, item in items_data.get("items", {}).items():
            if "hoe" in item_id:
                hoes.append(item)
        
        for item in hoes:
            text += f"• *{item.get('name')}*\n"
            text += f"  Прочность: {item.get('durability', 0)}\n"
            if item.get('harvest_bonus'):
                text += f"  🥔 +{item.get('harvest_bonus')} овоща за сбор\n"
            if item.get('rare_chance'):
                text += f"  ✨ {item.get('rare_chance')}% шанс на редкий овощ\n"
            text += f"  Цена: {item.get('value', 0)}💰\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:tools"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "potions":
        text = "⚗️ *ЗЕЛЬЯ*\n\n"
        
        potions = []
        for item_id, item in items_data.get("items", {}).items():
            if item.get("type") == "consumable" and "potion" in item_id:
                potions.append(item)
        
        for item in potions[:10]:
            text += f"• *{item.get('name')}*\n"
            if item.get('heal'):
                text += f"  ❤️ Восстанавливает {item.get('heal')} здоровья\n"
            if item.get('mana'):
                text += f"  🔮 Восстанавливает {item.get('mana')} маны\n"
            if item.get('effect'):
                text += f"  ✨ Эффект: {item.get('effect')}\n"
            text += f"  Цена: {item.get('value', 0)}💰\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "food":
        text = "🍲 *ЕДА*\n\n"
        
        foods = []
        for item_id, item in items_data.get("items", {}).items():
            if item.get("type") == "food":
                foods.append(item)
        
        for item in foods[:10]:
            text += f"• *{item.get('name')}*\n"
            text += f"  ❤️ +{item.get('heal', 0)} | ⚡ +{item.get('energy', 0)}\n"
            if item.get('effect'):
                text += f"  ✨ {item.get('effect')}\n"
            text += f"  Цена: {item.get('value', 0)}💰\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "bait":
        text = "🪱 *НАЖИВКИ*\n\n"
        
        baits = []
        for item_id, item in items_data.get("items", {}).items():
            if item.get("type") == "bait":
                baits.append(item)
        
        for item in baits:
            text += f"• *{item.get('name')}*\n"
            text += f"  🎣 Сила: {item.get('fishing_power', 0)}\n"
            if item.get('rare_fish_chance'):
                text += f"  ✨ +{item.get('rare_fish_chance')}% к редкой рыбе\n"
            if item.get('legendary_fish_chance'):
                text += f"  🌟 +{item.get('legendary_fish_chance')}% к легендарной рыбе\n"
            text += f"  Цена: {item.get('value', 0)}💰\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "chests":
        text = "🎁 *СУНДУКИ*\n\n"
        text += "• 📦 *Редкий сундук* - 50💰\n"
        text += "  Содержит обычные и необычные предметы\n\n"
        text += "• 🎁 *Эпический сундук* - 200💰\n"
        text += "  Гарантированный эпический предмет\n\n"
        text += "• 📦 *Легендарный сундук* - 1000💰\n"
        text += "  Шанс на легендарные предметы\n\n"
        text += "• 🎁 *Премиум сундук* - 500 DSTN\n"
        text += "  Содержит редкие ресурсы и осколки\n\n"
        text += "• 📦 *Радужный сундук* - 5 ⭐\n"
        text += "  Шанс на радужные осколки"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="shop:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        shop_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
