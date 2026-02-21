import telebot
import json
import time
import random
from datetime import datetime
import os

# ============================================
# НАСТРОЙКИ - 8147602886:AAGBRldvjY6n5cXofGT9ihXvwadMQk3RNmo
# ============================================

BOT_TOKEN = "8147602886:AAGBRldvjY6n5cXofGT9ihXvwadMQk3RNmo"

# ============================================
# ЗАГРУЗКА КВЕСТА ИЗ JSON
# ============================================
try:
    with open('quest.json', 'r', encoding='utf-8') as f:
        quest_data = json.load(f)
    print(f"✅ Квест загружен! Локаций: {len(quest_data['locations'])}")
    print(f"✅ Предметов: {len(quest_data.get('items', {}))}")
    print(f"✅ Заклинаний: {len(quest_data.get('spells', {}))}")
    print(f"✅ Врагов: {len(quest_data.get('enemies', {}))}")
    print(f"✅ Заданий: {len(quest_data.get('quests', {}))}")
    print(f"✅ Ежедневных заданий: {len(quest_data.get('daily_quests', {}))}")
    print(f"✅ Достижений: {len(quest_data.get('achievements', {}))}")
except Exception as e:
    print(f"❌ Ошибка загрузки квеста: {e}")
    quest_data = {
        "locations": {}, 
        "items": {}, 
        "spells": {},
        "enemies": {}, 
        "quests": {},
        "daily_quests": {},
        "achievements": {},
        "premium_chests": {},
        "daily_rewards": {},
        "player": {"max_energy": 100, "recovery_per_hour": 10}
    }

# ============================================
# ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================
bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище игроков
players = {}

class Player:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.location = "start"
        self.energy = 100
        self.max_energy = 100
        self.last_update = time.time()
        self.magic = 100
        self.max_magic = 100
        self.last_magic_update = time.time()
        self.inventory = []
        self.gold = 20
        self.tokens = 0
        self.destiny_tokens = 0  # Токены DSTN
        self.exp = 0
        self.health = 100
        self.max_health = 100
        self.completed_quests = []
        self.accepted_quests = []
        self.daily_quests = {}
        self.daily_quest_progress = {}
        self.last_daily_reset = time.time()
        self.weekly_quests = {}
        self.weekly_progress = {}
        self.last_weekly_reset = time.time()
        self.achievements = []
        self.achievement_stats = {
            "wolves_killed": 0,
            "fish_caught": 0,
            "ore_mined": 0,
            "meals_cooked": 0,
            "spiders_killed": 0,
            "bears_killed": 0,
            "moose_killed": 0
        }
        self.daily_streak = 0
        self.last_daily_claim = 0
        self.spells = []
        self.spell_cooldowns = {}
        self.base_damage = 1
        self.defense_bonus = 0
        self.blind_active = False
        self.combat_state = None
        self.last_rest_time = 0
        self.last_daily_chest = {}
        self.pickaxe_durability = {}
        self.fishing_rod_durability = {}
        self.sickle_durability = {}
        self.hoe_durability = {}
        self.player_class = None
        self.class_level = 1
        self.class_exp = 0
        self.stat_points = 0
        self.strength = 1
        self.dexterity = 1
        self.intelligence = 1
        self.vitality = 1
        self.crit_chance = 0
        self.crit_multiplier = 2.0
        self.dodge_chance = 0
        self.health_regen = 0
        self.magic_regen = 0
        self.luck = 0
        
        # Система домика
        self.house_level = 0
        self.house_beds = {}
        self.garden_beds = {}
        self.garden_progress = {}
        self.garden_planted_time = {}
        self.garden_crops = {}
        self.teleport_cooldown = 0
        
        # Стартовые предметы
        for item_id in quest_data.get("player", {}).get("start_items", []):
            self.add_item(item_id)
        
        # Стартовые заклинания
        for spell_id in quest_data.get("player", {}).get("start_spells", []):
            if spell_id not in self.spells:
                self.spells.append(spell_id)
    
    def check_daily_reset(self):
        now = time.time()
        if now - self.last_daily_reset > 86400:
            self.daily_quests = {}
            self.daily_quest_progress = {}
            self.last_daily_reset = now
            return True
        return False
    
    def check_weekly_reset(self):
        now = time.time()
        if now - self.last_weekly_reset > 604800:
            self.weekly_quests = {}
            self.weekly_progress = {}
            self.last_weekly_reset = now
            return True
        return False
    
    def claim_daily_reward(self):
        now = time.time()
        
        if now - self.last_daily_claim < 86400:
            remaining = int(86400 - (now - self.last_daily_claim)) / 3600
            return False, f"⏳ Следующая награда через {remaining:.1f}ч"
        
        if now - self.last_daily_claim > 172800:
            self.daily_streak = 0
        
        self.daily_streak += 1
        if self.daily_streak > 7:
            self.daily_streak = 1
        
        self.last_daily_claim = now
        return True, self.daily_streak
    
    def choose_class(self, class_name):
        if self.player_class is None:
            self.player_class = class_name
            if class_name == "warrior":
                self.strength = 3
                self.base_damage += 2
            elif class_name == "archer":
                self.dexterity = 3
                self.dodge_chance += 5
            elif class_name == "mage":
                self.intelligence = 3
                self.max_magic += 30
            elif class_name == "guardian":
                self.vitality = 3
                self.max_health += 30
                self.defense_bonus += 5
            return True
        return False
    
    def add_class_exp(self, amount):
        self.class_exp += amount
        exp_needed = self.class_level * 100
        if self.class_exp >= exp_needed:
            self.class_level += 1
            self.class_exp -= exp_needed
            self.stat_points += 1
            return True
        return False
    
    def calculate_damage(self):
        weapon_damage = 0
        for item_id in self.inventory:
            if item_id in quest_data.get("items", {}):
                item = quest_data["items"][item_id]
                if item.get("type") == "weapon":
                    weapon_damage += item.get("damage", 0)
        return self.base_damage + weapon_damage + (self.strength - 1)
    
    def calculate_defense(self):
        defense = self.defense_bonus
        for item_id in self.inventory:
            if item_id in quest_data.get("items", {}):
                item = quest_data["items"][item_id]
                if item.get("type") == "armor":
                    defense += item.get("defense", 0)
        return defense + (self.vitality - 1)
    
    def calculate_magic_damage(self):
        return 10 + (self.intelligence * 2)
    
    def refresh_energy(self):
        now = time.time()
        hours_passed = (now - self.last_update) // 3600
        if hours_passed > 0:
            self.energy = min(self.energy + hours_passed * 10, self.max_energy)
            self.last_update += hours_passed * 3600
    
    def refresh_magic(self):
        now = time.time()
        hours_passed = (now - self.last_magic_update) // 3600
        if hours_passed > 0:
            self.magic = min(self.magic + hours_passed * 5 + self.magic_regen, self.max_magic)
            self.last_magic_update += hours_passed * 3600
    
    def can_cast_spell(self, spell_id):
        if spell_id not in self.spell_cooldowns:
            return True
        last_used = self.spell_cooldowns[spell_id]
        spell = quest_data["spells"][spell_id]
        hours_passed = (time.time() - last_used) // 3600
        return hours_passed >= spell['cooldown']
    
    def use_spell(self, spell_id):
        self.spell_cooldowns[spell_id] = time.time()
    
    def has_item(self, item_id):
        return item_id in self.inventory
    
    def add_item(self, item_id):
        if item_id not in self.inventory:
            self.inventory.append(item_id)
            return True
        return False
    
    def remove_item(self, item_id):
        if item_id in self.inventory:
            self.inventory.remove(item_id)
            return True
        return False
    
    def accept_quest(self, quest_id):
        if quest_id not in self.accepted_quests and quest_id not in self.completed_quests:
            self.accepted_quests.append(quest_id)
            return True
        return False
    
    def complete_quest(self, quest_id):
        if quest_id in self.accepted_quests:
            self.accepted_quests.remove(quest_id)
            self.completed_quests.append(quest_id)
            return True
        return False

# ============================================
# ФУНКЦИЯ ОТОБРАЖЕНИЯ ЛОКАЦИИ
# ============================================
def show_location(message, player):
    player.refresh_energy()
    player.refresh_magic()
    
    location_id = player.location
    if location_id not in quest_data["locations"]:
        location_id = "start"
        player.location = "start"
    
    location = quest_data["locations"][location_id]
    
    text = f"📍 *{location['title']}*\n\n"
    text += location['description']
    text += f"\n\n⚡ Энергия: {player.energy}/{player.max_energy}"
    text += f"\n🔮 Магия: {player.magic}/{player.max_magic}"
    text += f"\n💰 Золото: {player.gold}"
    text += f"\n🪙 DSTN: {player.destiny_tokens}"
    text += f"\n❤️ Здоровье: {player.health}/{player.max_health}"
    text += f"\n⚔️ Урон: {player.calculate_damage()}"
    text += f"\n🛡️ Защита: {player.calculate_defense()}"
    
    if player.player_class:
        text += f"\n📖 Класс: {player.player_class} (ур. {player.class_level})"
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    for i, action in enumerate(location.get('actions', [])):
        action_type = action.get('type', '')
        
        if action.get('condition') == "item_not_in_inventory":
            item_id = action.get('item')
            if player.has_item(item_id):
                continue
        
        button_text = action['text']
        callback_data = f"action:{action_type}:{action.get('next_location', '')}:{i}"
        
        button = telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data)
        markup.add(button)
    
    markup.add(
        telebot.types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory"),
        telebot.types.InlineKeyboardButton("📊 Статус", callback_data="status"),
        telebot.types.InlineKeyboardButton("📜 Задания", callback_data="quests")
    )
    
    try:
        if location.get('image') and location['image'] != "":
            bot.send_photo(
                chat_id=message.chat.id,
                photo=location['image'],
                caption=text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        elif hasattr(message, 'message_id') and message.message_id:
            bot.edit_message_text(
                text,
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
    except:
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=markup,
            parse_mode='Markdown'
        )

# ============================================
# КОМАНДА /start
# ============================================

@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.from_user.id
    username = message.from_user.first_name

    if user_id not in players:
        players[user_id] = Player(user_id)
        print(f"🎮 Новый игрок: {username}")

    player = players[user_id]
    
    # СОЗДАЕМ КНОПКУ ДЛЯ WEBAPP
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    
    markup = InlineKeyboardMarkup()
    webapp_button = InlineKeyboardButton(
        text="🎮 ОТКРЫТЬ ИГРУ",
        web_app=WebAppInfo(url="https://destiny-1-6m57.onrender.com")
    )
    markup.add(webapp_button)
    
    # Отправляем приветствие с кнопкой
    bot.send_message(
        message.chat.id,
        f"👋 Привет, {username}!\n\nНажми кнопку ниже, чтобы открыть игру:",
        reply_markup=markup
    )

@bot.message_handler(commands=['class'])
def choose_class_command(message):
    user_id = message.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id, message.from_user.first_name)
    
    player = players[user_id]
    
    if player.player_class:
        bot.reply_to(message, f"❌ Ты уже выбрал класс: {player.player_class}")
        return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("⚔️ Воин", callback_data="choose_class:warrior"),
        telebot.types.InlineKeyboardButton("🏹 Лучник", callback_data="choose_class:archer"),
        telebot.types.InlineKeyboardButton("🔮 Маг", callback_data="choose_class:mage"),
        telebot.types.InlineKeyboardButton("🛡️ Страж", callback_data="choose_class:guardian")
    )
    
    bot.send_message(
        message.chat.id,
        "🌟 *Выбери свой класс:*\n\n"
        "⚔️ Воин: сила, ближний бой\n"
        "🏹 Лучник: ловкость, дальний бой\n"
        "🔮 Маг: интеллект, магия\n"
        "🛡️ Страж: защита, выживаемость",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# ОБРАБОТКА КНОПОК
# ============================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if user_id not in players:
        bot.answer_callback_query(call.id, "❌ Начни игру с /start")
        bot.edit_message_text(
            "Нажми /start чтобы начать игру",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        return
    
    player = players[user_id]
    player.refresh_energy()
    player.refresh_magic()
    player.check_daily_reset()
    player.check_weekly_reset()
    
    try:
        # ВЫБОР КЛАССА
        if call.data.startswith("choose_class:"):
            class_name = call.data.split(":")[1]
            if player.choose_class(class_name):
                bot.answer_callback_query(call.id, f"✅ Ты стал {class_name}!")
                bot.delete_message(call.message.chat.id, call.message.message_id)
                show_location(call.message, player)
            else:
                bot.answer_callback_query(call.id, "❌ Ты уже выбрал класс")
            return
        
        # ИНВЕНТАРЬ
        if call.data == "inventory":
            if not player.inventory:
                text = "🎒 *Инвентарь пуст*"
            else:
                text = "🎒 *Твой инвентарь:*\n\n"
                for item_id in player.inventory:
                    if item_id in quest_data.get("items", {}):
                        item = quest_data["items"][item_id]
                        text += f"• {item['name']}: {item.get('description', '')}\n"
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_location"))
            
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id)
            return
        
        # СТАТУС
        if call.data == "status":
            text = f"📊 *Статус персонажа*\n\n"
            text += f"👤 Имя: {player.username}\n"
            if player.player_class:
                text += f"📖 Класс: {player.player_class} (ур. {player.class_level})\n"
                text += f"📊 Очки навыков: {player.stat_points}\n"
                text += f"⚔️ Сила: {player.strength}\n"
                text += f"🏹 Ловкость: {player.dexterity}\n"
                text += f"🔮 Интеллект: {player.intelligence}\n"
                text += f"🛡️ Живучесть: {player.vitality}\n"
            text += f"\n⚡ Энергия: {player.energy}/{player.max_energy}"
            text += f"\n🔮 Магия: {player.magic}/{player.max_magic}"
            text += f"\n❤️ Здоровье: {player.health}/{player.max_health}"
            text += f"\n💰 Золото: {player.gold}"
            text += f"\n🪙 DSTN: {player.destiny_tokens}"
            text += f"\n🎒 Предметов: {len(player.inventory)}"
            text += f"\n📜 Заданий выполнено: {len(player.completed_quests)}"
            text += f"\n🏠 Уровень дома: {player.house_level}"
            
            markup = telebot.types.InlineKeyboardMarkup()
            if player.stat_points > 0:
                markup.add(telebot.types.InlineKeyboardButton("📈 Распределить очки", callback_data="stats_menu"))
            markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_location"))
            
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id)
            return
        
        # МЕНЮ СТАТОВ
        if call.data == "stats_menu":
            if player.stat_points <= 0:
                bot.answer_callback_query(call.id, "❌ Нет очков навыков")
                return
            
            text = f"📈 *Распределение очков*\n\n"
            text += f"📊 Доступно: {player.stat_points}\n\n"
            text += f"⚔️ Сила: {player.strength} (+1 урон)\n"
            text += f"🏹 Ловкость: {player.dexterity} (+1% уклонения)\n"
            text += f"🔮 Интеллект: {player.intelligence} (+2 маг урон, +5 маны)\n"
            text += f"🛡️ Живучесть: {player.vitality} (+10 здоровья, +1 защиты)\n"
            
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                telebot.types.InlineKeyboardButton("⚔️ +1 Сила", callback_data="upgrade_stat:strength"),
                telebot.types.InlineKeyboardButton("🏹 +1 Ловкость", callback_data="upgrade_stat:dexterity"),
                telebot.types.InlineKeyboardButton("🔮 +1 Интеллект", callback_data="upgrade_stat:intelligence"),
                telebot.types.InlineKeyboardButton("🛡️ +1 Живучесть", callback_data="upgrade_stat:vitality")
            )
            markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="status"))
            
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id)
            return
        
        # УЛУЧШЕНИЕ СТАТОВ
        if call.data.startswith("upgrade_stat:"):
            if player.stat_points <= 0:
                bot.answer_callback_query(call.id, "❌ Нет очков навыков")
                return
            
            stat = call.data.split(":")[1]
            if stat == "strength":
                player.strength += 1
            elif stat == "dexterity":
                player.dexterity += 1
            elif stat == "intelligence":
                player.intelligence += 1
            elif stat == "vitality":
                player.vitality += 1
                player.max_health += 10
                player.health += 10
            
            player.stat_points -= 1
            bot.answer_callback_query(call.id, f"✅ +1 к {stat}")
            call.data = "stats_menu"
            handle_callback(call)
            return
        
        # ЗАДАНИЯ
        if call.data == "quests":
            text = "📜 *Твои задания*\n\n"
            
            if not player.accepted_quests:
                text += "У тебя нет принятых заданий."
            else:
                for quest_id in player.accepted_quests:
                    if quest_id in quest_data.get("quests", {}):
                        quest = quest_data["quests"][quest_id]
                        text += f"*{quest['name']}*\n"
                        text += f"{quest['description']}\n"
                        text += f"Награда: {quest['rewards'].get('gold', 0)}💰"
                        if 'token' in quest['rewards']:
                            text += f", {quest['rewards']['token']} DSTN"
                        if 'item' in quest['rewards']:
                            item_name = quest_data["items"][quest['rewards']['item']]['name']
                            text += f", {item_name}"
                        text += "\n\n"
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_location"))
            
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id)
            return
        
        # ВОЗВРАТ К ЛОКАЦИИ
        if call.data == "back_to_location":
            show_location(call.message, player)
            bot.answer_callback_query(call.id)
            return
        
        # ОБРАБОТКА ДЕЙСТВИЙ
        if call.data.startswith("action:"):
            parts = call.data.split(':')
            if len(parts) >= 4:
                action_type = parts[1]
                next_loc = parts[2]
                action_index = int(parts[3])
                
                current_location = quest_data["locations"][player.location]
                actions = current_location.get('actions', [])
                
                if action_index < len(actions):
                    action = actions[action_index]
                    
                    energy_cost = action.get('energy_cost', 0)
                    if energy_cost > player.energy:
                        bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                        return
                    
                    # ПЕРЕДВИЖЕНИЕ
                    if action_type == "move":
                        player.energy -= energy_cost
                        player.location = next_loc
                        player.combat_state = None
                        bot.answer_callback_query(call.id, "✅ Идём...")
                        show_location(call.message, player)
                    
                    # ВЗЯТЬ ПРЕДМЕТ
                    elif action_type == "take_item":
                        item_id = action.get('item')
                        if item_id and item_id in quest_data.get("items", {}):
                            player.add_item(item_id)
                            player.energy -= energy_cost
                            player.location = next_loc
                            bot.answer_callback_query(call.id, f"✅ Ты взял {quest_data['items'][item_id]['name']}")
                            show_location(call.message, player)
                    
                    # ОТДЫХ
                    elif action_type == "rest":
                        cooldown = action.get('cooldown', 0)
                        current_time = time.time()
                        
                        if cooldown > 0 and hasattr(player, 'last_rest_time'):
                            time_passed = current_time - player.last_rest_time
                            if time_passed < cooldown:
                                remaining = int((cooldown - time_passed) / 60)
                                bot.answer_callback_query(call.id, f"⏳ Отдых ещё не доступен. Подожди {remaining} мин.")
                                return
                        
                        energy_gain = action.get('energy_gain', 10)
                        magic_gain = action.get('magic_gain', 0)
                        player.energy = min(player.energy + energy_gain, player.max_energy)
                        player.magic = min(player.magic + magic_gain, player.max_magic)
                        player.last_rest_time = current_time
                        player.last_update = time.time()
                        player.last_magic_update = time.time()
                        bot.answer_callback_query(call.id, f"✅ Отдохнул! +{energy_gain} энергии, +{magic_gain} магии")
                        show_location(call.message, player)
                    
                    # БЕСПЛАТНЫЙ ОТДЫХ
                    elif action_type == "free_rest":
                        energy_gain = action.get('energy_gain', 10)
                        player.energy = min(player.energy + energy_gain, player.max_energy)
                        player.last_update = time.time()
                        bot.answer_callback_query(call.id, f"✅ Ты отдохнул! +{energy_gain} энергии")
                        show_location(call.message, player)
                    
                    # КОПКА ЧЕРВЕЙ
                    elif action_type == "dig_worms":
                        energy_cost = action.get('energy_cost', 2)
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        worms_found = random.randint(1, 3)
                        player.energy -= energy_cost
                        player.add_item("worm")
                        if worms_found > 1:
                            for _ in range(worms_found - 1):
                                player.add_item("worm")
                        
                        bot.answer_callback_query(call.id, f"🪱 Ты накопал {worms_found} червей!")
                        show_location(call.message, player)
                    
                    # СБОР ТРАВ
                    elif action_type == "gather_herbs":
                        energy_cost = action.get('energy_cost', 2)
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        sickle = None
                        harvest_bonus = 0
                        rare_chance = 0
                        
                        if player.has_item("diamond_sickle"):
                            sickle = "diamond_sickle"
                        elif player.has_item("golden_sickle"):
                            sickle = "golden_sickle"
                        elif player.has_item("iron_sickle"):
                            sickle = "iron_sickle"
                        elif player.has_item("wooden_sickle"):
                            sickle = "wooden_sickle"
                        else:
                            bot.answer_callback_query(call.id, "❌ У тебя нет серпа! Купи у торговца.")
                            return
                        
                        sickle_data = quest_data["items"][sickle]
                        harvest_bonus = sickle_data.get('harvest_bonus', 0)
                        rare_chance = sickle_data.get('rare_chance', 0)
                        
                        if not hasattr(player, 'sickle_durability'):
                            player.sickle_durability = {}
                        
                        if sickle not in player.sickle_durability:
                            player.sickle_durability[sickle] = sickle_data.get('durability', 30)
                        
                        if player.sickle_durability[sickle] <= 0:
                            player.remove_item(sickle)
                            bot.answer_callback_query(call.id, "❌ Твой серп сломался!")
                            return
                        
                        player.energy -= energy_cost
                        player.sickle_durability[sickle] -= 1
                        
                        r = random.random()
                        if r < 0.4:
                            herb = "oregano"
                            base_amount = random.randint(1, 3)
                        elif r < 0.7:
                            herb = "basil"
                            base_amount = random.randint(1, 3)
                        else:
                            herb = "thyme"
                            base_amount = random.randint(1, 3)
                        
                        total_amount = base_amount + harvest_bonus
                        
                        for _ in range(total_amount):
                            player.add_item(herb)
                        
                        herb_name = quest_data["items"][herb]['name']
                        result_text = f"🌿 Ты собрал {total_amount} {herb_name}!"
                        
                        if random.random() * 100 < rare_chance:
                            rare_herbs = ["forest_berries", "mint", "fire_flower"]
                            rare_herb = random.choice(rare_herbs)
                            player.add_item(rare_herb)
                            rare_name = quest_data["items"][rare_herb]['name']
                            result_text += f"\n✨ Ты нашёл редкую траву: {rare_name}!"
                        
                        if player.sickle_durability[sickle] <= 0:
                            player.remove_item(sickle)
                            result_text += f"\n❌ Твой серп сломался."
                        else:
                            result_text += f"\nОсталось прочности: {player.sickle_durability[sickle]}"
                        
                        bot.answer_callback_query(call.id, result_text)
                        show_location(call.message, player)
                    
                    # СБОР ОВОЩЕЙ
                    elif action_type == "gather_vegetables":
                        energy_cost = action.get('energy_cost', 3)
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        hoe = None
                        harvest_bonus = 0
                        rare_chance = 0
                        
                        if player.has_item("diamond_hoe"):
                            hoe = "diamond_hoe"
                        elif player.has_item("golden_hoe"):
                            hoe = "golden_hoe"
                        elif player.has_item("iron_hoe"):
                            hoe = "iron_hoe"
                        elif player.has_item("wooden_hoe"):
                            hoe = "wooden_hoe"
                        else:
                            bot.answer_callback_query(call.id, "❌ У тебя нет мотыги! Купи у торговца.")
                            return
                        
                        hoe_data = quest_data["items"][hoe]
                        harvest_bonus = hoe_data.get('harvest_bonus', 0)
                        rare_chance = hoe_data.get('rare_chance', 0)
                        
                        if not hasattr(player, 'hoe_durability'):
                            player.hoe_durability = {}
                        
                        if hoe not in player.hoe_durability:
                            player.hoe_durability[hoe] = hoe_data.get('durability', 30)
                        
                        if player.hoe_durability[hoe] <= 0:
                            player.remove_item(hoe)
                            bot.answer_callback_query(call.id, "❌ Твоя мотыга сломалась!")
                            return
                        
                        player.energy -= energy_cost
                        player.hoe_durability[hoe] -= 1
                        
                        r = random.random()
                        if r < 0.4:
                            veg = "potato"
                            base_amount = random.randint(1, 4)
                        elif r < 0.7:
                            veg = "cabbage"
                            base_amount = random.randint(1, 2)
                        elif r < 0.9:
                            veg = "carrot"
                            base_amount = random.randint(1, 3)
                        else:
                            veg = "onion"
                            base_amount = random.randint(1, 2)
                        
                        total_amount = base_amount + harvest_bonus
                        
                        for _ in range(total_amount):
                            player.add_item(veg)
                        
                        veg_name = quest_data["items"][veg]['name']
                        result_text = f"🥕 Ты собрал {total_amount} {veg_name}!"
                        
                        if random.random() * 100 < rare_chance:
                            extra_veg = random.choice(["carrot", "potato"])
                            player.add_item(extra_veg)
                            extra_name = quest_data["items"][extra_veg]['name']
                            result_text += f"\n✨ Бонус: {extra_name}!"
                        
                        if player.hoe_durability[hoe] <= 0:
                            player.remove_item(hoe)
                            result_text += f"\n❌ Твоя мотыга сломалась."
                        else:
                            result_text += f"\nОсталось прочности: {player.hoe_durability[hoe]}"
                        
                        bot.answer_callback_query(call.id, result_text)
                        show_location(call.message, player)
                    
                    # РЫБАЛКА
                    elif action_type == "fish_with_bait":
                        bait = action.get('bait')
                        energy_cost = action.get('energy_cost', 2)
                        
                        if not player.has_item(bait):
                            bot.answer_callback_query(call.id, f"❌ У тебя нет такой наживки!")
                            return
                        
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        fishing_rod = None
                        rod_bonus = 0
                        extra_fish = 0
                        gem_chance = 0
                        
                        if player.has_item("premium_fishing_rod"):
                            fishing_rod = "premium_fishing_rod"
                        elif player.has_item("carbon_fishing_rod"):
                            fishing_rod = "carbon_fishing_rod"
                        elif player.has_item("bamboo_fishing_rod"):
                            fishing_rod = "bamboo_fishing_rod"
                        elif player.has_item("wooden_fishing_rod"):
                            fishing_rod = "wooden_fishing_rod"
                        else:
                            bot.answer_callback_query(call.id, "❌ У тебя нет удочки! Купи у торговца.")
                            return
                        
                        rod_data = quest_data["items"][fishing_rod]
                        rod_bonus = rod_data.get('bait_bonus', 0)
                        extra_fish = 0
                        if fishing_rod == "carbon_fishing_rod":
                            extra_fish = 1
                        elif fishing_rod == "premium_fishing_rod":
                            extra_fish = 2
                            gem_chance = rod_data.get('gem_chance', 3)
                        
                        if not hasattr(player, 'fishing_rod_durability'):
                            player.fishing_rod_durability = {}
                        
                        if fishing_rod not in player.fishing_rod_durability:
                            player.fishing_rod_durability[fishing_rod] = rod_data.get('durability', 30)
                        
                        if player.fishing_rod_durability[fishing_rod] <= 0:
                            player.remove_item(fishing_rod)
                            bot.answer_callback_query(call.id, "❌ Твоя удочка сломалась!")
                            return
                        
                        player.fishing_rod_durability[fishing_rod] -= 1
                        player.energy -= energy_cost
                        player.remove_item(bait)
                        
                        if bait == "worm":
                            r = random.random() * 100
                            if r < 70 - rod_bonus:
                                fish = "carp"
                            elif r < 90 - rod_bonus:
                                fish = "perch"
                            elif r < 99 - rod_bonus:
                                fish = "pike"
                            else:
                                fish = "golden_fish"
                        elif bait == "bread":
                            r = random.random() * 100
                            if r < 60 - rod_bonus:
                                fish = "carp"
                            elif r < 90 - rod_bonus:
                                fish = "perch"
                            elif r < 99 - rod_bonus:
                                fish = "pike"
                            else:
                                fish = "golden_fish"
                        else:
                            r = random.random() * 100
                            if r < 50 - rod_bonus:
                                fish = "carp"
                            elif r < 85 - rod_bonus:
                                fish = "perch"
                            elif r < 99 - rod_bonus:
                                fish = "pike"
                            else:
                                fish = "golden_fish"
                        
                        player.add_item(fish)
                        player.achievement_stats["fish_caught"] += 1 + extra_fish
                        fish_name = quest_data["items"][fish]['name']
                        result_text = f"🎣 Ты поймал {fish_name}!"
                        
                        for _ in range(extra_fish):
                            player.add_item(fish)
                            result_text += f"\n🎣 +1 {fish_name} (бонус удочки)!"
                        
                        if "catch_fish" in player.daily_quests:
                            quest = player.daily_quests["catch_fish"]
                            if not quest["completed"]:
                                player.daily_quest_progress["catch_fish"] = player.daily_quest_progress.get("catch_fish", 0) + 1 + extra_fish
                                quest_info = quest_data["daily_quests"]["catch_fish"]
                                if player.daily_quest_progress["catch_fish"] >= quest_info['requirements']['count']:
                                    quest["completed"] = True
                                    result_text += f"\n✅ Задание '{quest_info['name']}' выполнено!"
                        
                        if "weekly_fisher" in player.weekly_quests:
                            quest = player.weekly_quests["weekly_fisher"]
                            if not quest["completed"]:
                                player.weekly_progress["weekly_fisher"] = player.weekly_progress.get("weekly_fisher", 0) + 1 + extra_fish
                                quest_info = quest_data["weekly_quests"]["weekly_fisher"]
                                if player.weekly_progress["weekly_fisher"] >= quest_info['requirements']['count']:
                                    quest["completed"] = True
                                    result_text += f"\n✅ Еженедельное задание выполнено!"
                        
                        if gem_chance > 0 and random.random() * 100 < gem_chance:
                            gems = ["ruby", "diamond", "sapphire", "emerald"]
                            gem = random.choice(gems)
                            player.add_item(gem)
                            gem_name = quest_data["items"][gem]['name']
                            result_text += f"\n✨ Ты нашёл {gem_name}! 🎉"
                        
                        durability_left = player.fishing_rod_durability[fishing_rod]
                        if durability_left <= 0:
                            player.remove_item(fishing_rod)
                            result_text += f"\n❌ Твоя удочка сломалась."
                        else:
                            result_text += f"\nОсталось прочности: {durability_left}"
                        
                        bot.answer_callback_query(call.id, result_text)
                        show_location(call.message, player)
                    
                    # ЖАРКА РЫБЫ
                    elif action_type == "cook_fish":
                        fish_types = ["carp", "perch", "pike", "golden_fish"]
                        fish_found = None
                        
                        for fish in fish_types:
                            if player.has_item(fish):
                                fish_found = fish
                                break
                        
                        if not fish_found:
                            bot.answer_callback_query(call.id, "❌ У тебя нет рыбы для жарки!")
                            return
                        
                        player.remove_item(fish_found)
                        player.add_item("fried_fish")
                        player.achievement_stats["meals_cooked"] += 1
                        bot.answer_callback_query(call.id, "🍳 Ты пожарил рыбу! Получилась жареная рыбка.")
                        show_location(call.message, player)
                    
                    # ЖАРКА МЯСА
                    elif action_type == "cook_meat":
                        meat_types = ["bear_meat", "moose_meat", "wolf_meat", "beast_meat"]
                        meat_found = None
                        
                        for meat in meat_types:
                            if player.has_item(meat):
                                meat_found = meat
                                break
                        
                        if not meat_found:
                            bot.answer_callback_query(call.id, "❌ У тебя нет мяса для жарки!")
                            return
                        
                        player.remove_item(meat_found)
                        player.add_item("fried_meat")
                        player.achievement_stats["meals_cooked"] += 1
                        bot.answer_callback_query(call.id, "🍳 Ты пожарил мясо! Получилось жареное мясо.")
                        show_location(call.message, player)
                    
                    # ДОБЫЧА РУДЫ
                    elif action_type == "mine_ore":
                        if not (player.has_item("stone_pickaxe") or player.has_item("iron_pickaxe") or player.has_item("premium_pickaxe")):
                            bot.answer_callback_query(call.id, "❌ У тебя нет кирки! Купи у торговца.")
                            return
                        
                        energy_cost = action.get('energy_cost', 2)
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        pickaxe = None
                        if player.has_item("premium_pickaxe"):
                            pickaxe = "premium_pickaxe"
                        elif player.has_item("iron_pickaxe"):
                            pickaxe = "iron_pickaxe"
                        elif player.has_item("stone_pickaxe"):
                            pickaxe = "stone_pickaxe"
                        
                        if not hasattr(player, 'pickaxe_durability'):
                            player.pickaxe_durability = {}
                        
                        if pickaxe not in player.pickaxe_durability:
                            item_data = quest_data["items"][pickaxe]
                            player.pickaxe_durability[pickaxe] = item_data.get('durability', 100)
                        
                        if player.pickaxe_durability[pickaxe] <= 0:
                            player.remove_item(pickaxe)
                            bot.answer_callback_query(call.id, "❌ Твоя кирка сломалась!")
                            return
                        
                        player.pickaxe_durability[pickaxe] -= 1
                        player.energy -= energy_cost
                        
                        r = random.random()
                        if r < 0.4:
                            ore = "copper_ore"
                        elif r < 0.7:
                            ore = "iron_ore"
                        elif r < 0.9:
                            ore = "tin_ore"
                        else:
                            ore = "gold_ore"
                        
                        player.add_item(ore)
                        player.achievement_stats["ore_mined"] += 1
                        ore_name = quest_data["items"][ore]['name']
                        result_text = f"⛏️ Ты добыл {ore_name}!"
                        
                        if "mine_ore" in player.daily_quests:
                            quest = player.daily_quests["mine_ore"]
                            if not quest["completed"]:
                                player.daily_quest_progress["mine_ore"] = player.daily_quest_progress.get("mine_ore", 0) + 1
                                quest_info = quest_data["daily_quests"]["mine_ore"]
                                if player.daily_quest_progress["mine_ore"] >= quest_info['requirements']['count']:
                                    quest["completed"] = True
                                    result_text += f"\n✅ Задание '{quest_info['name']}' выполнено!"
                        
                        if "weekly_miner" in player.weekly_quests:
                            quest = player.weekly_quests["weekly_miner"]
                            if not quest["completed"]:
                                player.weekly_progress["weekly_miner"] = player.weekly_progress.get("weekly_miner", 0) + 1
                                quest_info = quest_data["weekly_quests"]["weekly_miner"]
                                if player.weekly_progress["weekly_miner"] >= quest_info['requirements']['count']:
                                    quest["completed"] = True
                                    result_text += f"\n✅ Еженедельное задание выполнено!"
                        
                        if pickaxe == "premium_pickaxe":
                            gem_chance = quest_data["items"][pickaxe].get('gem_chance', 5)
                            if random.random() * 100 < gem_chance:
                                gems = ["ruby", "diamond", "sapphire", "emerald", "ancient_coin"]
                                gem = random.choice(gems)
                                player.add_item(gem)
                                gem_name = quest_data["items"][gem]['name']
                                result_text += f"\n✨ И вдобавок ты нашёл {gem_name}! 🎉"
                        
                        if player.pickaxe_durability[pickaxe] <= 0:
                            player.remove_item(pickaxe)
                            result_text += f"\n❌ Твоя кирка сломалась."
                        else:
                            durability_left = player.pickaxe_durability[pickaxe]
                            result_text += f"\nОсталось прочности: {durability_left}"
                        
                        bot.answer_callback_query(call.id, result_text)
                        show_location(call.message, player)
                    
                    # КРАФТ БРОНИ
                    elif action_type == "craft_armor":
                        bot.answer_callback_query(call.id, "⚒️ Выбери тип брони в меню")
                    
                    # КРАФТ ОРУЖИЯ
                    elif action_type == "craft_weapon":
                        bot.answer_callback_query(call.id, "⚔️ Выбери тип оружия в меню")
                    
                    # КРАФТ СТЕКЛА
                    elif action_type == "craft_glass":
                        if player.has_item("sand") and player.has_item("sand") >= 5:
                            for _ in range(5):
                                player.remove_item("sand")
                            player.add_item("glass")
                            player.energy -= energy_cost
                            bot.answer_callback_query(call.id, "🪟 Ты сделал стекло!")
                        else:
                            bot.answer_callback_query(call.id, "❌ Нужно 5 песка!")
                        show_location(call.message, player)
                    
                    # ДОБЫЧА ПЕСКА
                    elif action_type == "gather_sand":
                        energy_cost = action.get('energy_cost', 3)
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        sand_min = action.get('sand_min', 3)
                        sand_max = action.get('sand_max', 6)
                        sand_found = random.randint(sand_min, sand_max)
                        
                        player.energy -= energy_cost
                        for _ in range(sand_found):
                            player.add_item("sand")
                        
                        bot.answer_callback_query(call.id, f"🏖️ Ты накопал {sand_found} песка!")
                        show_location(call.message, player)
                    
                    # КУПИТЬ ПИВО
                    elif action_type == "buy_beer":
                        price = action.get('price', 5)
                        energy_gain = action.get('energy_gain', 5)
                        
                        if player.gold >= price:
                            player.gold -= price
                            player.energy = min(player.energy + energy_gain, player.max_energy)
                            bot.answer_callback_query(call.id, f"🍺 Ты выпил эля! +{energy_gain} энергии")
                        else:
                            bot.answer_callback_query(call.id, f"❌ Не хватает золота! Нужно {price}💰")
                        
                        show_location(call.message, player)
                    
                    # ПОСЛУШАТЬ СЛУХИ
                    elif action_type == "gather_rumors":
                        energy_cost = action.get('energy_cost', 1)
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        player.energy -= energy_cost
                        
                        rumors = [
                            "Говорят, в глубинах шахты проснулся древний дракон...",
                            "Кто-то нашёл золотую морковь, светящуюся в темноте!",
                            "Старый гоблин-торговец ищет редкие самоцветы.",
                            "В вулкане видели огненного элементаля!",
                            "На мосту перед драконом кто-то оставил рюкзак..."
                        ]
                        
                        bot.answer_callback_query(call.id, random.choice(rumors))
                        show_location(call.message, player)
                    
                    # ПРОМЫВКА ПЕСКА
                    elif action_type == "wash_sand":
                        energy_cost = action.get('energy_cost', 4)
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        if not player.has_item("sand") or player.inventory.count("sand") < 3:
                            bot.answer_callback_query(call.id, "❌ Нужно минимум 3 песка!")
                            return
                        
                        for _ in range(3):
                            player.remove_item("sand")
                        
                        player.energy -= energy_cost
                        
                        if random.random() < 0.3:
                            gems = ["ruby", "diamond", "sapphire", "emerald"]
                            gem = random.choice(gems)
                            player.add_item(gem)
                            gem_name = quest_data["items"][gem]['name']
                            bot.answer_callback_query(call.id, f"💎 Ты нашёл {gem_name} при промывке!")
                        else:
                            player.add_item("gold_ore")
                            bot.answer_callback_query(call.id, "✨ Ты нашёл крупинки золота!")
                        
                        show_location(call.message, player)
                    
                    # ПОИСК В ОТВАЛАХ
                    elif action_type == "search_debris":
                        energy_cost = action.get('energy_cost', 2)
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        player.energy -= energy_cost
                        
                        r = random.random()
                        if r < 0.4:
                            player.add_item("copper_ore")
                            bot.answer_callback_query(call.id, "🔍 Ты нашёл кусок медной руды!")
                        elif r < 0.7:
                            player.add_item("iron_ore")
                            bot.answer_callback_query(call.id, "🔍 Ты нашёл железную руду!")
                        elif r < 0.9:
                            player.add_item("ancient_coin")
                            bot.answer_callback_query(call.id, "🪙 Ты нашёл древнюю монету!")
                        else:
                            bot.answer_callback_query(call.id, "🔍 Ты ничего не нашёл...")
                        
                        show_location(call.message, player)
                    
                    # КУПИТЬ ПРЕДМЕТ
                    elif action_type == "buy_item":
                        item_id = action.get('item')
                        price = action.get('price', 0)
                        
                        if item_id in quest_data.get("items", {}):
                            if player.gold >= price:
                                player.gold -= price
                                player.add_item(item_id)
                                bot.answer_callback_query(call.id, f"✅ Ты купил {quest_data['items'][item_id]['name']}")
                            else:
                                bot.answer_callback_query(call.id, f"❌ Не хватает золота! Нужно {price}💰")
                        
                        show_location(call.message, player)
                    
                    # КУПИТЬ ПРЕМИУМ ПРЕДМЕТ
                    elif action_type == "premium_item":
                        item_id = action.get('item')
                        stars_cost = action.get('stars', 0)
                        
                        bot.answer_callback_query(call.id, "⭐ Эта функция будет доступна позже")
                        show_location(call.message, player)
                    
                    # ПРОДАТЬ ПРЕДМЕТ
                    elif action_type == "sell_item":
                        item_id = action.get('item')
                        price = action.get('price', 0)
                        
                        if player.has_item(item_id):
                            player.remove_item(item_id)
                            player.gold += price
                            bot.answer_callback_query(call.id, f"✅ Ты продал предмет за {price}💰")
                        else:
                            bot.answer_callback_query(call.id, "❌ У тебя нет этого предмета")
                        
                        show_location(call.message, player)
                    
                    # ПРИНЯТЬ ЗАДАНИЕ
                    elif action_type == "accept_quest":
                        quest_id = action.get('quest_id')
                        if quest_id:
                            player.accept_quest(quest_id)
                            bot.answer_callback_query(call.id, "✅ Задание принято!")
                            player.location = next_loc
                            show_location(call.message, player)
                    
                    # КУПИТЬ ЗАКЛИНАНИЕ
                    elif action_type == "buy_spell":
                        spell_id = action.get('spell')
                        price = action.get('price', 0)
                        
                        if spell_id in quest_data.get("spells", {}):
                            if player.gold >= price:
                                if spell_id not in player.spells:
                                    player.gold -= price
                                    player.spells.append(spell_id)
                                    bot.answer_callback_query(call.id, f"✅ Ты выучил {quest_data['spells'][spell_id]['name']}!")
                                else:
                                    bot.answer_callback_query(call.id, "❌ Ты уже знаешь это заклинание")
                            else:
                                bot.answer_callback_query(call.id, f"❌ Не хватает золота! Нужно {price}💰")
                        
                        show_location(call.message, player)
                    
                    # ПОКАЗАТЬ ЗАКЛИНАНИЯ
                    elif action_type == "show_spells":
                        if not player.spells:
                            bot.answer_callback_query(call.id, "❌ У тебя нет заклинаний")
                            return
                        
                        text = "🔮 *Твои заклинания:*\n\n"
                        for spell_id in player.spells:
                            if spell_id in quest_data.get("spells", {}):
                                spell = quest_data["spells"][spell_id]
                                text += f"• {spell['name']}: {spell['description']}\n"
                                text += f"  Мана: {spell['magic_cost']}, КД: {spell['cooldown']}ч\n\n"
                        
                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_location"))
                        
                        bot.edit_message_text(
                            text,
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup,
                            parse_mode='Markdown'
                        )
                        bot.answer_callback_query(call.id)
                    
                    # ПОКАЗАТЬ ДОСТИЖЕНИЯ
                    elif action_type == "show_achievements":
                        text = "🏆 *Мои достижения:*\n\n"
                        
                        for ach_id, ach in quest_data.get("achievements", {}).items():
                            if ach_id in player.achievements:
                                text += f"✅ *{ach['name']}* - {ach['description']}\n"
                            else:
                                completed = False
                                if "wolf" in ach_id and player.achievement_stats.get("wolves_killed", 0) >= int(ach_id.split("_")[-1]):
                                    completed = True
                                elif "fisher" in ach_id and player.achievement_stats.get("fish_caught", 0) >= int(ach_id.split("_")[-1]):
                                    completed = True
                                elif "miner" in ach_id and player.achievement_stats.get("ore_mined", 0) >= int(ach_id.split("_")[-1]):
                                    completed = True
                                elif "chef" in ach_id and player.achievement_stats.get("meals_cooked", 0) >= int(ach_id.split("_")[-1]):
                                    completed = True
                                elif ach_id == "first_blood" and player.achievement_stats.get("wolves_killed", 0) > 0:
                                    completed = True
                                
                                if completed:
                                    text += f"🎯 *{ach['name']}* - ГОТОВО К ПОЛУЧЕНИЮ!\n"
                                    text += f"Награда: {ach['rewards'].get('gold', 0)}💰, {ach['rewards'].get('token', 0)} DSTN"
                                    if 'item' in ach['rewards']:
                                        item_name = quest_data["items"][ach['rewards']['item']]['name']
                                        text += f", {item_name}"
                                    text += "\n\n"
                                else:
                                    text += f"⭕ *{ach['name']}* - {ach['description']}\n"
                        
                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_location"))
                        
                        bot.edit_message_text(
                            text,
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup,
                            parse_mode='Markdown'
                        )
                        bot.answer_callback_query(call.id)
                    
                    # ПОЛУЧИТЬ ЕЖЕДНЕВНУЮ НАГРАДУ
                    elif action_type == "claim_daily_reward":
                        success, result = player.claim_daily_reward()
                        
                        if not success:
                            bot.answer_callback_query(call.id, result)
                            return
                        
                        day = result
                        reward_data = quest_data["daily_rewards"][f"day{day}"]
                        rewards = reward_data['rewards']
                        
                        player.gold += rewards.get('gold', 0)
                        player.destiny_tokens += rewards.get('token', 0)
                        if 'energy_refill' in rewards:
                            player.energy = min(player.energy + rewards['energy_refill'], player.max_energy)
                        if 'item' in rewards:
                            player.add_item(rewards['item'])
                        
                        reward_text = f"🎁 *День {day}* - Ты получил:\n"
                        if 'gold' in rewards:
                            reward_text += f"💰 +{rewards['gold']} золота\n"
                        if 'token' in rewards:
                            reward_text += f"🪙 +{rewards['token']} DSTN\n"
                        if 'energy_refill' in rewards:
                            reward_text += f"⚡ +{rewards['energy_refill']} энергии\n"
                        if 'item' in rewards:
                            item_name = quest_data["items"][rewards['item']]['name']
                            reward_text += f"📦 {item_name}\n"
                        
                        reward_text += f"\n📅 Твоя серия: *{day}/7* дней"
                        
                        bot.send_message(call.message.chat.id, reward_text, parse_mode='Markdown')
                        bot.answer_callback_query(call.id, "✅ Награда получена!")
                        show_location(call.message, player)
                    
                    # ОБЫСК ЗАЛА
                    elif action_type == "search_room" or action_type == "search_altar":
                        energy_cost = action.get('energy_cost', 2)
                        success_chance = action.get('success_chance', 40)
                        gold_min = action.get('gold_min', 5)
                        gold_max = action.get('gold_max', 15)
                        token_min = action.get('token_min', 2)
                        token_max = action.get('token_max', 8)
                        
                        if player.energy < energy_cost:
                            bot.answer_callback_query(call.id, "❌ Недостаточно энергии!")
                            return
                        
                        player.energy -= energy_cost
                        
                        if random.random() * 100 < success_chance:
                            gold_found = random.randint(gold_min, gold_max)
                            tokens_found = random.randint(token_min, token_max)
                            player.gold += gold_found
                            player.destiny_tokens += tokens_found
                            
                            result_text = f"✅ Ты нашёл: {gold_found}💰 золота и {tokens_found} DSTN!"
                        else:
                            result_text = "❌ Ты ничего не нашёл. Похоже, здесь уже всё разграблено."
                        
                        bot.answer_callback_query(call.id, result_text)
                        show_location(call.message, player)
                    
                    # КУПИТЬ СЕМЕНА
                    elif action_type == "buy_premium_seeds":
                        item_id = action.get('item')
                        stars = action.get('stars', 0)
                        
                        if item_id in quest_data.get("items", {}):
                            player.add_item(item_id)
                            bot.answer_callback_query(call.id, f"✅ Ты купил {quest_data['items'][item_id]['name']}")
                        
                        show_location(call.message, player)
                    
                    # ПОСТРОИТЬ ДОМИК
                    elif action_type == "build_house":
                        if player.house_level == 0:
                            if player.has_item("wood") and player.has_item("stone") and player.has_item("iron_ingot") and player.has_item("glass"):
                                if player.inventory.count("wood") >= 100 and player.inventory.count("stone") >= 100 and player.inventory.count("iron_ingot") >= 20 and player.inventory.count("glass") >= 10:
                                    for _ in range(100):
                                        player.remove_item("wood")
                                    for _ in range(100):
                                        player.remove_item("stone")
                                    for _ in range(20):
                                        player.remove_item("iron_ingot")
                                    for _ in range(10):
                                        player.remove_item("glass")
                                    
                                    player.house_level = 1
                                    player.location = "house_level1"
                                    bot.answer_callback_query(call.id, "🏠 Ты построил домик!")
                                else:
                                    bot.answer_callback_query(call.id, "❌ Не хватает ресурсов! Нужно: 100🪵, 100🪨, 20🔩, 10🪟")
                            else:
                                bot.answer_callback_query(call.id, "❌ У тебя нет нужных ресурсов!")
                        else:
                            bot.answer_callback_query(call.id, "❌ У тебя уже есть домик!")
                        
                        show_location(call.message, player)
                    
                    # ОТДЫХ НА МОСТУ
                    elif action_type == "rest_on_bridge":
                        energy_gain = action.get('energy_gain', 10)
                        player.energy = min(player.energy + energy_gain, player.max_energy)
                        
                        if player.has_item("leather"):
                            player.remove_item("leather")
                            bot.send_message(call.message.chat.id, "🔥 Твоя шкура сгорела в костре!")
                        
                        if "burnt_leather" not in player.achievements:
                            player.achievements.append("burnt_leather")
                            bot.send_message(call.message.chat.id, "🏆 Достижение 'Пожарный' получено!")
                        
                        bot.answer_callback_query(call.id, f"✅ Ты отдохнул! +{energy_gain} энергии")
                        show_location(call.message, player)
                    
                    # ТЕЛЕПОРТ
                    elif action_type == "teleport_menu":
                        text = "✨ *Куда телепортироваться?*\n\n"
                        text += "📍 Лесная опушка\n"
                        text += "📍 Деревенская площадь\n"
                        text += "📍 Берег озера\n"
                        text += "📍 Твой домик"
                        
                        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                        markup.add(
                            telebot.types.InlineKeyboardButton("🌲 Опушка", callback_data="teleport:start"),
                            telebot.types.InlineKeyboardButton("🏘️ Площадь", callback_data="teleport:village"),
                            telebot.types.InlineKeyboardButton("🏞️ Берег озера", callback_data="teleport:lake_shore"),
                            telebot.types.InlineKeyboardButton("🏠 Домик", callback_data="teleport:house_level5"),
                            telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_location")
                        )
                        
                        bot.edit_message_text(
                            text,
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup,
                            parse_mode='Markdown'
                        )
                        bot.answer_callback_query(call.id)
                    
                    elif action_type == "teleport":
                        target = call.data.split(":")[1]
                        current_time = time.time()
                        
                        if player.house_level >= 5:
                            if current_time - player.teleport_cooldown > 86400 or player.house_level < 5:
                                player.location = target
                                player.teleport_cooldown = current_time
                                bot.answer_callback_query(call.id, "✨ Телепортация!")
                                show_location(call.message, player)
                            else:
                                remaining = 86400 - (current_time - player.teleport_cooldown)
                                hours = int(remaining // 3600)
                                minutes = int((remaining % 3600) // 60)
                                bot.answer_callback_query(call.id, f"⏳ Телепорт ещё не готов. Подожди {hours}ч {minutes}мин")
                        else:
                            bot.answer_callback_query(call.id, "❌ Телепорт доступен только с 5 уровнем дома!")
                    
                    else:
                        bot.answer_callback_query(call.id, f"⚠️ Действие {action_type} в разработке")
                else:
                    bot.answer_callback_query(call.id, "⚠️ Ошибка действия")
        
        # БОЙ С МОНСТРОМ
        elif call.data.startswith("combat:"):
            parts = call.data.split(':')
            enemy_id = parts[1]
            
            if enemy_id not in quest_data.get("enemies", {}):
                bot.answer_callback_query(call.id, "❌ Враг не найден")
                return
            
            enemy = quest_data["enemies"][enemy_id]
            
            if not hasattr(player, 'combat_state') or not player.combat_state:
                player.combat_state = {
                    'enemy_id': enemy_id,
                    'enemy_health': enemy['health'],
                    'round': 1
                }
            
            player_damage = player.calculate_damage()
            
            crit = False
            if random.random() * 100 < player.crit_chance:
                crit = True
                player_damage = int(player_damage * player.crit_multiplier)
            
            player.combat_state['enemy_health'] -= player_damage
            
            battle_text = f"⚔️ *Раунд {player.combat_state['round']}*\n\n"
            if crit:
                battle_text += f"⚡ КРИТИЧЕСКИЙ УДАР! x{player.crit_multiplier}\n"
            battle_text += f"Ты нанёс *{player_damage}* урона!\n\n"
            
            enemy_max_health = enemy['health']
            current_enemy_health = player.combat_state['enemy_health']
            health_percent = current_enemy_health / enemy_max_health
            
            bar_length = 10
            filled = int(health_percent * bar_length)
            health_bar = "█" * filled + "░" * (bar_length - filled)
            
            battle_text += f"🐺 *{enemy['name']}*\n"
            battle_text += f"`[{health_bar}]` {current_enemy_health}/{enemy_max_health} ❤️\n\n"
            
            if current_enemy_health <= 0:
                battle_text += "🎉 *Враг повержен!* 🎉\n\n"
                battle_text += "Награда:\n"
                if 'rewards' in enemy:
                    player.gold += enemy['rewards'].get('gold', 0)
                    player.destiny_tokens += enemy['rewards'].get('token', 0)
                    player.exp += enemy['rewards'].get('exp', 0)
                    for item in enemy['rewards'].get('items', []):
                        player.add_item(item)
                    battle_text += f"💰 +{enemy['rewards'].get('gold', 0)} золота\n"
                    battle_text += f"🪙 +{enemy['rewards'].get('token', 0)} DSTN\n"
                    battle_text += f"✨ +{enemy['rewards'].get('exp', 0)} опыта\n"
                    battle_text += f"📦 +{len(enemy['rewards'].get('items', []))} предметов\n"
                
                if 'drop_chance' in enemy:
                    for item, chance in enemy['drop_chance'].items():
                        if random.random() * 100 < chance:
                            player.add_item(item)
                            item_name = quest_data["items"][item]['name']
                            battle_text += f"📦 Трофей: {item_name}\n"
                
                if enemy_id == "wolf":
                    player.achievement_stats["wolves_killed"] += 1
                elif enemy_id == "cave_spider":
                    player.achievement_stats["spiders_killed"] += 1
                elif enemy_id == "bear":
                    player.achievement_stats["bears_killed"] += 1
                elif enemy_id == "moose":
                    player.achievement_stats["moose_killed"] += 1
                
                if player.achievement_stats["wolves_killed"] == 1 and "first_blood" not in player.achievements:
                    player.achievements.append("first_blood")
                    battle_text += f"\n🏆 Достижение 'Первая кровь' получено!"
                
                if hasattr(player, 'daily_quests') and player.daily_quests:
                    for quest_id, quest_data_item in list(player.daily_quests.items()):
                        if not quest_data_item["completed"]:
                            quest_info = quest_data["daily_quests"][quest_id]
                            if 'enemy' in quest_info['requirements']:
                                if quest_info['requirements']['enemy'] == enemy_id:
                                    player.daily_quest_progress[quest_id] = player.daily_quest_progress.get(quest_id, 0) + 1
                                    if player.daily_quest_progress[quest_id] >= quest_info['requirements']['count']:
                                        player.daily_quests[quest_id]["completed"] = True
                                        battle_text += f"\n✅ Задание '{quest_info['name']}' выполнено!"
                
                if hasattr(player, 'weekly_quests') and player.weekly_quests:
                    for quest_id, quest_data_item in list(player.weekly_quests.items()):
                        if not quest_data_item["completed"]:
                            quest_info = quest_data["weekly_quests"][quest_id]
                            if 'enemy' in quest_info['requirements']:
                                if quest_info['requirements']['enemy'] == enemy_id:
                                    player.weekly_progress[quest_id] = player.weekly_progress.get(quest_id, 0) + 1
                                    if player.weekly_progress[quest_id] >= quest_info['requirements']['count']:
                                        player.weekly_quests[quest_id]["completed"] = True
                                        battle_text += f"\n✅ Еженедельное задание выполнено!"
                
                player.combat_state = None
                
                bot.send_message(call.message.chat.id, battle_text, parse_mode='Markdown')
                show_location(call.message, player)
                return
            
            # Ход врага
            dodge = False
            if random.random() * 100 < player.dodge_chance:
                dodge = True
            
            enemy_miss = player.blind_active or dodge
            if enemy_miss:
                player.blind_active = False
                if dodge:
                    battle_text += "✨ Ты уклонился от атаки!\n\n"
                else:
                    battle_text += "✨ *Враг ослеплён и промахивается!*\n\n"
            else:
                enemy_damage = enemy['damage'] - player.calculate_defense()
                if enemy_damage < 1:
                    enemy_damage = 1
                player.health -= enemy_damage
                
                battle_text += f"🐺 {enemy['name']} нанёс *{enemy_damage}* урона!\n\n"
            
            if player.health_regen > 0:
                player.health = min(player.health + player.health_regen, player.max_health)
                battle_text += f"💚 Регенерация восстановила {player.health_regen} здоровья\n\n"
            
            battle_text += "*Твоё состояние:*\n"
            battle_text += f"❤️ Здоровье: {player.health}/{player.max_health}\n"
            battle_text += f"🔮 Мана: {player.magic}/{player.max_magic}\n"
            battle_text += f"⚔️ Урон: {player_damage}\n"
            battle_text += f"🛡️ Защита: {player.calculate_defense()}\n"
            battle_text += f"🪙 DSTN: {player.destiny_tokens}\n"
            
            player.combat_state['round'] += 1
            
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                telebot.types.InlineKeyboardButton("⚔️ Атаковать", callback_data=f"combat:{enemy_id}"),
                telebot.types.InlineKeyboardButton("🏃 Сбежать", callback_data="back_to_location")
            )
            
            if player.spells:
                markup.add(telebot.types.InlineKeyboardButton("🔮 Магия", callback_data="show_spells"))
            
            bot.edit_message_text(
                battle_text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            
            bot.answer_callback_query(call.id)
        
        # ПОКАЗАТЬ ЗАКЛИНАНИЯ В БОЮ
        elif call.data == "show_spells":
            if not player.spells:
                bot.answer_callback_query(call.id, "❌ У тебя нет заклинаний")
                return
            
            text = "🔮 *Выбери заклинание:*\n\n"
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            
            for spell_id in player.spells:
                if spell_id in quest_data.get("spells", {}):
                    spell = quest_data["spells"][spell_id]
                    can_cast = player.can_cast_spell(spell_id)
                    
                    if can_cast and player.magic >= spell['magic_cost']:
                        callback = f"cast_spell:{spell_id}"
                        button_text = f"{spell['name']} ({spell['magic_cost']}🔮)"
                    else:
                        callback = "noop"
                        button_text = f"❌ {spell['name']} ({spell['magic_cost']}🔮)"
                    
                    markup.add(telebot.types.InlineKeyboardButton(button_text, callback_data=callback))
            
            markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_battle"))
            
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id)
        
        elif call.data.startswith("cast_spell:"):
            spell_id = call.data.split(":")[1]
            
            if spell_id not in player.spells:
                bot.answer_callback_query(call.id, "❌ У тебя нет этого заклинания")
                return
            
            spell = quest_data["spells"][spell_id]
            
            if not player.can_cast_spell(spell_id):
                bot.answer_callback_query(call.id, f"❌ Заклинание ещё не восстановлено (КД {spell['cooldown']}ч)")
                return
            
            if player.magic < spell['magic_cost']:
                bot.answer_callback_query(call.id, f"❌ Недостаточно магии! Нужно {spell['magic_cost']}")
                return
            
            player.magic -= spell['magic_cost']
            player.use_spell(spell_id)
            
            if 'damage' in spell:
                player.combat_state['enemy_health'] -= spell['damage']
                bot.answer_callback_query(call.id, f"🔥 {spell['name']} нанёс {spell['damage']} урона!")
            elif 'heal' in spell:
                player.health = min(player.health + spell['heal'], player.max_health)
                bot.answer_callback_query(call.id, f"💫 {spell['name']} восстановил {spell['heal']} здоровья!")
            elif spell_id == "blind":
                player.blind_active = True
                bot.answer_callback_query(call.id, f"✨ Враг ослеплён!")
            elif 'defense' in spell:
                player.defense_bonus += spell['defense']
                bot.answer_callback_query(call.id, f"🛡️ Защита увеличена на {spell['defense']}!")
            
            call.data = f"combat:{player.combat_state['enemy_id']}"
            handle_callback(call)
        
        elif call.data == "back_to_battle":
            if player.combat_state:
                call.data = f"combat:{player.combat_state['enemy_id']}"
                handle_callback(call)
            else:
                show_location(call.message, player)
        
        elif call.data == "noop":
            bot.answer_callback_query(call.id, "⏳ Это заклинание пока недоступно")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        bot.answer_callback_query(call.id, "⚠️ Произошла ошибка")

# ============================================
# ЗАПУСК
# ============================================
print("=" * 40)
print("🤖 LitRPG Telegram Бот")
print("=" * 40)
print("✅ Бот запускается...")
