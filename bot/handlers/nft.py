import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def nft_command(message):
    """Команда /nft - NFT осколки"""
    from main import nft_data
    
    shards = nft_data.get("nft", {}).get("shards", {})
    
    text = "💎 *NFT-осколки стихий*\n\n"
    text += "Уникальные NFT, выпущенные ограниченным тиражом:\n\n"
    
    for shard_id, shard in shards.items():
        text += f"{shard.get('name')}\n"
        text += f"├ Всего: {shard.get('total_supply', 10)} шт\n"
        text += f"├ Цена: {shard.get('price_stars')}⭐ / {shard.get('price_dstn')} DSTN\n"
        for bonus in shard.get('bonuses', [])[:2]:
            text += f"├ {bonus}\n"
        text += f"└ Способность: {shard.get('ability', {}).get('name')}\n\n"
    
    text += "🏆 *Сетовые бонусы:*\n"
    text += "2 осколка: +2% ко всем характеристикам\n"
    text += "3 осколка: +3% ко всем характеристикам\n"
    text += "4 осколка: +4% ко всем характеристикам\n"
    text += "5 осколков: +5% + радужный ник + аура"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔴 Красный", callback_data="nft:red"),
        InlineKeyboardButton("🔵 Синий", callback_data="nft:blue"),
        InlineKeyboardButton("🟢 Зелёный", callback_data="nft:green"),
        InlineKeyboardButton("🟡 Жёлтый", callback_data="nft:yellow"),
        InlineKeyboardButton("🟣 Фиолетовый", callback_data="nft:purple")
    )
    markup.add(
        InlineKeyboardButton("ℹ️ О NFT", callback_data="nft:info"),
        InlineKeyboardButton("🏆 Моя коллекция", callback_data="nft:collection")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, get_or_create_player_func, nft_data):
    """Обработка кнопок NFT"""
    from main import save_character
    
    data = call.data.split(':')[1]
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    shards = nft_data.get("nft", {}).get("shards", {})
    set_bonuses = nft_data.get("nft", {}).get("set_bonuses", {})
    
    if data in shards:
        shard = shards[data]
        
        text = f"{shard.get('name')}\n\n"
        text += f"{shard.get('description')}\n\n"
        text += "✨ *Бонусы:*\n"
        for bonus in shard.get('bonuses', []):
            text += f"• {bonus}\n"
        
        text += f"\n⚡ *Способность:*\n"
        text += f"{shard.get('ability', {}).get('name')}: {shard.get('ability', {}).get('description')}\n"
        text += f"⏱️ КД: {shard.get('ability', {}).get('cooldown')}\n\n"
        
        text += f"📊 Всего выпущено: {shard.get('total_supply')} шт\n"
        text += f"💰 Цена: {shard.get('price_stars')}⭐ / {shard.get('price_dstn')} DSTN"
        
        # Проверяем, есть ли уже у игрока
        owned = False
        if hasattr(character, 'nft_collection'):
            owned = data in character.nft_collection
        
        markup = InlineKeyboardMarkup()
        if not owned:
            markup.add(
                InlineKeyboardButton("💎 Купить за Stars", callback_data=f"nft:buy_stars:{data}"),
                InlineKeyboardButton("💎 Купить за DSTN", callback_data=f"nft:buy_dstn:{data}")
            )
        else:
            markup.add(InlineKeyboardButton("✅ Уже куплено", callback_data="nft:noop"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="nft:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("buy_"):
        parts = data.split('_')
        payment = parts[1]
        shard_id = parts[2]
        
        bot_instance.answer_callback_query(call.id, "🔜 Скоро будет доступно")
        bot_instance.edit_message_text(
            f"🔜 *Покупка NFT*\n\n"
            f"Покупка NFT осколков появится в ближайшее время.\n\n"
            f"После покупки осколок будет привязан к твоему аккаунту.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
    
    elif data == "collection":
        collection = character.nft_collection if hasattr(character, 'nft_collection') else []
        
        if not collection:
            text = "🏆 *Твоя NFT коллекция*\n\n"
            text += "У тебя пока нет NFT осколков.\n\n"
            text += "Купи осколки, чтобы получить мощные бонусы!"
        else:
            text = "🏆 *Твоя NFT коллекция*\n\n"
            for shard_id in collection:
                if shard_id in shards:
                    shard = shards[shard_id]
                    text += f"• {shard.get('name')}\n"
            
            count = len(collection)
            if count in set_bonuses:
                bonus = set_bonuses[str(count)]
                text += f"\n🎯 *Сетовый бонус:* {bonus.get('name')}\n"
                text += f"{bonus.get('bonus')}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="nft:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "info":
        text = "ℹ️ *О NFT осколках*\n\n"
        text += "NFT осколки — уникальные цифровые предметы на блокчейне TON.\n\n"
        text += "✨ *Что дают:*\n"
        text += "• Постоянные бонусы к характеристикам\n"
        text += "• Уникальные способности\n"
        text += "• Особый цвет ника\n"
        text += "• Ауру вокруг персонажа\n"
        text += "• Рамку для аватарки\n"
        text += "• Предмет для дома (алтарь)\n\n"
        text += "🎯 *Сетовые бонусы*\n"
        text += "Собирай несколько осколков для дополнительных бонусов!\n\n"
        text += "📊 *Всего выпущено:* 50 NFT (по 10 каждого цвета)"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="nft:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        nft_command(call.message)
    
    elif data == "noop":
        bot_instance.answer_callback_query(call.id)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
