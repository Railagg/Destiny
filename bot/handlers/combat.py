import logging
import random
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def attack_command(message, bot, get_or_create_player, enemies_data, locations_data):
    """Начать бой с врагом в текущей локации"""
    user_id = message.from_user.id
    user, character = get_or_create_player(user_id)
    
    # Проверяем, не в бою ли уже
    if character.in_combat:
        bot.send_message(message.chat.id, "⚔️ Ты уже в бою! Используй /fight")
        return
    
    # Получаем врагов в текущей локации
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
    
    # Сохраняем данные врага
    enemy_max_health = enemy.get('health', 10)
    
    # Начинаем бой
    character.in_combat = True
    character.combat_enemy = enemy_id
    character.combat_turn = 0  # ход игрока
    character.current_health = character.health  # копируем текущее здоровье
    character.current_mana = character.magic
    from main import save_character
    save_character(character)
    
    # Отправляем сообщение о начале боя
    text = f"⚔️ *Начало боя!*\n\n"
    text += f"👾 *{enemy.get('name', 'Враг')}*\n"
    text += f"❤️ Здоровье: {enemy_max_health}\n"
    text += f"⚔️ Урон: {enemy.get('damage', 2)}\n"
    if enemy.get('armor', 0):
        text += f"🛡️ Броня: {enemy.get('armor', 0)}\n"
    text += f"\n💪 Твоё здоровье: {character.current_health}/{character.max_health}\n"
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
        from main import save_character
        save_character(character)
        bot.answer_callback_query(call.id, "❌ Ошибка боя")
        return
    
    enemy_max_health = enemy.get('health', 10)
    enemy_damage = enemy.get('damage', 2)
    enemy_armor = enemy.get('armor', 0)
    
    # Получаем текущее здоровье врага из сообщения
    message_text = call.message.text or call.message.caption or ""
    enemy_health_match = re.search(r"❤️ Здоровье: (\d+)", message_text)
    enemy_health = enemy_max_health
    if enemy_health_match:
        enemy_health = int(enemy_health_match.group(1))
    
    result_text = ""
    player_damage = 0
    
    # ========== ХОД ИГРОКА ==========
    if action == "attack":
        # Рассчитываем урон игрока с разбросом
        from main import calculate_damage
        base_damage = calculate_damage(character)
        damage_variation = random.uniform(0.8, 1.2)
        player_damage = int(base_damage * damage_variation)
        
        # Критический удар
        if random.randint(1, 100) <= character.crit_chance:
            player_damage = int(player_damage * character.crit_multiplier)
            result_text += f"💥 *КРИТ!* "
        
        # Учитываем броню врага
        if enemy_armor > 0:
            player_damage = max(1, player_damage - enemy_armor)
        
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
            # Магический урон с разбросом
            base_magic = character.intelligence * 3
            magic_variation = random.uniform(0.9, 1.3)
            magic_damage = int(base_magic * magic_variation)
            enemy_health -= magic_damage
            result_text += f"🔮 Ты нанёс *{magic_damage}* магического урона!\n"
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно маны")
            return
    
    elif action == "flee":
        # Шанс сбежать зависит от ловкости
        flee_chance = 30 + character.dexterity * 2
        if random.randint(1, 100) <= flee_chance:
            character.in_combat = False
            from main import save_character
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
    
    # ========== ПРОВЕРКА НА ПОБЕДУ ==========
    if enemy_health <= 0:
        exp_gain = enemy.get('exp', 10)
        gold_gain = enemy.get('gold', 5)
        
        character.experience += exp_gain
        character.gold += gold_gain
        
        # ===== ТРОФЕИ (с поддержкой min/max) =====
        drops = enemy.get('drops', [])
        drop_text = ""
        for drop in drops:
            if random.randint(1, 100) <= drop.get('chance', 100):
                item_id = drop.get('item')
                
                # Определяем количество
                if 'min' in drop and 'max' in drop:
                    amount = random.randint(drop['min'], drop['max'])
                else:
                    amount = drop.get('amount', 1)
                
                # Добавляем предметы
                for _ in range(amount):
                    character.add_item(item_id)
                
                # Название предмета для красивого вывода
                item_name = items_data.get("items", {}).get(item_id, {}).get('name', item_id)
                drop_text += f"📦 {item_name} x{amount}\n"
        
        # ===== ПРОВЕРКА НА ПОВЫШЕНИЕ УРОВНЯ =====
        level_up_text = ""
        while character.experience >= character.level * 100:
            character.level += 1
            character.max_health += 10
            character.health = character.max_health
            character.current_health = character.max_health
            character.max_energy += 5
            level_up_text += f"✨ *УРОВЕНЬ {character.level}!*\n"
        
        character.in_combat = False
        from main import save_character
        save_character(character)
        
        # Формируем итоговое сообщение
        result_text = f"🎉 *Победа!*\n\n"
        result_text += f"✨ Опыт: +{exp_gain}\n"
        result_text += f"💰 Золото: +{gold_gain}\n"
        if drop_text:
            result_text += f"\n📦 *Добыча:*\n{drop_text}"
        if level_up_text:
            result_text += f"\n{level_up_text}"
        
        bot.edit_message_text(
            result_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return
    
    # ========== ХОД ВРАГА (если игрок не сбежал) ==========
    if action != "flee":
        # Проверка на уклонение игрока
        dodge_chance = character.dodge_chance + character.dexterity
        if random.randint(1, 100) <= dodge_chance:
            result_text += "💨 Ты увернулся от атаки!\n"
        else:
            # Урон врага с разбросом
            enemy_damage_variation = random.uniform(0.8, 1.2)
            enemy_attack = int(enemy_damage * enemy_damage_variation)
            
            # Если игрок в защите, урон уменьшается вдвое
            if character.combat_turn == 2:
                enemy_attack = max(1, enemy_attack // 2)
                character.combat_turn = 0
            
            character.current_health -= enemy_attack
            result_text += f"👾 Враг нанёс *{enemy_attack}* урона!\n"
    
    # ========== ПРОВЕРКА НА ПОРАЖЕНИЕ ==========
    if character.current_health <= 0:
        gold_loss = character.gold // 10
        character.gold -= gold_loss
        character.current_health = 1
        character.in_combat = False
        from main import save_character
        save_character(character)
        
        bot.edit_message_text(
            f"💀 *Ты повержен!*\n\n"
            f"Ты потерял {gold_loss}💰 золота...",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return
    
    from main import save_character
    save_character(character)
    
    # ========== ПРОДОЛЖЕНИЕ БОЯ ==========
    text = f"⚔️ *Продолжение боя*\n\n"
    text += f"👾 *{enemy.get('name', 'Враг')}*\n"
    text += f"❤️ Осталось: {max(1, enemy_health)}/{enemy_max_health}\n\n"
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
