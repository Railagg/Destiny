import logging
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def attack_command(message, bot, get_or_create_player, enemies_data):
    """Начать бой с врагом в текущей локации"""
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Проверяем, не в бою ли уже
    if character.in_combat:
        bot.send_message(message.chat.id, "⚔️ Ты уже в бою! Используй /fight")
        return
    
    # Получаем врагов в текущей локации
    from main import locations_data
    location = locations_data.get("locations", {}).get(character.location, {})
    enemies_in_location = location.get("enemies", [])
    
    if not enemies_in_location:
        bot.send_message(message.chat.id, "🐭 Здесь нет врагов.")
        return
    
    # Выбираем случайного врага
    enemy_id = random.choice(enemies_in_location)
    enemy = enemies_data.get("enemies", {}).get(enemy_id, {})
    
    if not enemy:
        bot.send_message(message.chat.id, "❌ Ошибка: враг не найден")
        return
    
    # Начинаем бой
    character.in_combat = True
    character.combat_enemy = enemy_id
    character.combat_turn = 0  # ход игрока
    character.current_health = character.health  # копируем текущее здоровье
    save_character(character)
    
    # Отправляем сообщение о начале боя
    text = f"⚔️ *Начало боя!*\n\n"
    text += f"👾 *{enemy.get('name', 'Враг')}*\n"
    text += f"❤️ Здоровье: {enemy.get('health', 10)}\n"
    text += f"⚔️ Урон: {enemy.get('damage', 2)}\n\n"
    text += f"💪 Твоё здоровье: {character.current_health}/{character.max_health}\n"
    text += f"🔮 Твоя мана: {character.current_mana}/{character.max_magic}"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Атаковать", callback_data="combat:attack"),
        InlineKeyboardButton("🛡️ Защита", callback_data="combat:defend"),
        InlineKeyboardButton("🔮 Магия", callback_data="combat:magic"),
        InlineKeyboardButton("🏃 Сбежать", callback_data="combat:flee")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def combat_turn(call, bot, get_or_create_player, enemies_data, items_data, action):
    """Обработка хода в бою"""
    user_id = call.from_user.id
    user, character = get_or_create_player(user_id)
    
    if not character.in_combat:
        bot.answer_callback_query(call.id, "❌ Ты не в бою")
        return
    
    enemy_id = character.combat_enemy
    enemy = enemies_data.get("enemies", {}).get(enemy_id, {})
    
    if not enemy:
        character.in_combat = False
        save_character(character)
        bot.answer_callback_query(call.id, "❌ Ошибка боя")
        return
    
    enemy_health = enemy.get('health', 10)
    enemy_damage = enemy.get('damage', 2)
    
    # Ход игрока
    result_text = ""
    player_damage = 0
    
    if action == "attack":
        # Рассчитываем урон игрока
        from main import calculate_damage
        player_damage = calculate_damage(character)
        # Критический удар
        if random.randint(1, 100) <= character.crit_chance:
            player_damage = int(player_damage * character.crit_multiplier)
            result_text += f"💥 *КРИТ!* "
        
        enemy_health -= player_damage
        result_text += f"Ты нанёс *{player_damage}* урона!\n"
    
    elif action == "defend":
        # Защита уменьшает урон в следующем ходу
        character.combat_turn = 2  # следующий ход с защитой
        result_text += "🛡️ Ты встал в защитную стойку.\n"
    
    elif action == "magic":
        # Магическая атака (тратит ману)
        if character.current_mana >= 10:
            character.current_mana -= 10
            magic_damage = character.intelligence * 3
            enemy_health -= magic_damage
            result_text += f"🔮 Ты нанёс *{magic_damage}* магического урона!\n"
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно маны")
            return
    
    elif action == "flee":
        # Шанс сбежать
        if random.randint(1, 100) <= 50:
            character.in_combat = False
            save_character(character)
            bot.edit_message_text(
                "🏃 Ты успешно сбежал!",
                call.message.chat.id,
                call.message.message_id
            )
            bot.answer_callback_query(call.id)
            return
        else:
            result_text += "😰 Не удалось сбежать!\n"
    
    # Проверяем, убит ли враг
    if enemy_health <= 0:
        # Победа!
        exp_gain = enemy.get('exp', 10)
        gold_gain = enemy.get('gold', 5)
        
        character.experience += exp_gain
        character.gold += gold_gain
        
        # Шанс на дроп
        drops = enemy.get('drops', [])
        for drop in drops:
            if random.randint(1, 100) <= drop.get('chance', 100):
                character.add_item(drop.get('item'))
                result_text += f"📦 Ты получил: {drop.get('item')}\n"
        
        # Проверка на уровень
        while character.experience >= character.level * 100:
            character.level += 1
            character.max_health += 10
            character.health = character.max_health
            character.max_energy += 5
            result_text += f"✨ *УРОВЕНЬ {character.level}!*\n"
        
        character.in_combat = False
        save_character(character)
        
        result_text += f"\n🎉 *Победа!*\n"
        result_text += f"✨ Опыт: +{exp_gain}\n"
        result_text += f"💰 Золото: +{gold_gain}"
        
        bot.edit_message_text(
            result_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return
    
    # Ход врага
    if action != "flee":
        # Враг атакует
        enemy_attack = enemy_damage
        if character.combat_turn == 2:  # режим защиты
            enemy_attack = max(1, enemy_attack // 2)
            character.combat_turn = 0
        
        character.current_health -= enemy_attack
        result_text += f"👾 Враг нанёс *{enemy_attack}* урона!\n"
    
    # Проверяем, жив ли игрок
    if character.current_health <= 0:
        # Поражение
        character.current_health = 1
        character.in_combat = False
        save_character(character)
        
        bot.edit_message_text(
            f"💀 *Ты повержен!*\n\nТы едва смог унести ноги...",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return
    
    save_character(character)
    
    # Продолжаем бой
    text = f"⚔️ *Продолжение боя*\n\n"
    text += f"👾 *{enemy.get('name', 'Враг')}*\n"
    text += f"❤️ Осталось: {max(0, enemy_health)}\n\n"
    text += f"💪 Твоё здоровье: {character.current_health}/{character.max_health}\n"
    text += f"🔮 Твоя мана: {character.current_mana}/{character.max_magic}\n\n"
    text += result_text
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚔️ Атаковать", callback_data="combat:attack"),
        InlineKeyboardButton("🛡️ Защита", callback_data="combat:defend"),
        InlineKeyboardButton("🔮 Магия", callback_data="combat:magic"),
        InlineKeyboardButton("🏃 Сбежать", callback_data="combat:flee")
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id)
