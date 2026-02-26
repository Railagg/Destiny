import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import random
import time
from datetime import datetime, timedelta

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ КВЕСТОВ
# ============================================

QUEST_TYPES = {
    "kill": "⚔️ Убить",
    "collect": "📦 Собрать",
    "reach_location": "📍 Достичь",
    "talk": "💬 Поговорить",
    "craft": "🔨 Скрафтить",
    "build_house": "🏠 Построить",
    "choose_class": "🎭 Выбрать класс"
}

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

def quests_command(message, bot_instance, get_or_create_player_func, quests_data):
    """Команда /quests - показать квесты"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    text = "📜 *Квесты*\n\n"
    
    # Активные квесты
    active_quests = character.active_quests or []
    
    if active_quests:
        text += "*📋 Активные квесты:*\n"
        for quest_id in active_quests[:3]:  # Показываем первые 3
            quest = find_quest(quest_id, quests_data)
            if quest:
                progress = character.quest_progress.get(quest_id, {}).get("progress", 0)
                target = get_quest_target(quest)
                text += f"• {quest.get('name', quest_id)}: {progress}/{target}\n"
        if len(active_quests) > 3:
            text += f"  ... и ещё {len(active_quests) - 3}\n"
        text += "\n"
    
    # Доступные квесты
    available_quests = get_available_quests(character, quests_data, active_quests)
    
    if available_quests:
        text += "*📌 Доступные квесты:*\n"
        for quest_id, quest in available_quests[:5]:
            text += f"• {quest.get('name', quest_id)}\n"
            text += f"  {quest.get('description', '')[:50]}...\n"
        text += "\n"
    
    # Статистика
    text += f"✅ Выполнено квестов: {character.completed_quests_count or 0}\n"
    text += f"⭐ Очки квестов: {character.quest_points or 0}"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📋 Активные", callback_data="quests:active"),
        InlineKeyboardButton("📌 Доступные", callback_data="quests:available"),
        InlineKeyboardButton("✅ Завершённые", callback_data="quests:completed"),
        InlineKeyboardButton("🏆 Ежедневные", callback_data="quests:daily"),
        InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start")
    )
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_active_quests(call, bot_instance, character, quests_data):
    """Показать активные квесты"""
    active_quests = character.active_quests or []
    
    if not active_quests:
        bot_instance.answer_callback_query(call.id, "❌ Нет активных квестов")
        return
    
    text = "📋 *Активные квесты*\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for quest_id in active_quests:
        quest = find_quest(quest_id, quests_data)
        if quest:
            progress = character.quest_progress.get(quest_id, {}).get("progress", 0)
            target = get_quest_target(quest)
            
            # Прогресс-бар
            progress_percent = int((progress / target) * 10)
            progress_bar = "█" * progress_percent + "░" * (10 - progress_percent)
            
            text += f"*{quest.get('name', quest_id)}*\n"
            text += f"{quest.get('description', '')}\n"
            text += f"Прогресс: {progress_bar} {progress}/{target}\n"
            text += f"Награда: {format_rewards(quest.get('rewards', {}))}\n\n"
            
            markup.add(InlineKeyboardButton(
                f"✅ {quest.get('name', quest_id)[:20]}",
                callback_data=f"quests:complete:{quest_id}"
            ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="quests:main"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_available_quests(call, bot_instance, character, quests_data):
    """Показать доступные квесты"""
    active_quests = character.active_quests or []
    available = get_available_quests(character, quests_data, active_quests)
    
    if not available:
        bot_instance.answer_callback_query(call.id, "❌ Нет доступных квестов")
        return
    
    text = "📌 *Доступные квесты*\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for quest_id, quest in available[:5]:
        text += f"*{quest.get('name', quest_id)}*\n"
        text += f"{quest.get('description', '')}\n"
        text += f"Требуемый уровень: {quest.get('level_req', 1)}\n"
        text += f"Награда: {format_rewards(quest.get('rewards', {}))}\n\n"
        
        markup.add(InlineKeyboardButton(
            f"📌 {quest.get('name', quest_id)[:20]}",
            callback_data=f"quests:take:{quest_id}"
        ))
    
    if len(available) > 5:
        text += f"... и ещё {len(available) - 5} квестов"
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="quests:main"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_completed_quests(call, bot_instance, character):
    """Показать завершённые квесты"""
    completed = character.completed_quests or []
    
    if not completed:
        bot_instance.answer_callback_query(call.id, "❌ Нет завершённых квестов")
        return
    
    text = "✅ *Завершённые квесты*\n\n"
    
    for quest_id in completed[-10:]:  # Последние 10
        text += f"• {quest_id}\n"
    
    text += f"\nВсего завершено: {len(completed)}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="quests:main"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_daily_quests(call, bot_instance, character, quests_data):
    """Показать ежедневные квесты"""
    from main import refresh_daily_quests
    
    # Обновляем ежедневные квесты, если нужно
    refresh_daily_quests(character)
    
    daily_quests = character.daily_quests or []
    
    if not daily_quests:
        # Создаём новые ежедневные квесты
        daily_quests = generate_daily_quests(character, quests_data)
        character.daily_quests = daily_quests
        from main import save_character
        save_character(character)
    
    text = "🏆 *Ежедневные квесты*\n\n"
    text += "Обновляются каждый день в 00:00 UTC\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for quest_id, quest_data in daily_quests.items():
        progress = quest_data.get("progress", 0)
        target = quest_data.get("target", 1)
        completed = quest_data.get("completed", False)
        
        status = "✅" if completed else "⏳"
        name = quest_data.get("name", quest_id)
        
        text += f"{status} *{name}*\n"
        if not completed:
            progress_percent = int((progress / target) * 10)
            progress_bar = "█" * progress_percent + "░" * (10 - progress_percent)
            text += f"Прогресс: {progress_bar} {progress}/{target}\n"
        
        rewards = quest_data.get("rewards", {})
        text += f"Награда: {format_rewards(rewards)}\n\n"
        
        if not completed and progress >= target:
            markup.add(InlineKeyboardButton(
                f"✅ Забрать: {name}",
                callback_data=f"quests:claim_daily:{quest_id}"
            ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="quests:main"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def take_quest(call, bot_instance, character, quest_id, quests_data):
    """Взять квест"""
    from main import save_character
    
    # Находим квест
    quest = find_quest(quest_id, quests_data)
    if not quest:
        bot_instance.answer_callback_query(call.id, "❌ Квест не найден")
        return
    
    # Проверяем уровень
    if character.level < quest.get("level_req", 1):
        bot_instance.answer_callback_query(
            call.id, 
            f"❌ Требуется уровень {quest.get('level_req', 1)}"
        )
        return
    
    # Проверяем, не взят ли уже
    active_quests = character.active_quests or []
    if quest_id in active_quests:
        bot_instance.answer_callback_query(call.id, "❌ Квест уже взят")
        return
    
    # Проверяем, не выполнен ли уже
    completed = character.completed_quests or []
    if quest_id in completed:
        bot_instance.answer_callback_query(call.id, "❌ Квест уже выполнен")
        return
    
    # Добавляем квест
    if not character.active_quests:
        character.active_quests = []
    character.active_quests.append(quest_id)
    
    # Инициализируем прогресс
    if not character.quest_progress:
        character.quest_progress = {}
    
    character.quest_progress[quest_id] = {
        "progress": 0,
        "started": datetime.utcnow().isoformat()
    }
    
    save_character(character)
    
    bot_instance.answer_callback_query(call.id, f"✅ Квест '{quest.get('name', quest_id)}' взят!")
    
    # Возвращаемся к списку доступных
    show_available_quests(call, bot_instance, character, quests_data)

def complete_quest(call, bot_instance, character, quest_id, quests_data):
    """Завершить квест (получить награду)"""
    from main import save_character
    
    # Находим квест
    quest = find_quest(quest_id, quests_data)
    if not quest:
        bot_instance.answer_callback_query(call.id, "❌ Квест не найден")
        return
    
    # Проверяем, активен ли квест
    active_quests = character.active_quests or []
    if quest_id not in active_quests:
        bot_instance.answer_callback_query(call.id, "❌ Квест не активен")
        return
    
    # Проверяем прогресс
    progress = character.quest_progress.get(quest_id, {}).get("progress", 0)
    target = get_quest_target(quest)
    
    if progress < target:
        bot_instance.answer_callback_query(
            call.id, 
            f"❌ Квест не выполнен: {progress}/{target}"
        )
        return
    
    # Выдаём награду
    rewards = quest.get("rewards", {})
    reward_text = give_rewards(character, rewards)
    
    # Удаляем из активных
    character.active_quests.remove(quest_id)
    
    # Добавляем в выполненные
    if not character.completed_quests:
        character.completed_quests = []
    character.completed_quests.append(quest_id)
    
    # Увеличиваем счётчик
    character.completed_quests_count = (character.completed_quests_count or 0) + 1
    
    # Добавляем очки квестов
    character.quest_points = (character.quest_points or 0) + 10
    
    save_character(character)
    
    bot_instance.answer_callback_query(
        call.id, 
        f"✅ Квест выполнен!\n{reward_text}"
    )
    
    # Возвращаемся к активным
    show_active_quests(call, bot_instance, character, quests_data)

def claim_daily_quest(call, bot_instance, character, quest_id):
    """Забрать награду за ежедневный квест"""
    from main import save_character
    
    daily_quests = character.daily_quests or {}
    
    if quest_id not in daily_quests:
        bot_instance.answer_callback_query(call.id, "❌ Квест не найден")
        return
    
    quest_data = daily_quests[quest_id]
    
    if quest_data.get("completed"):
        bot_instance.answer_callback_query(call.id, "❌ Награда уже получена")
        return
    
    if quest_data.get("progress", 0) < quest_data.get("target", 1):
        bot_instance.answer_callback_query(call.id, "❌ Квест не выполнен")
        return
    
    # Выдаём награду
    rewards = quest_data.get("rewards", {})
    reward_text = give_rewards(character, rewards)
    
    # Отмечаем как выполненный
    quest_data["completed"] = True
    character.daily_quests = daily_quests
    
    # Добавляем очки квестов
    character.quest_points = (character.quest_points or 0) + 5
    
    save_character(character)
    
    bot_instance.answer_callback_query(
        call.id, 
        f"✅ Награда получена!\n{reward_text}"
    )
    
    # Возвращаемся к ежедневным
    from main import quests_data
    show_daily_quests(call, bot_instance, character, quests_data)

def update_quest_progress(character, event_type, target_id=None, amount=1):
    """Обновить прогресс квестов (вызывается из других хендлеров)"""
    from main import save_character, quests_data
    
    updated = False
    active_quests = character.active_quests or []
    
    for quest_id in active_quests:
        quest = find_quest(quest_id, quests_data)
        if not quest:
            continue
        
        objectives = quest.get("objectives", [])
        for obj in objectives:
            if obj.get("type") == event_type:
                obj_target = obj.get("target")
                if not target_id or obj_target == target_id:
                    # Обновляем прогресс
                    if not character.quest_progress:
                        character.quest_progress = {}
                    
                    if quest_id not in character.quest_progress:
                        character.quest_progress[quest_id] = {"progress": 0}
                    
                    character.quest_progress[quest_id]["progress"] += amount
                    updated = True
    
    # Обновляем ежедневные квесты
    daily_quests = character.daily_quests or {}
    for quest_id, quest_data in daily_quests.items():
        if quest_data.get("completed"):
            continue
        
        obj = quest_data.get("objective", {})
        if obj.get("type") == event_type:
            obj_target = obj.get("target")
            if not target_id or obj_target == target_id:
                quest_data["progress"] = quest_data.get("progress", 0) + amount
                updated = True
    
    if updated:
        save_character(character)

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def find_quest(quest_id, quests_data):
    """Найти квест по ID во всех актах"""
    if not quests_data or "quests" not in quests_data:
        return None
    
    # Ищем по актам
    acts = quests_data["quests"]
    for act_id, act_data in acts.items():
        if isinstance(act_data, dict) and "quests" in act_data:
            for quest in act_data["quests"]:
                if quest.get("id") == quest_id:
                    return quest
    
    return None

def get_available_quests(character, quests_data, active_quests):
    """Получить доступные квесты"""
    available = []
    
    if not quests_data or "quests" not in quests_data:
        return available
    
    acts = quests_data["quests"]
    completed = character.completed_quests or []
    
    for act_id, act_data in acts.items():
        if isinstance(act_data, dict) and "quests" in act_data:
            if character.level < act_data.get("level_req", 0):
                continue
            
            for quest in act_data["quests"]:
                quest_id = quest.get("id")
                if quest_id and quest_id not in active_quests and quest_id not in completed:
                    if character.level >= quest.get("level_req", 1):
                        available.append((quest_id, quest))
    
    return available

def get_quest_target(quest):
    """Получить цель квеста"""
    objectives = quest.get("objectives", [])
    if objectives:
        return objectives[0].get("count", 1)
    return 1

def format_rewards(rewards):
    """Форматировать награду для отображения"""
    parts = []
    
    if rewards.get("exp"):
        parts.append(f"{rewards['exp']}✨")
    if rewards.get("gold"):
        parts.append(f"{rewards['gold']}💰")
    if rewards.get("dstn"):
        parts.append(f"{rewards['dstn']}💎")
    if rewards.get("rainbow_shard"):
        parts.append(f"{rewards['rainbow_shard']}🌈")
    if rewards.get("items"):
        items = rewards["items"]
        if isinstance(items, list):
            if len(items) == 2 and isinstance(items[1], int):
                parts.append(f"{items[0]} x{items[1]}")
            else:
                parts.append(f"{items[0]}")
    if rewards.get("title"):
        parts.append(f"титул '{rewards['title']}'")
    
    return ", ".join(parts) if parts else "❓"

def give_rewards(character, rewards):
    """Выдать награду за квест"""
    from main import save_character
    
    reward_text = []
    
    if rewards.get("exp"):
        character.experience += rewards["exp"]
        reward_text.append(f"✨ +{rewards['exp']} опыта")
    
    if rewards.get("gold"):
        character.gold += rewards["gold"]
        reward_text.append(f"💰 +{rewards['gold']} золота")
    
    if rewards.get("dstn"):
        character.dstn = (character.dstn or 0) + rewards["dstn"]
        reward_text.append(f"💎 +{rewards['dstn']} DSTN")
    
    if rewards.get("rainbow_shard"):
        character.rainbow_shards = (character.rainbow_shards or 0) + rewards["rainbow_shard"]
        reward_text.append(f"🌈 +{rewards['rainbow_shard']} осколков")
    
    if rewards.get("items"):
        items = rewards["items"]
        if isinstance(items, list):
            if len(items) == 2 and isinstance(items[1], int):
                item_id, count = items
                for _ in range(count):
                    character.add_item(item_id)
                reward_text.append(f"📦 +{item_id} x{count}")
            else:
                character.add_item(items[0])
                reward_text.append(f"📦 +{items[0]}")
    
    if rewards.get("title"):
        if not character.titles:
            character.titles = []
        character.titles.append(rewards["title"])
        reward_text.append(f"🏆 титул '{rewards['title']}'")
    
    return "\n".join(reward_text)

def generate_daily_quests(character, quests_data):
    """Сгенерировать ежедневные квесты"""
    daily_quests = {}
    
    # Шаблоны ежедневных квестов
    templates = [
        {
            "id": "daily_kill",
            "name": "⚔️ Ежедневная охота",
            "description": "Убей 20 врагов",
            "objective": {"type": "kill", "target": "any", "count": 20},
            "rewards": {"exp": 200, "gold": 500}
        },
        {
            "id": "daily_gather",
            "name": "🌿 Сбор ресурсов",
            "description": "Собери 50 ресурсов",
            "objective": {"type": "gather", "target": "any", "count": 50},
            "rewards": {"exp": 150, "gold": 300}
        },
        {
            "id": "daily_fish",
            "name": "🎣 Рыбный день",
            "description": "Поймай 10 рыб",
            "objective": {"type": "fish", "count": 10},
            "rewards": {"exp": 100, "gold": 200, "items": ["bait", 3]}
        },
        {
            "id": "daily_mine",
            "name": "⛏️ Шахтёрский день",
            "description": "Добудь 30 руды",
            "objective": {"type": "mine", "count": 30},
            "rewards": {"exp": 200, "gold": 400, "items": ["coal", 5]}
        },
        {
            "id": "daily_craft",
            "name": "🔨 День крафта",
            "description": "Скрафти 5 предметов",
            "objective": {"type": "craft", "count": 5},
            "rewards": {"exp": 150, "gold": 300, "items": ["magic_dust", 2]}
        }
    ]
    
    # Выбираем 3 случайных квеста
    selected = random.sample(templates, min(3, len(templates)))
    
    for quest in selected:
        quest_id = quest["id"]
        daily_quests[quest_id] = {
            "name": quest["name"],
            "description": quest["description"],
            "objective": quest["objective"],
            "target": quest["objective"]["count"],
            "progress": 0,
            "completed": False,
            "rewards": quest["rewards"]
        }
    
    return daily_quests

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================

def handle_callback(call, bot_instance, get_or_create_player_func, quests_data):
    """Обработка callback от квестов"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    from main import save_character
    
    data = call.data.split(':')
    action = data[1] if len(data) > 1 else "main"
    
    if action == "main":
        quests_command(call.message, bot_instance, get_or_create_player_func, quests_data)
    
    elif action == "active":
        show_active_quests(call, bot_instance, character, quests_data)
    
    elif action == "available":
        show_available_quests(call, bot_instance, character, quests_data)
    
    elif action == "completed":
        show_completed_quests(call, bot_instance, character)
    
    elif action == "daily":
        show_daily_quests(call, bot_instance, character, quests_data)
    
    elif action == "take" and len(data) > 2:
        quest_id = data[2]
        take_quest(call, bot_instance, character, quest_id, quests_data)
    
    elif action == "complete" and len(data) > 2:
        quest_id = data[2]
        complete_quest(call, bot_instance, character, quest_id, quests_data)
    
    elif action == "claim_daily" and len(data) > 2:
        quest_id = data[2]
        claim_daily_quest(call, bot_instance, character, quest_id)
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ В разработке")

# ============================================
# ФУНКЦИИ ДЛЯ ДРУГИХ ХЕНДЛЕРОВ
# ============================================

def on_kill(character, enemy_id):
    """Вызывается при убийстве врага"""
    update_quest_progress(character, "kill", enemy_id)
    update_quest_progress(character, "kill", "any")

def on_gather(character, resource_id):
    """Вызывается при сборе ресурса"""
    update_quest_progress(character, "gather", resource_id)
    update_quest_progress(character, "gather", "any")

def on_fish(character):
    """Вызывается при ловле рыбы"""
    update_quest_progress(character, "fish")

def on_mine(character):
    """Вызывается при добыче руды"""
    update_quest_progress(character, "mine")

def on_craft(character):
    """Вызывается при крафте"""
    update_quest_progress(character, "craft")

def on_reach_location(character, location_id):
    """Вызывается при достижении локации"""
    update_quest_progress(character, "reach_location", location_id)

def on_talk(character, npc_id):
    """Вызывается при разговоре с NPC"""
    update_quest_progress(character, "talk", npc_id)

def on_build_house(character):
    """Вызывается при постройке дома"""
    update_quest_progress(character, "build_house")

def on_choose_class(character):
    """Вызывается при выборе класса"""
    update_quest_progress(character, "choose_class")
