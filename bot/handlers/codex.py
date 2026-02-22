import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def codex_command(message):
    """Команда /codex - энциклопедия"""
    text = "📚 *ЭНЦИКЛОПЕДИЯ*\n\n"
    text += "Выбери раздел:\n\n"
    text += "👾 *Бестиарий* - все монстры\n"
    text += "⚔️ *Предметы* - все предметы\n"
    text += "🗺️ *Локации* - все места\n"
    text += "🏆 *Достижения* - все ачивки\n"
    text += "🔨 *Крафт* - все рецепты\n"
    text += "🎭 *Классы* - информация о классах"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👾 Бестиарий", callback_data="codex:bestiary"),
        InlineKeyboardButton("⚔️ Предметы", callback_data="codex:items"),
        InlineKeyboardButton("🗺️ Локации", callback_data="codex:locations"),
        InlineKeyboardButton("🏆 Достижения", callback_data="codex:achievements"),
        InlineKeyboardButton("🔨 Крафт", callback_data="codex:crafting"),
        InlineKeyboardButton("🎭 Классы", callback_data="codex:classes")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def handle_callback(call, bot_instance, codex_data):
    """Обработка кнопок энциклопедии"""
    data = call.data.split(':')[1]
    
    if data == "bestiary":
        bestiary = codex_data.get("codex", {}).get("bestiary", {})
        categories = bestiary.get("categories", {})
        
        text = "👾 *БЕСТИАРИЙ*\n\n"
        text += "Выбери категорию монстров:\n\n"
        
        for cat_id, category in categories.items():
            text += f"• {category.get('name')} - {category.get('description', '')}\n"
        
        markup = InlineKeyboardMarkup(row_width=2)
        for cat_id in categories.keys():
            cat_name = categories[cat_id].get('name', cat_id)
            markup.add(InlineKeyboardButton(cat_name, callback_data=f"codex:bestiary_{cat_id}"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("bestiary_"):
        cat_id = data.replace("bestiary_", "")
        bestiary = codex_data.get("codex", {}).get("bestiary", {})
        category = bestiary.get("categories", {}).get(cat_id, {})
        creatures = category.get("creatures", [])
        
        text = f"👾 *{category.get('name')}*\n\n"
        
        for creature in creatures[:10]:  # Показываем первых 10
            text += f"• *{creature.get('name')}* (ур. {creature.get('level', '?')})\n"
            text += f"  ❤️ {creature.get('health')} | ⚔️ {creature.get('damage')}\n"
            text += f"  💰 {creature.get('gold')} | ✨ {creature.get('exp')}\n"
            if creature.get('drops'):
                text += f"  🎁 Дроп: {', '.join(creature['drops'][:3])}\n"
            text += f"  📍 {creature.get('location', 'Неизвестно')}\n\n"
        
        if len(creatures) > 10:
            text += f"...и ещё {len(creatures) - 10} видов"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:bestiary"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "items":
        items = codex_data.get("codex", {}).get("items", {})
        categories = items.get("categories", {})
        
        text = "⚔️ *ПРЕДМЕТЫ*\n\n"
        text += "Выбери категорию предметов:\n\n"
        
        for cat_id, category in categories.items():
            text += f"• {category.get('name')} - {category.get('description', '')}\n"
        
        markup = InlineKeyboardMarkup(row_width=2)
        for cat_id in categories.keys():
            cat_name = categories[cat_id].get('name', cat_id)
            markup.add(InlineKeyboardButton(cat_name, callback_data=f"codex:items_{cat_id}"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("items_"):
        cat_id = data.replace("items_", "")
        items = codex_data.get("codex", {}).get("items", {})
        category = items.get("categories", {}).get(cat_id, {})
        
        text = f"⚔️ *{category.get('name')}*\n\n"
        
        if cat_id == "materials":
            materials = category.get("items", [])
            for item in materials[:10]:
                text += f"• *{item.get('name')}* ({item.get('rarity', '')})\n"
                text += f"  💰 {item.get('value')} | {item.get('description')}\n"
                if item.get('source'):
                    text += f"  📍 {item.get('source')}\n\n"
        else:
            subcategories = category.get("subcategories", {})
            for sub_id, subcat in subcategories.items():
                text += f"*{subcat.get('name')}*\n"
                items_list = subcat.get("items", [])
                for item in items_list[:5]:
                    text += f"  • {item.get('name')} - {item.get('description')}\n"
                if len(items_list) > 5:
                    text += f"  ...и ещё {len(items_list) - 5} предметов\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:items"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "locations":
        locations = codex_data.get("codex", {}).get("locations", {})
        categories = locations.get("categories", {})
        
        text = "🗺️ *ЛОКАЦИИ*\n\n"
        text += "Выбери категорию мест:\n\n"
        
        for cat_id, category in categories.items():
            text += f"• {category.get('name')} - {category.get('description', '')}\n"
        
        markup = InlineKeyboardMarkup(row_width=2)
        for cat_id in categories.keys():
            cat_name = categories[cat_id].get('name', cat_id)
            markup.add(InlineKeyboardButton(cat_name, callback_data=f"codex:locations_{cat_id}"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("locations_"):
        cat_id = data.replace("locations_", "")
        locations = codex_data.get("codex", {}).get("locations", {})
        category = locations.get("categories", {}).get(cat_id, {})
        loc_list = category.get("locations", [])
        
        text = f"🗺️ *{category.get('name')}*\n\n"
        
        for loc in loc_list[:10]:
            text += f"• *{loc.get('name')}* (ур. {loc.get('level_req', '?')})\n"
            text += f"  {loc.get('description', '')}\n"
            if loc.get('resources'):
                text += f"  Ресурсы: {', '.join(loc['resources'][:3])}\n"
            if loc.get('mobs'):
                text += f"  Мобы: {', '.join(loc['mobs'][:3])}\n\n"
        
        if len(loc_list) > 10:
            text += f"...и ещё {len(loc_list) - 10} локаций"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:locations"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "achievements":
        achievements = codex_data.get("codex", {}).get("achievements", {})
        categories = achievements.get("categories", {})
        
        text = "🏆 *ДОСТИЖЕНИЯ*\n\n"
        text += "Выбери категорию достижений:\n\n"
        
        for cat_id, category in categories.items():
            text += f"• {category.get('name')}\n"
        
        markup = InlineKeyboardMarkup(row_width=2)
        for cat_id in categories.keys():
            cat_name = categories[cat_id].get('name', cat_id)
            markup.add(InlineKeyboardButton(cat_name, callback_data=f"codex:achievements_{cat_id}"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("achievements_"):
        cat_id = data.replace("achievements_", "")
        achievements = codex_data.get("codex", {}).get("achievements", {})
        category = achievements.get("categories", {}).get(cat_id, {})
        ach_list = category.get("achievements", [])
        
        text = f"🏆 *{category.get('name', 'Достижения')}*\n\n"
        
        for ach in ach_list[:10]:
            text += f"• *{ach.get('name')}*\n"
            text += f"  {ach.get('description', '')}\n"
            if ach.get('reward'):
                rewards = []
                if 'dstn' in ach['reward']:
                    rewards.append(f"{ach['reward']['dstn']} DSTN")
                if 'title' in ach['reward']:
                    rewards.append(f"титул '{ach['reward']['title']}'")
                if 'rainbow_shard' in ach['reward']:
                    rewards.append(f"{ach['reward']['rainbow_shard']} 🌈 осколок")
                text += f"  🎁 Награда: {', '.join(rewards)}\n\n"
        
        if len(ach_list) > 10:
            text += f"...и ещё {len(ach_list) - 10} достижений"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:achievements"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "crafting":
        crafting = codex_data.get("codex", {}).get("crafting", {})
        categories = crafting.get("categories", {})
        
        text = "🔨 *КРАФТ*\n\n"
        text += "Выбери категорию рецептов:\n\n"
        
        for cat_id, category in categories.items():
            text += f"• {category.get('name')}\n"
        
        markup = InlineKeyboardMarkup(row_width=2)
        for cat_id in categories.keys():
            cat_name = categories[cat_id].get('name', cat_id)
            markup.add(InlineKeyboardButton(cat_name, callback_data=f"codex:crafting_{cat_id}"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("crafting_"):
        cat_id = data.replace("crafting_", "")
        crafting = codex_data.get("codex", {}).get("crafting", {})
        category = crafting.get("categories", {}).get(cat_id, {})
        recipes = category.get("recipes", [])
        
        text = f"🔨 *{category.get('name', 'Крафт')}*\n\n"
        
        for recipe in recipes[:10]:
            text += f"• *{recipe.get('name')}*\n"
            text += f"  Требования: уровень {recipe.get('level_req', 1)}\n"
            if recipe.get('materials'):
                mats = []
                for mat, count in recipe['materials'].items():
                    mats.append(f"{count} {mat}")
                text += f"  Материалы: {', '.join(mats)}\n"
            text += f"  Результат: {recipe.get('result', '')}\n"
            text += f"  Станция: {recipe.get('station', 'верстак')}\n\n"
        
        if len(recipes) > 10:
            text += f"...и ещё {len(recipes) - 10} рецептов"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:crafting"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "classes":
        classes = codex_data.get("codex", {}).get("classes", {})
        class_list = classes.get("classes", [])
        
        text = "🎭 *КЛАССЫ*\n\n"
        
        for cls in class_list:
            text += f"• *{cls.get('name')}*\n"
            text += f"  {cls.get('description', '')}\n"
            text += f"  ❤️ {cls.get('health', '?')} | ⚔️ {cls.get('damage', '?')} | 🛡️ {cls.get('defense', '?')}\n"
            text += f"  Особенность: {cls.get('mastery', '')}\n\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
        
        bot_instance.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu":
        codex_command(call.message)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
