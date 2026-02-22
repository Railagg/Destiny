from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import json

def start_command(message, bot):
    """Обработчик команды /start"""
    from main import get_or_create_player, refresh_energy, refresh_magic, check_daily_login, get_daily_reward, save_character
    
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
        
        # Добавляем предметы
        for item in reward.get("items", []):
            if isinstance(item, list):
                item_name = item[0]
                item_count = item[1] if len(item) > 1 else 1
                for _ in range(item_count):
                    character.add_item(item_name)
            else:
                character.add_item(item)
        
        save_character(character)
        
        bot.send_message(
            message.chat.id,
            f"🎁 *Ежедневная награда!*\nДень {streak}\n"
            f"💰 +{reward['gold']} золота\n"
            f"🪙 +{reward['dstn']} DSTN",
            parse_mode='Markdown'
        )

    # СОЗДАЁМ КНОПКУ С WEBAPP
    markup = InlineKeyboardMarkup()
    
    # Главная кнопка для открытия игры
    webapp_button = InlineKeyboardButton(
        text="🎮 ОТКРЫТЬ ИГРУ",
        web_app=WebAppInfo(url="https://destiny-1-6m57.onrender.com")
    )
    markup.add(webapp_button)
    
    # Дополнительные кнопки
    markup.row(
        InlineKeyboardButton("📊 Статус", callback_data="game:status"),
        InlineKeyboardButton("🎒 Инвентарь", callback_data="game:inventory")
    )
    markup.row(
        InlineKeyboardButton("🐾 Питомцы", callback_data="pets:menu"),
        InlineKeyboardButton("💱 Обмен", callback_data="exchange:menu")
    )
    markup.row(
        InlineKeyboardButton("🏠 Домик", callback_data="game:house"),
        InlineKeyboardButton("⚔️ PvP", callback_data="pvp:menu")
    )

    bot.send_message(
        message.chat.id,
        f"👋 *Добро пожаловать, {first_name}!*\n\n"
        f"⚡ Энергия: {character.energy}/{character.max_energy}\n"
        f"💰 Золото: {character.gold}\n"
        f"🪙 DSTN: {character.destiny_tokens}\n"
        f"❤️ Здоровье: {character.health}/{character.max_health}\n"
        f"📈 Уровень: {character.level}\n\n"
        f"📅 Стрик входа: {character.login_streak or 0} дней\n\n"
        f"👇 Нажми кнопку ниже, чтобы открыть игру!",
        reply_markup=markup,
        parse_mode='Markdown'
    )

def help_command(message, bot):
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

def handle_webapp_data(call, bot):
    """Обработка данных из WebApp"""
    try:
        data = json.loads(call.web_app_data.data)
        print(f"📦 Получены данные из WebApp: {data}")
        
        action = data.get('action')
        
        if action == 'buy':
            item_id = data.get('item_id')
            price = data.get('price')
            bot.send_message(
                call.message.chat.id,
                f"✅ *Покупка в WebApp!*\nПредмет: {item_id}\nЦена: {price}💰",
                parse_mode='Markdown'
            )
            
        elif action == 'move':
            location = data.get('location')
            bot.send_message(
                call.message.chat.id,
                f"🚶 *Перемещение*\nТы перешёл в локацию: {location}",
                parse_mode='Markdown'
            )
            
        elif action == 'level_up':
            new_level = data.get('level')
            bot.send_message(
                call.message.chat.id,
                f"🎉 *Поздравляю!*\nТы достиг {new_level} уровня в WebApp!",
                parse_mode='Markdown'
            )
            
        elif action == 'achievement':
            achievement = data.get('name')
            bot.send_message(
                call.message.chat.id,
                f"🏆 *Новое достижение!*\n{achievement}",
                parse_mode='Markdown'
            )
            
        else:
            bot.send_message(
                call.message.chat.id,
                f"📦 Данные из игры: {data}",
                parse_mode='Markdown'
            )
            
        bot.answer_callback_query(call.id, "✅ Данные получены!")
        
    except Exception as e:
        print(f"❌ Ошибка обработки WebApp данных: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка")
