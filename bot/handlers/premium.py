import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
from datetime import datetime, timedelta
import time

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ ПРЕМИУМ-СИСТЕМЫ
# ============================================

PREMIUM_COLORS = {
    "7days": "🟢",
    "28days": "🔵", 
    "90days": "🟣",
    "180days": "🟡",
    "365days": "🔴"
}

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

def premium_command(message, bot_instance, get_or_create_player_func, premium_data):
    """Команда /premium - премиум-подписка"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    plans = premium_data.get("premium", {}).get("plans", {})
    
    # Проверяем текущий статус
    premium_status = get_premium_status(character)
    
    text = "👑 *PREMIUM DESTINY*\n\n"
    
    if premium_status['active']:
        text += f"✅ *Премиум активен*\n"
        text += f"📅 План: {premium_status['plan_name']}\n"
        text += f"⏳ Осталось: {premium_status['days_left']} дней\n\n"
    else:
        text += "Премиум-подписка даёт невероятные бонусы!\n\n"
    
    # Таблица сравнения
    text += "📊 *СРАВНЕНИЕ ПЛАНОВ*\n\n"
    text += "│ План │ Энергия │💰 Золото│✨ Опыт│ 🎁 │\n"
    text += "├──────┼─────────┼─────────┼───────┼─────┤\n"
    
    for plan_id, plan in plans.items():
        color = PREMIUM_COLORS.get(plan_id, "⚪")
        bonuses = plan.get('bonuses', {})
        energy = bonuses.get('max_energy', 100)
        gold = int((bonuses.get('gold_multiplier', 1) - 1) * 100)
        exp = int((bonuses.get('exp_multiplier', 1) - 1) * 100)
        chests = bonuses.get('chests_per_day', 0)
        
        text += f"│{color} {plan_id[:2]}│ {energy} │ +{gold}% │ +{exp}% │ +{chests} │\n"
    
    text += "\n✨ *Преимущества:*\n"
    text += "• ⚡ Больше энергии\n"
    text += "• 💰 Больше золота и опыта\n"
    text += "• 🎁 Дополнительные сундуки\n"
    text += "• 🏠 Улучшенный отдых в доме\n"
    text += "• 💱 Лучший курс в обменнике\n"
    text += "• 🌈 Доступ к радужному магазину\n"
    text += "• 🐾 Бонусы для питомцев\n\n"
    
    text += "🎁 *Подарок при покупке:* легендарный сундук!\n"
    text += "💎 *Первая покупка:* скидка 50% на Stars, 25% на TON!"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Кнопки планов
    for plan_id, plan in plans.items():
        color = PREMIUM_COLORS.get(plan_id, "⚪")
        name = plan.get('name', plan_id)
        price = plan.get('price_stars', 0)
        markup.add(InlineKeyboardButton(
            f"{color} {name} - {price}⭐",
            callback_data=f"premium:show:{plan_id}"
        ))
    
    markup.add(
        InlineKeyboardButton("ℹ️ О премиуме", callback_data="premium:info"),
        InlineKeyboardButton("📊 Мой статус", callback_data="premium:status"),
        InlineKeyboardButton("🏆 Награды за верность", callback_data="premium:renewal"),
        InlineKeyboardButton("🌈 Радужный магазин", callback_data="rainbow:shop")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_plan(call, bot_instance, character, plan_id, premium_data):
    """Показать детали плана"""
    plans = premium_data.get("premium", {}).get("plans", {})
    plan = plans.get(plan_id)
    
    if not plan:
        bot_instance.answer_callback_query(call.id, "❌ План не найден")
        return
    
    first_purchase = premium_data.get("premium", {}).get("first_purchase_bonus", {})
    ton_discount = premium_data.get("premium", {}).get("ton_discount", {})
    
    color = PREMIUM_COLORS.get(plan_id, "⚪")
    
    text = f"{color} *{plan.get('name')}*\n\n"
    text += f"📅 Длительность: {plan.get('duration')} дней\n\n"
    
    text += "✨ *Бонусы:*\n"
    bonuses = plan.get('bonuses', {})
    
    # Основные бонусы
    text += f"• ⚡ Макс. энергия: {bonuses.get('max_energy', 100)}\n"
    text += f"• 💰 Золото: +{int((bonuses.get('gold_multiplier', 1)-1)*100)}%\n"
    text += f"• ✨ Опыт: +{int((bonuses.get('exp_multiplier', 1)-1)*100)}%\n"
    text += f"• 🎁 Сундуков в день: +{bonuses.get('chests_per_day', 0)}\n"
    text += f"• 📦 Слотов инвентаря: +{bonuses.get('inventory_slots', 0)}\n"
    text += f"• 🏠 Отдых в доме: x{bonuses.get('house_rest_multiplier', 1)}\n"
    
    # Дополнительные бонусы
    if bonuses.get('shop_discount'):
        text += f"• 🏪 Скидка в магазине: {bonuses.get('shop_discount')}%\n"
    if bonuses.get('rainbow_shard_weekly'):
        text += f"• 🌈 Радужных осколков в неделю: +{bonuses.get('rainbow_shard_weekly')}\n"
    if bonuses.get('premium_chest_daily'):
        text += f"• 🎁 Премиум-сундук каждый день\n"
    if bonuses.get('exchange_bonus'):
        exchange = bonuses.get('exchange_bonus', {})
        text += f"• 💱 Курс обмена: {exchange.get('ton_to_dstn', 2500)} TON→DSTN\n"
        if exchange.get('fee_free'):
            text += f"• 💸 Без комиссии за обмен\n"
    
    text += f"\n💰 *Цены:*\n"
    text += f"• Stars: {plan.get('price_stars')} ⭐"
    
    # Учитываем первую покупку
    if first_purchase.get('enabled') and plan_id in first_purchase.get('applicable_plans', []):
        text += f" (первая покупка: {first_purchase.get('stars_discount')}% скидка!)"
    text += f"\n"
    
    text += f"• TON: {plan.get('price_ton')} 💎"
    if ton_discount.get('enabled'):
        text += f" (постоянная скидка {ton_discount.get('discount_percent')}%)"
    text += f"\n"
    
    if plan.get('price_dstn'):
        text += f"• DSTN: {plan.get('price_dstn')} 💫\n"
    
    text += f"\n🎁 *Подарок:*\n"
    gift = plan.get('gift', {})
    if gift.get('legendary_chest'):
        text += f"• {gift.get('legendary_chest')} легендарных сундуков\n"
    if gift.get('dstn'):
        text += f"• {gift.get('dstn')} DSTN\n"
    if gift.get('gold'):
        text += f"• {gift.get('gold')} золота\n"
    if gift.get('pet'):
        text += f"• 🐾 Особый питомец: {gift.get('pet')}\n"
    if gift.get('skin'):
        text += f"• ✨ Особый скин\n"
    if gift.get('title'):
        text += f"• 👑 Титул: {gift.get('title')}\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💎 Купить за Stars", callback_data=f"premium:buy_stars:{plan_id}"),
        InlineKeyboardButton("💎 Купить за TON", callback_data=f"premium:buy_ton:{plan_id}")
    )
    if plan.get('price_dstn'):
        markup.add(InlineKeyboardButton("💫 Купить за DSTN", callback_data=f"premium:buy_dstn:{plan_id}"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="premium:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_info(call, bot_instance):
    """Показать информацию о премиуме"""
    text = "ℹ️ *О ПРЕМИУМ-ПОДПИСКЕ*\n\n"
    
    text += "🌟 *Что даёт премиум:*\n\n"
    
    text += "⚡ *Энергия*\n"
    text += "• Увеличенный запас энергии (до 250)\n"
    text += "• Больше действий за день\n\n"
    
    text += "💰 *Ресурсы*\n"
    text += "• +30% к золоту и опыту\n"
    text += "• Дополнительные сундуки каждый день\n"
    text += "• Лучший курс в обменнике\n\n"
    
    text += "🏠 *Дом*\n"
    text += "• Улучшенный отдых (до x2.5)\n"
    text += "• Дополнительные слоты в инвентаре\n\n"
    
    text += "🌈 *Радужные камни*\n"
    text += "• Доступ к магазину радужных камней\n"
    text += "• Еженедельные радужные осколки\n"
    text += "• Скидки на покупку камней\n\n"
    
    text += "🐾 *Питомцы*\n"
    text += "• Ускоренный рост питомцев\n"
    text += "• Дополнительное счастье\n\n"
    
    text += "🎁 *Подарки*\n"
    text += "• Легендарные сундуки при покупке\n"
    text += "• Особые питомцы и скины\n"
    text += "• Уникальные титулы\n\n"
    
    text += "🏆 *Награды за верность*\n"
    text += "• 3 месяца: титул 'Верный'\n"
    text += "• 6 месяцев: серебряная рамка\n"
    text += "• 1 год: золотая рамка и аура\n"
    text += "• 2 года: платиновая рамка\n"
    text += "• 3 года: радужная рамка и титул 'Бог'\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="premium:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_status(call, bot_instance, character):
    """Показать статус премиума игрока"""
    premium_status = get_premium_status(character)
    
    text = "👑 *ТВОЙ ПРЕМИУМ СТАТУС*\n\n"
    
    if premium_status['active']:
        text += f"✅ *Активен*\n"
        text += f"📅 План: {premium_status['plan_name']}\n"
        text += f"⏳ Истекает через: {premium_status['days_left']} дней\n"
        text += f"📊 Всего дней: {premium_status['total_days']}\n\n"
        
        # Активные бонусы
        text += "✨ *Твои бонусы:*\n"
        text += f"• ⚡ Энергия: {character.max_energy}\n"
        text += f"• 💰 Золото: +{int((premium_status['gold_mult']-1)*100)}%\n"
        text += f"• ✨ Опыт: +{int((premium_status['exp_mult']-1)*100)}%\n"
        text += f"• 🎁 Сундуков в день: +{premium_status['chests']}\n"
        
        if premium_status['rainbow_shard_weekly']:
            text += f"• 🌈 Осколков в неделю: +{premium_status['rainbow_shard_weekly']}\n"
        
        # Награды за верность
        renewal = get_renewal_bonuses(character)
        if renewal:
            text += f"\n🏆 *Награды за верность:*\n"
            for bonus in renewal:
                text += f"• {bonus}\n"
    else:
        text += "❌ *Премиум не активен*\n\n"
        text += "Купи подписку, чтобы получить:\n"
        text += "• ⚡ Больше энергии\n"
        text += "• 💰 Больше золота и опыта\n"
        text += "• 🎁 Дополнительные сундуки\n"
        text += "• 🏠 Улучшенный отдых\n"
        text += "• 🌈 Доступ к радужному магазину\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔙 Назад", callback_data="premium:menu"),
        InlineKeyboardButton("🏆 Награды", callback_data="premium:renewal")
    )
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_renewal_bonuses(call, bot_instance, character, premium_data):
    """Показать награды за продление"""
    renewal = premium_data.get("premium", {}).get("renewal_bonuses", {})
    
    # Получаем стаж игрока
    total_days = character.premium_total_days if hasattr(character, 'premium_total_days') else 0
    months = total_days // 30
    years = total_days // 365
    
    text = "🏆 *НАГРАДЫ ЗА ВЕРНОСТЬ*\n\n"
    text += f"📊 Твой стаж: {total_days} дней ({years} лет {months % 12} мес)\n\n"
    
    for bonus_id, bonus in renewal.items():
        req = bonus.get('requirement', '')
        reward = bonus.get('reward', {})
        
        # Проверяем, получено ли
        earned = hasattr(character, f'renewal_{bonus_id}') and getattr(character, f'renewal_{bonus_id}')
        
        status = "✅" if earned else "⏳"
        text += f"{status} *{bonus.get('name')}*\n"
        text += f"  {req}\n"
        
        rewards = []
        if reward.get('rainbow_shard'):
            rewards.append(f"{reward['rainbow_shard']}🌈")
        if reward.get('rainbow_stone'):
            rewards.append(f"{reward['rainbow_stone']}💎")
        if reward.get('legendary_chest'):
            rewards.append(f"{reward['legendary_chest']}🎁")
        if reward.get('title'):
            rewards.append(f"титул '{reward['title']}'")
        if reward.get('frame'):
            rewards.append("особая рамка")
        if reward.get('aura'):
            rewards.append("аура")
        
        if rewards:
            text += f"  🎁 Награда: {', '.join(rewards)}\n"
        text += "\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="premium:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def buy_premium(call, bot_instance, character, plan_id, payment_method, premium_data):
    """Купить премиум"""
    from main import save_character
    
    plans = premium_data.get("premium", {}).get("plans", {})
    plan = plans.get(plan_id)
    
    if not plan:
        bot_instance.answer_callback_query(call.id, "❌ План не найден")
        return
    
    first_purchase = premium_data.get("premium", {}).get("first_purchase_bonus", {})
    
    # Проверяем, первая ли покупка
    is_first = not hasattr(character, 'premium_first_purchase') or not character.premium_first_purchase
    
    price = plan.get(f'price_{payment_method}', 0)
    
    if payment_method == 'stars' and is_first and first_purchase.get('enabled'):
        if plan_id in first_purchase.get('applicable_plans', []):
            price = int(price * (100 - first_purchase.get('stars_discount', 0)) / 100)
    
    text = f"💎 *ПОКУПКА ПРЕМИУМА*\n\n"
    text += f"План: {plan.get('name')}\n"
    text += f"Способ оплаты: {payment_method.upper()}\n"
    text += f"Цена: {price} {payment_method.upper()}\n\n"
    
    if is_first and first_purchase.get('enabled'):
        text += f"🎉 *Первая покупка!*\n"
        text += f"Скидка {first_purchase.get('stars_discount')}% применена!\n\n"
    
    text += "Для оплаты используй команду /pay или обратись в поддержку.\n\n"
    text += "В разработке находится интеграция с платёжными системами."
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data=f"premium:show:{plan_id}"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def activate_premium(character, plan_id, duration_days, premium_data):
    """Активировать премиум (вызывается после успешной оплаты)"""
    from main import save_character
    
    plans = premium_data.get("premium", {}).get("plans", {})
    plan = plans.get(plan_id)
    
    if not plan:
        return False
    
    now = datetime.utcnow()
    
    # Обновляем или продлеваем подписку
    if character.premium_until and character.premium_until > now:
        character.premium_until += timedelta(days=duration_days)
    else:
        character.premium_until = now + timedelta(days=duration_days)
    
    character.premium_plan = plan_id
    character.premium_total_days = (character.premium_total_days or 0) + duration_days
    
    # Отмечаем первую покупку
    if not hasattr(character, 'premium_first_purchase') or not character.premium_first_purchase:
        character.premium_first_purchase = True
    
    # Применяем бонусы
    apply_premium_bonuses(character, plan)
    
    # Выдаём подарок
    gift = plan.get('gift', {})
    if gift.get('legendary_chest'):
        for _ in range(gift['legendary_chest']):
            character.add_item('legendary_chest_key')
    if gift.get('dstn'):
        character.dstn = (character.dstn or 0) + gift['dstn']
    if gift.get('gold'):
        character.gold += gift['gold']
    if gift.get('pet'):
        character.add_item(gift['pet'])
    if gift.get('title'):
        if not character.titles:
            character.titles = []
        character.titles.append(gift['title'])
    
    # Проверяем награды за верность
    check_renewal_bonuses(character, premium_data)
    
    save_character(character)
    return True

def apply_premium_bonuses(character, plan):
    """Применить бонусы премиума к персонажу"""
    bonuses = plan.get('bonuses', {})
    
    character.max_energy = bonuses.get('max_energy', character.max_energy)
    character.gold_multiplier = bonuses.get('gold_multiplier', 1.0)
    character.exp_multiplier = bonuses.get('exp_multiplier', 1.0)
    character.luck_bonus = bonuses.get('luck', 0)
    character.chests_per_day = bonuses.get('chests_per_day', 0)
    character.inventory_slots_bonus = bonuses.get('inventory_slots', 0)
    character.house_rest_multiplier = bonuses.get('house_rest_multiplier', 1.0)
    character.pet_exp_gain = bonuses.get('pet_exp_gain', 1.0)
    
    if bonuses.get('rainbow_shard_weekly'):
        character.rainbow_shard_weekly = bonuses['rainbow_shard_weekly']
    
    if bonuses.get('exchange_bonus'):
        character.exchange_bonus = bonuses['exchange_bonus']

def check_renewal_bonuses(character, premium_data):
    """Проверить и выдать награды за верность"""
    from main import save_character
    
    total_days = character.premium_total_days or 0
    renewal = premium_data.get("premium", {}).get("renewal_bonuses", {})
    
    bonuses_earned = []
    
    # 3 месяца
    if total_days >= 90 and not hasattr(character, 'renewal_3months'):
        character.renewal_3months = True
        reward = renewal.get('3months', {}).get('reward', {})
        apply_renewal_reward(character, reward)
        bonuses_earned.append("3 месяца")
    
    # 6 месяцев
    if total_days >= 180 and not hasattr(character, 'renewal_6months'):
        character.renewal_6months = True
        reward = renewal.get('6months', {}).get('reward', {})
        apply_renewal_reward(character, reward)
        bonuses_earned.append("6 месяцев")
    
    # 1 год
    if total_days >= 365 and not hasattr(character, 'renewal_1year'):
        character.renewal_1year = True
        reward = renewal.get('1year', {}).get('reward', {})
        apply_renewal_reward(character, reward)
        bonuses_earned.append("1 год")
    
    # 2 года
    if total_days >= 730 and not hasattr(character, 'renewal_2years'):
        character.renewal_2years = True
        reward = renewal.get('2years', {}).get('reward', {})
        apply_renewal_reward(character, reward)
        bonuses_earned.append("2 года")
    
    # 3 года
    if total_days >= 1095 and not hasattr(character, 'renewal_3years'):
        character.renewal_3years = True
        reward = renewal.get('3years', {}).get('reward', {})
        apply_renewal_reward(character, reward)
        bonuses_earned.append("3 года")
    
    if bonuses_earned:
        save_character(character)
    
    return bonuses_earned

def apply_renewal_reward(character, reward):
    """Применить награду за верность"""
    if reward.get('rainbow_shard'):
        character.rainbow_shards = (character.rainbow_shards or 0) + reward['rainbow_shard']
    
    if reward.get('rainbow_stone'):
        character.rainbow_stones = (character.rainbow_stones or 0) + reward['rainbow_stone']
    
    if reward.get('legendary_chest'):
        for _ in range(reward['legendary_chest']):
            character.add_item('legendary_chest_key')
    
    if reward.get('title'):
        if not character.titles:
            character.titles = []
        character.titles.append(reward['title'])
    
    if reward.get('frame'):
        character.profile_frame = reward['frame']
    
    if reward.get('aura'):
        character.profile_aura = reward['aura']

def get_premium_status(character):
    """Получить статус премиума"""
    now = datetime.utcnow()
    
    if hasattr(character, 'premium_until') and character.premium_until and character.premium_until > now:
        days_left = (character.premium_until - now).days
        hours_left = ((character.premium_until - now).seconds // 3600)
        
        # Получаем название плана
        plan_name = "Премиум"
        gold_mult = 1.0
        exp_mult = 1.0
        chests = 0
        rainbow_shard_weekly = 0
        
        if hasattr(character, 'premium_plan') and character.premium_plan:
            from main import premium_data
            plans = premium_data.get("premium", {}).get("plans", {})
            plan = plans.get(character.premium_plan, {})
            plan_name = plan.get('name', character.premium_plan)
            
            bonuses = plan.get('bonuses', {})
            gold_mult = bonuses.get('gold_multiplier', 1.0)
            exp_mult = bonuses.get('exp_multiplier', 1.0)
            chests = bonuses.get('chests_per_day', 0)
            rainbow_shard_weekly = bonuses.get('rainbow_shard_weekly', 0)
        
        return {
            'active': True,
            'plan_name': plan_name,
            'days_left': days_left,
            'hours_left': hours_left,
            'total_days': character.premium_total_days or 0,
            'gold_mult': gold_mult,
            'exp_mult': exp_mult,
            'chests': chests,
            'rainbow_shard_weekly': rainbow_shard_weekly
        }
    else:
        return {
            'active': False,
            'plan_name': None,
            'days_left': 0,
            'hours_left': 0,
            'total_days': character.premium_total_days or 0,
            'gold_mult': 1.0,
            'exp_mult': 1.0,
            'chests': 0,
            'rainbow_shard_weekly': 0
        }

def get_renewal_bonuses(character):
    """Получить список полученных наград за верность"""
    bonuses = []
    
    if hasattr(character, 'renewal_3months') and character.renewal_3months:
        bonuses.append("3 месяца: титул 'Верный'")
    if hasattr(character, 'renewal_6months') and character.renewal_6months:
        bonuses.append("6 месяцев: серебряная рамка")
    if hasattr(character, 'renewal_1year') and character.renewal_1year:
        bonuses.append("1 год: золотая рамка + аура")
    if hasattr(character, 'renewal_2years') and character.renewal_2years:
        bonuses.append("2 года: платиновая рамка")
    if hasattr(character, 'renewal_3years') and character.renewal_3years:
        bonuses.append("3 года: радужная рамка + титул 'Бог'")
    
    return bonuses

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func, premium_data):
    """Обработка кнопок премиума"""
    from main import save_character
    
    parts = call.data.split(':')
    action = parts[1] if len(parts) > 1 else "menu"
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if action == "menu":
        premium_command(call.message, bot_instance, get_or_create_player_func, premium_data)
    
    elif action.startswith("show:"):
        plan_id = action.split(':')[2]
        show_plan(call, bot_instance, character, plan_id, premium_data)
    
    elif action.startswith("buy_stars:"):
        plan_id = action.split(':')[2]
        buy_premium(call, bot_instance, character, plan_id, 'stars', premium_data)
    
    elif action.startswith("buy_ton:"):
        plan_id = action.split(':')[2]
        buy_premium(call, bot_instance, character, plan_id, 'ton', premium_data)
    
    elif action.startswith("buy_dstn:"):
        plan_id = action.split(':')[2]
        buy_premium(call, bot_instance, character, plan_id, 'dstn', premium_data)
    
    elif action == "info":
        show_info(call, bot_instance)
    
    elif action == "status":
        show_status(call, bot_instance, character)
    
    elif action == "renewal":
        show_renewal_bonuses(call, bot_instance, character, premium_data)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
