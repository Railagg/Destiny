import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import random
import time
from datetime import datetime

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КЛАССОВЫЕ БОНУСЫ В БОЮ
# ============================================

CLASS_COMBAT_BONUSES = {
    "warrior": {
        "name": "⚔️ Мечник",
        "crit_multiplier": 2.2,
        "crit_chance_bonus": 5,
        "damage_multiplier": 1.1,
        "rage_gain": 2,  # Ярость за удар
        "abilities": {
            "whirlwind": {"name": "🌀 Вихрь", "damage": 0.8, "aoe": True, "cooldown": 3},
            "mighty_blow": {"name": "💥 Мощный удар", "damage": 1.5, "cooldown": 2},
            "execute": {"name": "🔪 Казнь", "damage": 2.0, "condition": "enemy_hp_below_30%"}
        }
    },
    "archer": {
        "name": "🏹 Лучник",
        "crit_multiplier": 2.0,
        "crit_chance_bonus": 8,
        "dodge_bonus": 5,
        "range_bonus": 1.2,
        "abilities": {
            "aimed_shot": {"name": "🎯 Прицельный выстрел", "damage": 1.3, "ignore_armor": 30, "cooldown": 2},
            "rapid_fire": {"name": "⚡ Быстрая стрельба", "hits": 3, "damage": 0.5, "cooldown": 3},
            "frost_arrow": {"name": "❄️ Ледяная стрела", "damage": 1.0, "slow": 50, "cooldown": 2}
        }
    },
    "mage": {
        "name": "🔮 Маг",
        "magic_damage_multiplier": 1.2,
        "mana_regen_bonus": 5,
        "spell_crit_chance": 8,
        "abilities": {
            "fireball": {"name": "🔥 Огненный шар", "damage": 1.4, "mana_cost": 20, "burn": 10, "cooldown": 2},
            "ice_spike": {"name": "❄️ Ледяное копьё", "damage": 1.2, "mana_cost": 15, "freeze_chance": 30, "cooldown": 2},
            "arcane_explosion": {"name": "🌀 Тайный взрыв", "damage": 1.0, "mana_cost": 25, "aoe": True, "cooldown": 3}
        }
    },
    "guardian": {
        "name": "🛡️ Страж",
        "defense_multiplier": 1.3,
        "block_chance_bonus": 10,
        "health_regen_bonus": 5,
        "threat_multiplier": 2.0,
        "abilities": {
            "shield_bash": {"name": "🛡️ Удар щитом", "damage": 1.2, "stun_chance": 40, "cooldown": 2},
            "taunt": {"name": "👹 Провокация", "effect": "force_target", "cooldown": 3},
            "defensive_stance": {"name": "🛡️ Оборонительная стойка", "defense": 1.5, "duration": 3, "cooldown": 4}
        }
    },
    "paladin": {
        "name": "⚔️✨ Паладин",
        "holy_damage": 5,
        "shield_growth": 3,  # Щит растёт с каждым ударом
        "heal_power_bonus": 10,
        "abilities": {
            "holy_strike": {"name": "✨ Священный удар", "damage": 1.2, "heal_self": 10, "cooldown": 1},
            "divine_shield": {"name": "🛡️ Божественный щит", "shield": 50, "duration": 2, "cooldown": 4},
            "blessing": {"name": "🙏 Благословение", "heal": 30, "buff": "damage+20%", "duration": 3, "cooldown": 3}
        }
    },
    "rogue": {
        "name": "🗡️ Разбойник",
        "crit_multiplier": 2.5,
        "crit_chance_bonus": 12,
        "dodge_bonus": 12,
        "stealth_bonus": 20,
        "backstab_multiplier": 3.0,
        "abilities": {
            "backstab": {"name": "🗡️ Удар в спину", "damage": 2.0, "condition": "stealth_or_behind", "cooldown": 1},
            "poison_blade": {"name": "🧪 Отравленный клинок", "damage": 1.0, "poison": 15, "duration": 3, "cooldown": 2},
            "vanish": {"name": "👻 Исчезновение", "effect": "stealth", "duration": 2, "cooldown": 4}
        }
    },
    "druid": {
        "name": "🌿 Друид",
        "heal_power_bonus": 20,
        "nature_damage_bonus": 10,
        "health_regen_bonus": 10,
        "abilities": {
            "healing_touch": {"name": "💚 Лечащее прикосновение", "heal": 40, "mana_cost": 20, "cooldown": 2},
            "thorn_whip": {"name": "🌱 Шипастая плеть", "damage": 1.2, "bleed": 10, "duration": 3, "cooldown": 1},
            "bear_form": {"name": "🐻 Форма медведя", "health_multiplier": 2.0, "damage_multiplier": 1.3, "duration": 3, "cooldown": 5}
        }
    },
    "warlock": {
        "name": "💀 Чернокнижник",
        "life_steal": 10,
        "curse_power_bonus": 20,
        "shadow_damage_bonus": 15,
        "abilities": {
            "shadow_bolt": {"name": "💀 Теневая стрела", "damage": 1.3, "life_steal": 20, "mana_cost": 15, "cooldown": 1},
            "curse_of_weakness": {"name": "😈 Проклятие слабости", "enemy_damage_reduction": 20, "duration": 3, "cooldown": 2},
            "summon_imp": {"name": "👹 Призыв беса", "summon_damage": 0.5, "duration": 3, "cooldown": 4}
        }
    },
    "shaman": {
        "name": "🥁 Шаман",
        "totem_power_bonus": 30,
        "elemental_damage_bonus": 10,
        "spirit_power_bonus": 20,
        "abilities": {
            "lightning_bolt": {"name": "⚡ Удар молнии", "damage": 1.3, "chain": 2, "mana_cost": 15, "cooldown": 1},
            "healing_wave": {"name": "🌊 Целительная волна", "heal": 30, "aoe": True, "mana_cost": 25, "cooldown": 3},
            "totem_of_wrath": {"name": "🪓 Тотем гнева", "damage_buff": 20, "duration": 3, "cooldown": 4}
        }
    }
}

# ============================================
# ФУНКЦИИ БОЯ
# ============================================

def attack_command(message, bot_instance, get_or_create_player_func, enemies_data, locations_data):
    """Начать бой с врагом"""
    user_id = message.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    from main import refresh_energy, refresh_magic, save_character
    
    refresh_energy(character)
    refresh_magic(character)
    
    # Проверяем энергию
    if character.energy < 5:
        bot_instance.send_message(
            message.chat.id,
            "❌ У тебя недостаточно энергии для боя! (нужно 5⚡)\n"
            "Отдохни или подожди восстановления."
        )
        return
    
    # Получаем текущую локацию
    location_id = character.current_location or "start"
    location = locations_data.get("locations", {}).get(location_id, {})
    
    # Получаем список врагов в локации
    enemies = location.get("enemies", [])
    if not enemies:
        # Если нет врагов, показываем ближайшие локации с врагами
        text = "🕊️ В этой локации нет врагов.\n\n"
        text += "Попробуй отправиться в:\n"
        text += "• 🌲 Глухой лес\n"
        text += "• ⛰️ Горы\n"
        text += "• 🕳️ Шахта\n"
        text += "• 🏜️ Пустыня\n"
        text += "• 🌿 Болото\n"
        text += "• ❄️ Ледяные равнины\n"
        text += "• 🌋 Вулкан"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🗺️ Карта", callback_data="game:map"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
        
        bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')
        return
    
    # Выбираем случайного врага
    enemy_id = random.choice(enemies)
    enemy_data = enemies_data.get("enemies", {}).get(enemy_id, {})
    
    if not enemy_data:
        bot_instance.send_message(message.chat.id, "❌ Ошибка загрузки врага")
        return
    
    # Тратим энергию
    character.energy -= 5
    save_character(character)
    
    # Создаём сессию боя
    start_combat(message, bot_instance, character, enemy_id, enemy_data)

def start_combat(message, bot_instance, character, enemy_id, enemy_data):
    """Начать боевую сессию"""
    user_id = message.from_user.id
    
    # Сохраняем состояние боя в кэш (в реальной игре нужно хранить в БД)
    # Для простоты используем глобальный словарь
    if not hasattr(bot_instance, "combat_sessions"):
        bot_instance.combat_sessions = {}
    
    enemy_hp = enemy_data.get("health", 50) * (1 + (character.level * 0.1))  # Масштабируем уровень
    
    combat_state = {
        "enemy_id": enemy_id,
        "enemy_name": enemy_data.get("name", "Враг"),
        "enemy_hp": int(enemy_hp),
        "enemy_max_hp": int(enemy_hp),
        "enemy_damage": enemy_data.get("damage", 5),
        "enemy_armor": enemy_data.get("armor", 0),
        "player_hp": character.health,
        "player_max_hp": character.max_health,
        "turn": 0,
        "status_effects": {},
        "combat_log": []
    }
    
    bot_instance.combat_sessions[user_id] = combat_state
    
    show_combat_menu(message, bot_instance, character, combat_state)

def show_combat_menu(message, bot_instance, character, combat_state):
    """Показать меню боя"""
    from main import calculate_damage, calculate_defense, calculate_magic_damage
    
    player_damage = calculate_damage(character)
    player_magic_damage = calculate_magic_damage(character)
    
    # Классовые бонусы
    class_bonus = CLASS_COMBAT_BONUSES.get(character.player_class, {})
    
    text = f"⚔️ *БОЙ!*\n\n"
    
    # Информация о враге
    text += f"👾 *{combat_state['enemy_name']}*\n"
    text += f"❤️ HP: {combat_state['enemy_hp']}/{combat_state['enemy_max_hp']}\n"
    text += f"⚔️ Урон: {combat_state['enemy_damage']}\n"
    text += f"🛡️ Броня: {combat_state['enemy_armor']}\n\n"
    
    # Информация об игроке
    text += f"👤 *Ты*\n"
    text += f"❤️ HP: {character.health}/{character.max_health}\n"
    text += f"⚡ Энергия: {character.energy}\n"
    text += f"🔮 Мана: {character.magic}/{character.max_magic}\n"
    text += f"⚔️ Урон: {player_damage} (физ.)\n"
    text += f"✨ Маг. урон: {player_magic_damage}\n\n"
    
    # Классовая информация
    if character.player_class and class_bonus:
        text += f"🎭 *{class_bonus['name']}*\n"
        if character.player_class == "paladin" and hasattr(character, 'paladin_shield'):
            text += f"🛡️ Щит паладина: +{character.paladin_shield or 0}\n"
        if character.player_class == "rogue" and hasattr(character, 'stealth'):
            if character.stealth:
                text += f"👻 Ты в невидимости!\n"
    
    # Последние действия
    if combat_state['combat_log']:
        text += f"\n📜 *Последние действия:*\n"
        for log in combat_state['combat_log'][-3:]:
            text += f"• {log}\n"
    
    # Кнопки действий
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Базовые атаки
    markup.add(
        InlineKeyboardButton("⚔️ Атака", callback_data="combat:attack:physical"),
        InlineKeyboardButton("🔮 Магия", callback_data="combat:attack:magic")
    )
    
    # Классовые способности (если есть мана)
    if character.magic >= 15 and class_bonus:
        abilities = class_bonus.get("abilities", {})
        ability_buttons = []
        for abil_id, abil in list(abilities.items())[:4]:  # Максимум 4 кнопки
            mana_cost = abil.get("mana_cost", 0)
            if character.magic >= mana_cost:
                ability_buttons.append(
                    InlineKeyboardButton(f"{abil['name']}", callback_data=f"combat:ability:{abil_id}")
                )
        
        if ability_buttons:
            for i in range(0, len(ability_buttons), 2):
                markup.add(*ability_buttons[i:i+2])
    
    # Защита и бегство
    markup.add(
        InlineKeyboardButton("🛡️ Защита", callback_data="combat:defend"),
        InlineKeyboardButton("🏃 Сбежать", callback_data="combat:flee")
    )
    
    bot_instance.send_message(
        message.chat.id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def combat_turn(call, bot_instance, get_or_create_player_func, enemies_data, items_data, action):
    """Обработка хода в бою"""
    user_id = call.from_user.id
    user, character = get_or_create_player_func(user_id)
    
    from main import save_character, refresh_energy, refresh_magic, calculate_damage, calculate_defense
    
    refresh_energy(character)
    refresh_magic(character)
    
    # Получаем состояние боя
    if not hasattr(bot_instance, "combat_sessions") or user_id not in bot_instance.combat_sessions:
        bot_instance.answer_callback_query(call.id, "❌ Бой не найден. Начни заново!")
        return
    
    combat_state = bot_instance.combat_sessions[user_id]
    
    # Обработка действия игрока
    player_damage = calculate_damage(character)
    player_magic_damage = calculate_magic_damage(character)
    class_bonus = CLASS_COMBAT_BONUSES.get(character.player_class, {})
    
    player_effect = ""
    enemy_effect = ""
    
    if action == "attack:physical":
        # Физическая атака
        damage = player_damage
        crit_chance = character.crit_chance or 0
        crit_multiplier = class_bonus.get("crit_multiplier", character.crit_multiplier or 2.0)
        
        if random.randint(1, 100) <= crit_chance:
            damage = int(damage * crit_multiplier)
            player_effect = "⚡ КРИТ!"
        
        # Учёт брони врага
        armor = combat_state['enemy_armor']
        damage = max(1, damage - armor)
        
        combat_state['enemy_hp'] -= damage
        combat_state['combat_log'].append(f"⚔️ Ты нанёс {damage} урона {player_effect}")
        
        # Особые эффекты классов
        if character.player_class == "warrior":
            # Ярость воина
            character.rage = getattr(character, 'rage', 0) + class_bonus.get("rage_gain", 0)
        
        elif character.player_class == "rogue" and hasattr(character, 'stealth') and character.stealth:
            # Бонус из скрытности
            damage = int(damage * class_bonus.get("backstab_multiplier", 1.0))
            character.stealth = False
            combat_state['combat_log'].append(f"👻 Удар из тени!")
        
        elif character.player_class == "paladin":
            # Рост щита паладина
            character.paladin_shield = getattr(character, 'paladin_shield', 0) + class_bonus.get("shield_growth", 3)
            if character.paladin_shield > 150:
                character.paladin_shield = 150
    
    elif action == "attack:magic":
        # Магическая атака
        if character.magic < 10:
            bot_instance.answer_callback_query(call.id, "❌ Недостаточно маны!")
            return
        
        damage = player_magic_damage
        character.magic -= 10
        
        crit_chance = class_bonus.get("spell_crit_chance", character.crit_chance or 0)
        if random.randint(1, 100) <= crit_chance:
            damage = int(damage * 2.0)
            player_effect = "✨ КРИТ!"
        
        combat_state['enemy_hp'] -= damage
        combat_state['combat_log'].append(f"🔮 Магия нанесла {damage} урона {player_effect}")
    
    elif action == "defend":
        # Защита - меньше урона в следующий ход
        combat_state['status_effects']['defending'] = True
        combat_state['combat_log'].append(f"🛡️ Ты готовишься к защите")
    
    elif action == "flee":
        # Попытка сбежать
        if random.randint(1, 100) <= 70:  # 70% шанс
            bot_instance.answer_callback_query(call.id, "✅ Ты сбежал!")
            del bot_instance.combat_sessions[user_id]
            bot_instance.delete_message(call.message.chat.id, call.message.message_id)
            from handlers.game import location_command
            location_command(call.message)
            return
        else:
            combat_state['combat_log'].append(f"🏃 Не удалось сбежать!")
    
    elif action.startswith("ability:"):
        # Классовая способность
        ability_id = action.split(':')[1]
        abilities = class_bonus.get("abilities", {})
        ability = abilities.get(ability_id, {})
        
        if not ability:
            bot_instance.answer_callback_query(call.id, "❌ Способность не найдена")
            return
        
        mana_cost = ability.get("mana_cost", 0)
        if character.magic < mana_cost:
            bot_instance.answer_callback_query(call.id, "❌ Недостаточно маны!")
            return
        
        character.magic -= mana_cost
        
        if "damage" in ability:
            damage = int(player_damage * ability["damage"])
            if ability.get("aoe"):
                # Урон по площади
                damage = int(damage * 0.7)
                combat_state['combat_log'].append(f"{ability['name']} нанёс {damage} урона всем врагам")
            else:
                combat_state['combat_log'].append(f"{ability['name']} нанёс {damage} урона")
            combat_state['enemy_hp'] -= damage
        
        if "heal" in ability:
            heal = ability["heal"]
            character.health = min(character.health + heal, character.max_health)
            combat_state['combat_log'].append(f"{ability['name']} восстановил {heal}❤️")
        
        if "buff" in ability:
            combat_state['status_effects'][f"buff_{ability_id}"] = ability.get("duration", 2)
            combat_state['combat_log'].append(f"{ability['name']} активирован")
        
        if "summon_damage" in ability:
            # Призыв помощника
            summon_damage = int(player_damage * ability["summon_damage"])
            combat_state['enemy_hp'] -= summon_damage
            combat_state['combat_log'].append(f"{ability['name']} нанёс {summon_damage} урона")
    
    # Проверка на победу
    if combat_state['enemy_hp'] <= 0:
        # Победа
        victory(call, bot_instance, character, combat_state, enemies_data, items_data)
        return
    
    # Ход врага
    enemy_attack(combat_state, character)
    
    # Проверка на поражение
    if character.health <= 0:
        # Поражение
        defeat(call, bot_instance, character, combat_state)
        return
    
    # Сохраняем изменения
    save_character(character)
    
    # Обновляем меню
    bot_instance.delete_message(call.message.chat.id, call.message.message_id)
    show_combat_menu(call.message, bot_instance, character, combat_state)

def enemy_attack(combat_state, character):
    """Атака врага"""
    enemy_damage = combat_state['enemy_damage']
    
    # Защита игрока
    if combat_state['status_effects'].get('defending'):
        enemy_damage = int(enemy_damage * 0.5)
        del combat_state['status_effects']['defending']
        combat_state['combat_log'].append(f"🛡️ Защита уменьшила урон!")
    
    # Уклонение
    if random.randint(1, 100) <= (character.dodge_chance or 0):
        combat_state['combat_log'].append(f"💨 Ты уклонился!")
        return
    
    # Блок щитом
    if random.randint(1, 100) <= (character.block_chance or 0):
        blocked = min(enemy_damage, character.block_amount or 0)
        enemy_damage -= blocked
        combat_state['combat_log'].append(f"🛡️ Заблокировано {blocked} урона!")
    
    # Щит паладина
    if hasattr(character, 'paladin_shield') and character.paladin_shield > 0:
        shield_block = min(enemy_damage, character.paladin_shield)
        enemy_damage -= shield_block
        character.paladin_shield -= shield_block
        combat_state['combat_log'].append(f"✨ Щит паладина поглотил {shield_block} урона!")
    
    # Наносим урон
    character.health -= max(1, enemy_damage)
    combat_state['combat_log'].append(f"👾 Враг нанёс {enemy_damage} урона")

def victory(call, bot_instance, character, combat_state, enemies_data, items_data):
    """Обработка победы"""
    from main import save_character
    
    enemy_id = combat_state['enemy_id']
    enemy_data = enemies_data.get("enemies", {}).get(enemy_id, {})
    
    # Базовая награда
    exp_gain = enemy_data.get("exp_reward", 50)
    gold_gain = random.randint(
        enemy_data.get("gold_min", 10),
        enemy_data.get("gold_max", 30)
    )
    
    # Классовые бонусы к опыту
    if character.player_class == "mage":
        exp_gain = int(exp_gain * 1.1)
    
    character.experience += exp_gain
    character.gold += gold_gain
    
    # Проверка на повышение уровня
    level_up = False
    while character.experience >= character.level * 1000:
        character.experience -= character.level * 1000
        character.level += 1
        level_up = True
        
        # Повышение характеристик при уровне
        character.max_health += 10
        character.health += 10
        character.max_energy += 5
        character.max_magic += 5
    
    # Дроп предметов
    drops = []
    drop_chance = enemy_data.get("drop_chance", {})
    for item_id, chance in drop_chance.items():
        if random.randint(1, 100) <= chance:
            if items_data and "items" in items_data:
                item_data = items_data["items"].get(item_id, {})
                if item_data:
                    character.add_item(item_id)
                    drops.append(item_data.get("name", item_id))
    
    # Сохраняем
    save_character(character)
    del bot_instance.combat_sessions[call.from_user.id]
    
    # Формируем текст победы
    text = f"🎉 *ПОБЕДА!*\n\n"
    text += f"Ты одолел {combat_state['enemy_name']}!\n\n"
    text += f"💰 Золото: +{gold_gain}\n"
    text += f"✨ Опыт: +{exp_gain}\n"
    
    if drops:
        text += f"\n📦 Добыча:\n"
        for drop in drops:
            text += f"• {drop}\n"
    
    if level_up:
        text += f"\n🌟 *НОВЫЙ УРОВЕНЬ!*\n"
        text += f"Ты достиг {character.level} уровня!\n"
        text += f"❤️ Здоровье +10\n"
        text += f"⚡ Энергия +5\n"
        text += f"🔮 Мана +5"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⚔️ Продолжить бой", callback_data="combat:new"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:location"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def defeat(call, bot_instance, character, combat_state):
    """Обработка поражения"""
    from main import save_character
    
    # Штраф за смерть
    gold_loss = int(character.gold * 0.1)
    character.gold -= gold_loss
    character.health = int(character.max_health * 0.3)  # Воскрешение с 30% здоровья
    
    # Сброс боевых баффов
    if hasattr(character, 'stealth'):
        character.stealth = False
    if hasattr(character, 'paladin_shield'):
        character.paladin_shield = 0
    
    save_character(character)
    del bot_instance.combat_sessions[call.from_user.id]
    
    text = f"💀 *ПОРАЖЕНИЕ*\n\n"
    text += f"Ты пал в бою с {combat_state['enemy_name']}...\n\n"
    text += f"💰 Потеряно золота: {gold_loss}\n"
    text += f"❤️ Ты воскрес с 30% здоровья"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Вернуться", callback_data="game:location"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def calculate_magic_damage(character):
    """Рассчитать магический урон"""
    from main import items_data
    
    base_magic_damage = character.intelligence * 2 + (character.magic_damage_bonus or 0)
    
    # Бонус от предметов
    inventory = character.get_inventory()
    for item_id in inventory:
        if item_id in items_data.get("items", {}):
            item = items_data["items"][item_id]
            if item.get("type") == "weapon" and item.get("magic_damage"):
                base_magic_damage += item["magic_damage"]
    
    # Классовые бонусы
    class_bonus = CLASS_COMBAT_BONUSES.get(character.player_class, {})
    magic_multiplier = class_bonus.get("magic_damage_multiplier", 1.0)
    
    return int(base_magic_damage * magic_multiplier)
