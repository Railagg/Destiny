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
        character.dstn = (character.dstn or 0) + reward.get("dstn", 0)
        
        # Добавляем радужные осколки (3 и 6 день)
        if streak == 3 or streak == 6:
            if not hasattr(character, 'rainbow_shards'):
                character.rainbow_shards = 0
            character.rainbow_shards += 1
            from handlers.rainbow import add_rainbow_shard
            add_rainbow_shard(character, "daily_login")
        
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
        
        daily_text = f"🎁 *Ежедневная награда!*\nДень {streak}\n"
        daily_text += f"💰 +{reward['gold']} золота\n"
        if reward.get("dstn"):
            daily_text += f"💎 +{reward['dstn']} DSTN\n"
        if streak == 3 or streak == 6:
            daily_text += f"🌈 +1 радужный осколок\n"
        
        bot.send_message(
            message.chat.id,
            daily_text,
            parse_mode='Markdown'
        )

    # СОЗДАЁМ КНОПКУ С WEBAPP
    markup = InlineKeyboardMarkup()
    
    # Главная кнопка для открытия игры
    webapp_button = InlineKeyboardButton(
        text="🎮 ОТКРЫТЬ ИГРУ",
        web_app=WebAppInfo(url="https://destiny-web.onrender.com/")
    )
    markup.add(webapp_button)
    
    # Кнопка "Пойти в горы" - самая верхняя после игры
    markup.row(
        InlineKeyboardButton("⛰️ Пойти в горы", callback_data="game:goto_mountains")
    )
    
    # Дополнительные кнопки
    markup.row(
        InlineKeyboardButton("📊 Статус", callback_data="game:status"),
        InlineKeyboardButton("🗺️ Карта", callback_data="game:map")
    )
    markup.row(
        InlineKeyboardButton("🐾 Питомцы", callback_data="pets:menu"),
        InlineKeyboardButton("💱 Обмен", callback_data="exchange:menu")
    )
    markup.row(
        InlineKeyboardButton("🏠 Домик", callback_data="game:house"),
        InlineKeyboardButton("⚔️ PvP", callback_data="pvp:menu")
    )
    markup.row(
        InlineKeyboardButton("📜 Квесты", callback_data="quests:main"),
        InlineKeyboardButton("🔨 Крафт", callback_data="game:craft")
    )
    markup.row(
        InlineKeyboardButton("🌈 Радуга", callback_data="rainbow:menu"),
        InlineKeyboardButton("👑 Премиум", callback_data="premium:menu")
    )

    # Проверяем, есть ли у игрока класс
    if not character.player_class:
        text = f"👋 *Добро пожаловать, {first_name}!*\n\n"
        text += "🌟 *Выбери свой класс*, чтобы начать приключение!\n\n"
        text += "⚡ Энергия: {character.energy}/{character.max_energy}\n"
        text += "💰 Золото: {character.gold}\n"
        text += "💎 DSTN: {character.dstn or 0}\n"
        text += "❤️ Здоровье: {character.health}/{character.max_health}\n"
        text += "📈 Уровень: {character.level}\n\n"
        text += "📅 Стрик входа: {character.login_streak or 0} дней\n\n"
        text += "👇 Нажми кнопку ниже, чтобы выбрать класс!"
        
        # Добавляем кнопки классов
        from handlers.game import CLASSES
        class_markup = InlineKeyboardMarkup(row_width=3)
        class_buttons = []
        for class_id, class_info in CLASSES.items():
            class_buttons.append(InlineKeyboardButton(
                class_info['emoji'], 
                callback_data=f"game:class:{class_id}"
            ))
        
        for i in range(0, len(class_buttons), 3):
            class_markup.add(*class_buttons[i:i+3])
        
        class_markup.add(InlineKeyboardButton("🔙 Позже", callback_data="game:skip_class"))
        
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=class_markup,
            parse_mode='Markdown'
        )
    else:
        # Определяем, можно ли показать инвентарь в текущей локации
        from main import can_show_inventory
        show_inv = can_show_inventory(character.current_location or "start")
        
        text = f"👋 *С возвращением, {first_name}!*\n\n"
        text += f"⚡ Энергия: {character.energy}/{character.max_energy}\n"
        text += f"💰 Золото: {character.gold}\n"
        text += f"💎 DSTN: {character.dstn or 0}\n"
        text += f"❤️ Здоровье: {character.health}/{character.max_health}\n"
        text += f"📈 Уровень: {character.level}\n"
        if character.player_class:
            from handlers.game import CLASSES
            class_info = CLASSES.get(character.player_class, {})
            class_name = class_info.get('name', character.player_class)
            text += f"🎭 Класс: {class_name}\n"
        text += f"📅 Стрик входа: {character.login_streak or 0} дней\n"
        
        # Показываем радужные ресурсы
        if hasattr(character, 'rainbow_shards') and character.rainbow_shards:
            text += f"🌈 Осколков: {character.rainbow_shards}\n"
        if hasattr(character, 'rainbow_stones') and character.rainbow_stones:
            text += f"💎 Радужных камней: {character.rainbow_stones}\n"
        
        text += f"\n📍 Ты в локации: {character.current_location or 'start'}\n\n"
        text += f"👇 Нажми кнопку ниже, чтобы продолжить игру!"
        
        # Добавляем кнопку инвентаря только если можно
        if show_inv:
            markup.row(
                InlineKeyboardButton("🎒 Инвентарь", callback_data="game:inventory")
            )
        
        bot.send_message(
            message.chat.id,
            text,
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
    text += "/location - локация\n"
    text += "/map - карта мира\n\n"
    text += "⚔️ *Боевые:*\n"
    text += "/class - выбор класса\n"
    text += "/attack - атаковать врага\n"
    text += "/pvp - PvP арена\n\n"
    text += "🏠 *Домик:*\n"
    text += "/house - домик\n"
    text += "/craft - крафт\n\n"
    text += "🐾 *Питомцы:*\n"
    text += "/pets - питомцы\n\n"
    text += "📜 *Квесты:*\n"
    text += "/quests - квесты\n\n"
    text += "👥 *Социальное:*\n"
    text += "/guild - гильдия\n"
    text += "/top - рейтинги\n\n"
    text += "📚 *Информация:*\n"
    text += "/codex - энциклопедия\n"
    text += "/events - ивенты\n\n"
    text += "💎 *Премиум:*\n"
    text += "/premium - подписка\n"
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
            # Обновляем локацию персонажа
            from main import get_or_create_player, save_character
            user_id = call.from_user.id
            user, character = get_or_create_player(user_id)
            character.current_location = location
            save_character(character)
            
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
            
        elif action == 'combat_result':
            result = data.get('result')
            exp = data.get('exp', 0)
            gold = data.get('gold', 0)
            
            from main import get_or_create_player, save_character
            user_id = call.from_user.id
            user, character = get_or_create_player(user_id)
            
            if result == 'win':
                character.experience += exp
                character.gold += gold
                save_character(character)
                
                bot.send_message(
                    call.message.chat.id,
                    f"⚔️ *Победа!*\n✨ +{exp} опыта\n💰 +{gold} золота",
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    call.message.chat.id,
                    f"💀 *Поражение...*\nТы пал в бою, но воскреснешь!",
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
