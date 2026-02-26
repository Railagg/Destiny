# /bot/handlers/pvp.py
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import random
import time
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ PVP
# ============================================

PVP_ARENAS = {
    "training": {
        "name": "🏟️ Тренировочная арена",
        "description": "Бесплатные тренировки без риска",
        "entry_fee": 0,
        "min_level": 1,
        "exp_reward": 10,
        "rating_change": 0
    },
    "basic": {
        "name": "⚔️ Арена новичков",
        "description": "Для бойцов до 20 уровня",
        "entry_fee": 100,
        "min_level": 5,
        "max_level": 20,
        "exp_reward": 50,
        "rating_change": 10
    },
    "advanced": {
        "name": "🔥 Арена воинов",
        "description": "Для опытных бойцов 20-40 уровня",
        "entry_fee": 500,
        "min_level": 20,
        "max_level": 40,
        "exp_reward": 150,
        "rating_change": 20
    },
    "elite": {
        "name": "👑 Элитная арена",
        "description": "Для лучших из лучших 40+ уровня",
        "entry_fee": 2000,
        "min_level": 40,
        "exp_reward": 500,
        "rating_change": 30
    },
    "legendary": {
        "name": "🌟 Легендарная арена",
        "description": "Только для чемпионов",
        "entry_fee": 10000,
        "min_level": 60,
        "exp_reward": 2000,
        "rating_change": 50,
        "requires_premium": True
    }
}

PVP_REWARDS = {
    "win": {
        "gold": 100,
        "exp": 50,
        "rating": 10,
        "tokens": 5
    },
    "loss": {
        "gold": 20,
        "exp": 10,
        "rating": -5,
        "tokens": 1
    },
    "draw": {
        "gold": 50,
        "exp": 25,
        "rating": 0,
        "tokens": 2
    },
    "streak": {
        "3": {"bonus": 50, "title": "🔥 Начинающий боец"},
        "5": {"bonus": 100, "title": "⚡ Опытный воин"},
        "10": {"bonus": 200, "title": "👑 Непобедимый"},
        "20": {"bonus": 500, "title": "🌟 Легенда арены"}
    }
}

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

def pvp_command(message, bot_instance, get_or_create_player_func):
    """Команда /pvp - PvP арена"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    pvp_rating = getattr(character, 'pvp_rating', 1000)
    pvp_wins = getattr(character, 'pvp_wins', 0)
    pvp_losses = getattr(character, 'pvp_losses', 0)
    pvp_streak = getattr(character, 'pvp_streak', 0)
    
    text = "⚔️ *PvP АРЕНА*\n\n"
    
    text += f"📊 *Твоя статистика:*\n"
    text += f"🏆 Рейтинг: {pvp_rating}\n"
    text += f"✅ Побед: {pvp_wins}\n"
    text += f"❌ Поражений: {pvp_losses}\n"
    text += f"🔥 Текущая серия: {pvp_streak}\n\n"
    
    text += "🎯 *Доступные арены:*\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    for arena_id, arena in PVP_ARENAS.items():
        if character.level >= arena['min_level']:
            if 'max_level' in arena and character.level > arena['max_level']:
                continue
            
            text += f"• {arena['name']} (ур. {arena['min_level']}+)\n"
            text += f"  {arena['description']}\n"
            text += f"  Взнос: {arena['entry_fee']}💰\n\n"
            
            markup.add(InlineKeyboardButton(
                arena['name'],
                callback_data=f"pvp:arena:{arena_id}"
            ))
    
    markup.add(InlineKeyboardButton("🏆 Рейтинг", callback_data="pvp:rating"))
    markup.add(InlineKeyboardButton("📜 История", callback_data="pvp:history"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def pvp_fight_command(message, bot_instance, get_or_create_player_func):
    """Команда /pvp_fight - начать PvP бой"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    args = message.text.split()
    if len(args) < 2:
        bot_instance.send_message(
            message.chat.id,
            "❌ Укажи ID арены!\n"
            "Пример: /pvp_fight basic\n"
            "Доступные арены: training, basic, advanced, elite, legendary",
            parse_mode='Markdown'
        )
        return
    
    arena_id = args[1].lower()
    
    if arena_id not in PVP_ARENAS:
        bot_instance.send_message(
            message.chat.id,
            "❌ Арена не найдена!",
            parse_mode='Markdown'
        )
        return
    
    arena = PVP_ARENAS[arena_id]
    
    # Проверяем уровень
    if character.level < arena['min_level']:
        bot_instance.send_message(
            message.chat.id,
            f"❌ Нужен уровень {arena['min_level']}+ для этой арены!",
            parse_mode='Markdown'
        )
        return
    
    if 'max_level' in arena and character.level > arena['max_level']:
        bot_instance.send_message(
            message.chat.id,
            f"❌ Максимальный уровень для этой арены: {arena['max_level']}!",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем золото
    if character.gold < arena['entry_fee']:
        bot_instance.send_message(
            message.chat.id,
            f"❌ Нужно {arena['entry_fee']} золота для входа!",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем энергию
    if character.energy < 10:
        bot_instance.send_message(
            message.chat.id,
            "❌ Нужно 10 энергии для боя!",
            parse_mode='Markdown'
        )
        return
    
    # Ищем противника
    start_pvp_battle(message, bot_instance, character, arena_id, arena)

def pvp_arena_command(message, bot_instance, get_or_create_player_func):
    """Команда /pvp_arena - информация об аренах"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "🏟️ *ИНФОРМАЦИЯ ОБ АРЕНАХ*\n\n"
    
    for arena_id, arena in PVP_ARENAS.items():
        text += f"*{arena['name']}*\n"
        text += f"📝 {arena['description']}\n"
        text += f"📊 Требуемый уровень: {arena['min_level']}"
        if 'max_level' in arena:
            text += f" - {arena['max_level']}"
        text += f"\n💰 Взнос: {arena['entry_fee']} золота\n"
        text += f"✨ Награда за победу: {arena['exp_reward']} опыта, +{arena['rating_change']} рейтинга\n\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pvp:menu"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# ФУНКЦИИ БОЯ
# ============================================

def start_pvp_battle(message, bot_instance, character, arena_id, arena):
    """Начать PvP бой"""
    user_id = message.from_user.id
    
    # Сохраняем состояние боя
    if not hasattr(bot_instance, "pvp_battles"):
        bot_instance.pvp_battles = {}
    
    # Платим взнос
    character.gold -= arena['entry_fee']
    character.energy -= 10
    
    from main import save_character
    save_character(character)
    
    # Ищем противника
    opponent = find_opponent(character, arena_id)
    
    if opponent:
        # Начинаем бой
        battle_id = f"{user_id}_{int(time.time())}"
        
        battle_state = {
            "battle_id": battle_id,
            "arena_id": arena_id,
            "player1": {
                "id": user_id,
                "name": message.from_user.first_name or f"Игрок {user_id}",
                "hp": character.health,
                "max_hp": character.max_health,
                "damage": calculate_pvp_damage(character),
                "defense": calculate_pvp_defense(character),
                "crit_chance": getattr(character, 'crit_chance', 5),
                "dodge_chance": getattr(character, 'dodge_chance', 5)
            },
            "player2": opponent,
            "turn": 1,
            "log": []
        }
        
        bot_instance.pvp_battles[battle_id] = battle_state
        
        show_pvp_battle_start(message, bot_instance, battle_state)
    else:
        # Встаём в очередь
        if not hasattr(bot_instance, "pvp_queue"):
            bot_instance.pvp_queue = {}
        
        if arena_id not in bot_instance.pvp_queue:
            bot_instance.pvp_queue[arena_id] = []
        
        queue_time = int(time.time())
        bot_instance.pvp_queue[arena_id].append({
            "user_id": user_id,
            "name": message.from_user.first_name or f"Игрок {user_id}",
            "character": character,
            "queue_time": queue_time,
            "message": message
        })
        
        bot_instance.send_message(
            message.chat.id,
            f"⏳ Ищем противника на арене {arena['name']}...\n"
            f"Ты в очереди. Как только найдём противника, бой начнётся автоматически.",
            parse_mode='Markdown'
        )

def find_opponent(character, arena_id):
    """Найти противника в очереди"""
    from main import get_or_create_player
    
    # Здесь должна быть логика поиска по базе данных
    # Пока возвращаем заглушку
    return {
        "id": 12345,
        "name": "Тестовый противник",
        "hp": 100,
        "max_hp": 100,
        "damage": 15,
        "defense": 5,
        "crit_chance": 5,
        "dodge_chance": 5
    }

def show_pvp_battle_start(message, bot_instance, battle_state):
    """Показать начало PvP боя"""
    p1 = battle_state['player1']
    p2 = battle_state['player2']
    
    text = f"⚔️ *PvP БИТВА*\n\n"
    text += f"🏟️ Арена: {PVP_ARENAS[battle_state['arena_id']]['name']}\n\n"
    
    text += f"👤 *{p1['name']}*\n"
    text += f"❤️ HP: {p1['hp']}/{p1['max_hp']}\n"
    text += f"⚔️ Урон: {p1['damage']}\n\n"
    
    text += f"VS\n\n"
    
    text += f"👤 *{p2['name']}*\n"
    text += f"❤️ HP: {p2['hp']}/{p2['max_hp']}\n"
    text += f"⚔️ Урон: {p2['damage']}\n\n"
    
    text += f"Ход {battle_state['turn']}"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⚔️ Атаковать", callback_data=f"pvp:attack:{battle_state['battle_id']}"),
        InlineKeyboardButton("🛡️ Защита", callback_data=f"pvp:defend:{battle_state['battle_id']}")
    )
    markup.add(
        InlineKeyboardButton("✨ Умение", callback_data=f"pvp:skill:{battle_state['battle_id']}"),
        InlineKeyboardButton("🏃 Сдаться", callback_data=f"pvp:surrender:{battle_state['battle_id']}")
    )
    
    bot_instance.send_message(
        message.chat.id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def pvp_attack(call, bot_instance, battle_id, player_id):
    """Обработка атаки в PvP"""
    if not hasattr(bot_instance, "pvp_battles") or battle_id not in bot_instance.pvp_battles:
        bot_instance.answer_callback_query(call.id, "❌ Бой не найден!")
        return
    
    battle = bot_instance.pvp_battles[battle_id]
    
    # Определяем, кто атакует
    if battle['player1']['id'] == player_id:
        attacker = battle['player1']
        defender = battle['player2']
    else:
        attacker = battle['player2']
        defender = battle['player1']
    
    # Рассчитываем урон
    damage = attacker['damage']
    
    # Проверка на крит
    if random.randint(1, 100) <= attacker['crit_chance']:
        damage = int(damage * 1.5)
        battle['log'].append(f"⚡ КРИТ!")
    
    # Проверка на уклонение
    if random.randint(1, 100) <= defender['dodge_chance']:
        battle['log'].append(f"💨 Противник уклонился!")
        damage = 0
    
    # Защита
    if battle.get('defending') == defender['id']:
        damage = int(damage * 0.5)
        battle['log'].append(f"🛡️ Защита уменьшила урон!")
        battle['defending'] = None
    
    # Наносим урон
    defender['hp'] -= max(1, damage)
    battle['log'].append(f"⚔️ {attacker['name']} нанёс {damage} урона!")
    
    # Проверка на победу
    if defender['hp'] <= 0:
        end_pvp_battle(call, bot_instance, battle, attacker['id'], defender['id'])
        return
    
    # Меняем ход
    battle['turn'] += 1
    bot_instance.pvp_battles[battle_id] = battle
    
    # Обновляем сообщение
    update_pvp_battle(call, bot_instance, battle)

def pvp_defend(call, bot_instance, battle_id, player_id):
    """Обработка защиты в PvP"""
    if not hasattr(bot_instance, "pvp_battles") or battle_id not in bot_instance.pvp_battles:
        bot_instance.answer_callback_query(call.id, "❌ Бой не найден!")
        return
    
    battle = bot_instance.pvp_battles[battle_id]
    battle['defending'] = player_id
    battle['log'].append(f"🛡️ {get_player_name(battle, player_id)} готовится к защите!")
    
    # Меняем ход
    battle['turn'] += 1
    bot_instance.pvp_battles[battle_id] = battle
    
    update_pvp_battle(call, bot_instance, battle)

def pvp_skill(call, bot_instance, battle_id, player_id):
    """Использование умения в PvP"""
    bot_instance.answer_callback_query(call.id, "⏳ Умения в разработке")

def pvp_surrender(call, bot_instance, battle_id, player_id):
    """Сдаться в PvP"""
    if not hasattr(bot_instance, "pvp_battles") or battle_id not in bot_instance.pvp_battles:
        bot_instance.answer_callback_query(call.id, "❌ Бой не найден!")
        return
    
    battle = bot_instance.pvp_battles[battle_id]
    
    # Определяем победителя
    if battle['player1']['id'] == player_id:
        winner_id = battle['player2']['id']
        loser_id = player_id
    else:
        winner_id = battle['player1']['id']
        loser_id = player_id
    
    end_pvp_battle(call, bot_instance, battle, winner_id, loser_id, surrendered=True)

def update_pvp_battle(call, bot_instance, battle):
    """Обновить сообщение с боем"""
    p1 = battle['player1']
    p2 = battle['player2']
    
    text = f"⚔️ *PvP БИТВА*\n\n"
    text += f"🏟️ Арена: {PVP_ARENAS[battle['arena_id']]['name']}\n\n"
    
    text += f"👤 *{p1['name']}*\n"
    text += f"❤️ HP: {p1['hp']}/{p1['max_hp']}\n\n"
    
    text += f"VS\n\n"
    
    text += f"👤 *{p2['name']}*\n"
    text += f"❤️ HP: {p2['hp']}/{p2['max_hp']}\n\n"
    
    text += f"📜 *Лог боя:*\n"
    for log in battle['log'][-3:]:
        text += f"• {log}\n"
    
    text += f"\nХод {battle['turn']}"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⚔️ Атаковать", callback_data=f"pvp:attack:{battle['battle_id']}"),
        InlineKeyboardButton("🛡️ Защита", callback_data=f"pvp:defend:{battle['battle_id']}")
    )
    markup.add(
        InlineKeyboardButton("✨ Умение", callback_data=f"pvp:skill:{battle['battle_id']}"),
        InlineKeyboardButton("🏃 Сдаться", callback_data=f"pvp:surrender:{battle['battle_id']}")
    )
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def end_pvp_battle(call, bot_instance, battle, winner_id, loser_id, surrendered=False):
    """Завершить PvP бой"""
    from main import save_character, get_or_create_player
    
    arena = PVP_ARENAS[battle['arena_id']]
    
    # Получаем игроков
    winner_user, winner_char = get_or_create_player_func(call.from_user.id if winner_id == call.from_user.id else winner_id)
    loser_user, loser_char = get_or_create_player_func(call.from_user.id if loser_id == call.from_user.id else loser_id)
    
    # Награда победителю
    winner_char.gold += arena['entry_fee'] * 2
    winner_char.experience += arena['exp_reward']
    winner_char.pvp_wins = getattr(winner_char, 'pvp_wins', 0) + 1
    winner_char.pvp_rating = getattr(winner_char, 'pvp_rating', 1000) + arena['rating_change']
    winner_char.pvp_streak = getattr(winner_char, 'pvp_streak', 0) + 1
    
    # Штраф проигравшему
    if not surrendered:
        loser_char.pvp_losses = getattr(loser_char, 'pvp_losses', 0) + 1
        loser_char.pvp_rating = getattr(loser_char, 'pvp_rating', 1000) - arena['rating_change'] // 2
        loser_char.pvp_streak = 0
    
    save_character(winner_char)
    save_character(loser_char)
    
    # Удаляем бой
    del bot_instance.pvp_battles[battle['battle_id']]
    
    # Показываем результат
    text = f"🎉 *БОЙ ЗАВЕРШЁН!*\n\n"
    
    if winner_id == call.from_user.id:
        text += f"✅ *ТЫ ПОБЕДИЛ!*\n\n"
        text += f"💰 Получено: {arena['entry_fee'] * 2} золота\n"
        text += f"✨ Получено: {arena['exp_reward']} опыта\n"
        text += f"🏆 Рейтинг: +{arena['rating_change']}\n"
    else:
        text += f"❌ *ТЫ ПРОИГРАЛ!*\n\n"
        if surrendered:
            text += f"Ты сдался...\n\n"
        text += f"💰 Получено: 0 золота\n"
        text += f"✨ Получено: {arena['exp_reward'] // 4} опыта\n"
        text += f"🏆 Рейтинг: -{arena['rating_change'] // 2}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⚔️ На арену", callback_data="pvp:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def get_player_name(battle, player_id):
    """Получить имя игрока по ID"""
    if battle['player1']['id'] == player_id:
        return battle['player1']['name']
    return battle['player2']['name']

def calculate_pvp_damage(character):
    """Рассчитать PvP урон"""
    base_damage = character.strength * 2 + character.level * 2
    
    # Бонус от экипировки
    from main import items_data
    if character.equipped_weapon:
        weapon = items_data.get("items", {}).get(character.equipped_weapon, {})
        base_damage += weapon.get("damage", 0)
    
    return base_damage

def calculate_pvp_defense(character):
    """Рассчитать PvP защиту"""
    base_defense = character.vitality * 2 + character.level
    
    # Бонус от экипировки
    from main import items_data
    if character.equipped_armor:
        armor = items_data.get("items", {}).get(character.equipped_armor, {})
        base_defense += armor.get("defense", 0)
    
    return base_defense

# ============================================
# РЕЙТИНГ И ИСТОРИЯ
# ============================================

def show_pvp_rating(call, bot_instance):
    """Показать рейтинг PvP"""
    # Здесь должен быть запрос к БД
    text = "🏆 *ТОП PvP РЕЙТИНГ*\n\n"
    
    text += "1. Игрок1 — 2850 рейтинга (152 побед)\n"
    text += "2. Игрок2 — 2740 рейтинга (143 побед)\n"
    text += "3. Игрок3 — 2630 рейтинга (134 побед)\n"
    text += "4. Игрок4 — 2520 рейтинга (125 побед)\n"
    text += "5. Игрок5 — 2410 рейтинга (116 побед)\n"
    text += "6. Игрок6 — 2300 рейтинга (107 побед)\n"
    text += "7. Игрок7 — 2190 рейтинга (98 побед)\n"
    text += "8. Игрок8 — 2080 рейтинга (89 побед)\n"
    text += "9. Игрок9 — 1970 рейтинга (80 побед)\n"
    text += "10. Игрок10 — 1860 рейтинга (71 побед)"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pvp:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_pvp_history(call, bot_instance, character):
    """Показать историю PvP боёв"""
    history = getattr(character, 'pvp_history', [])
    
    text = "📜 *ИСТОРИЯ PvP БОЁВ*\n\n"
    
    if not history:
        text += "У тебя пока нет PvP боёв."
    else:
        for battle in history[-10:]:
            result = "✅" if battle.get('win') else "❌"
            arena = battle.get('arena', 'Неизвестно')
            opponent = battle.get('opponent', 'Неизвестно')
            rating = battle.get('rating_change', 0)
            time_str = battle.get('time', '')
            
            text += f"{result} {arena}: {opponent} "
            if rating > 0:
                text += f"(+{rating})\n"
            else:
                text += f"({rating})\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="pvp:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func):
    """Обработка кнопок PvP"""
    from main import save_character
    
    parts = call.data.split(':')
    action = parts[1] if len(parts) > 1 else "menu"
    
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    if action == "menu":
        pvp_command(call.message, bot_instance, get_or_create_player_func)
    
    elif action == "arena" and len(parts) > 2:
        arena_id = parts[2]
        start_pvp_battle(call.message, bot_instance, character, arena_id, PVP_ARENAS[arena_id])
    
    elif action == "rating":
        show_pvp_rating(call, bot_instance)
    
    elif action == "history":
        show_pvp_history(call, bot_instance, character)
    
    elif action == "attack" and len(parts) > 2:
        battle_id = parts[2]
        pvp_attack(call, bot_instance, battle_id, user_id)
    
    elif action == "defend" and len(parts) > 2:
        battle_id = parts[2]
        pvp_defend(call, bot_instance, battle_id, user_id)
    
    elif action == "skill" and len(parts) > 2:
        battle_id = parts[2]
        pvp_skill(call, bot_instance, battle_id, user_id)
    
    elif action == "surrender" and len(parts) > 2:
        battle_id = parts[2]
        pvp_surrender(call, bot_instance, battle_id, user_id)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ В разработке")

# ============================================
# ФУНКЦИИ ДЛЯ СОВМЕСТИМОСТИ С __init__.py
# ============================================

def pvp_fight_command(message, bot_instance, get_or_create_player_func):
    """Команда /pvp_fight - начать PvP бой"""
    pvp_fight_command(message, bot_instance, get_or_create_player_func)

def pvp_arena_command(message, bot_instance, get_or_create_player_func):
    """Команда /pvp_arena - информация об аренах"""
    pvp_arena_command(message, bot_instance, get_or_create_player_func)

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'pvp_command',
    'pvp_fight_command',
    'pvp_arena_command',
    'handle_callback'
]
