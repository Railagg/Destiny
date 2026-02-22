import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import os

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

def start_command(message):
    """Обработчик команды /start"""
    from main import get_or_create_player, refresh_energy, refresh_magic, check_daily_login, get_daily_reward
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    user, character = get_or_create_player(user_id, username, first_name)

    refresh_energy(character)
    refresh_magic(character)
    
    # Проверяем ежедневный вход
    claimed, streak = check_daily_login(character)
    if claimed:
        reward = get_daily_reward(streak)
        character.gold += reward["gold"]
        character.destiny_tokens += reward["dstn"]
        for item in reward["items"]:
            if isinstance(item, list):
                for _ in range(item[1]):
                    character.add_item(item[0])
            else:
                character.add_item(item)
        from main import save_character
        save_character(character)
        
        bot.send_message(
            message.chat.id,
            f"🎁 *Ежедневная награда!*\nДень {streak}\n"
            f"💰 +{reward['gold']} золота\n"
            f"🪙 +{reward['dstn']} DSTN",
            parse_mode='Markdown'
        )

    # Создаем клавиатуру с WebApp
    markup = InlineKeyboardMarkup()
    webapp_button = InlineKeyboardButton(
        text="🎮 ОТКРЫТЬ ИГРУ",
        web_app=WebAppInfo(url="https://destiny-1-6m57.onrender.com")
    )
    markup.add(webapp_button)
    
    # Добавляем кнопки для команд
    markup.row(
        InlineKeyboardButton("📊 Статус", callback_data="game:status"),
        InlineKeyboardButton("🎒 Инвентарь", callback_data="game:inventory")
    )
    markup.row(
        InlineKeyboardButton("🗺️ Карта", callback_data="game:map"),
        InlineKeyboardButton("📜 Квесты", callback_data="game:quests")
    )
    markup.row(
        InlineKeyboardButton("🐾 Питомцы", callback_data="pets:menu"),
        InlineKeyboardButton("💱 Обмен", callback_data="exchange:menu")
    )

    bot.send_message(
        message.chat.id,
        f"👋 *Добро пожаловать, {first_name}!*\n\n"
        f"⚡ Энергия: {character.energy}/{character.max_energy}\n"
        f"💰 Золото: {character.gold}\n"
        f"🪙 DSTN: {character.destiny_tokens}\n"
        f"❤️ Здоровье: {character.health}/{character.max_health}\n\n"
        f"📅 Стрик входа: {character.login_streak or 0} дней",
        reply_markup=markup,
        parse_mode='Markdown'
    )

def help_command(message):
    """Обработчик команды /help"""
    text = "❓ *Помощь*\n\n"
    text += "📋 *Основные команды:*\n"
    text += "/start - начать игру\n"
    text += "/profile - профиль\n"
    text += "/status - статус\n"
    text += "/inventory - инвентарь\n"
    text += "/location - локация\n"
    text += "/map - карта мира\n\n"
    text += "⚔️ *Боевые:*\n"
    text += "/class - выбор класса\n"
    text += "/pvp - PvP арена\n\n"
    text += "🏠 *Домик:*\n"
    text += "/house - домик\n"
    text += "/craft - крафт\n\n"
    text += "🐾 *Питомцы:*\n"
    text += "/pets - питомцы\n\n"
    text += "👥 *Социальное:*\n"
    text += "/guild - гильдия\n"
    text += "/top - рейтинги\n\n"
    text += "📚 *Информация:*\n"
    text += "/codex - энциклопедия\n"
    text += "/events - ивенты\n\n"
    text += "💎 *Премиум:*\n"
    text += "/premium - подписка\n"
    text += "/nft - NFT осколки\n"
    text += "/rainbow - радужные камни\n"
    text += "/shop - магазин\n\n"
    text += "💱 *Экономика:*\n"
    text += "/exchange - обмен TON/DSTN"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
