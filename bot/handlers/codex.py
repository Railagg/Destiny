import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# ============================================
# КОНСТАНТЫ ДЛЯ ЭНЦИКЛОПЕДИИ
# ============================================

RARITY_EMOJI = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟡",
    "ancient": "🔴",
    "mythic": "💜"
}

CLASS_INFO = {
    "warrior": {
        "name": "⚔️ Мечник",
        "description": "Мастер клинка, наносящий огромный урон. Специализируется на критических ударах.",
        "health": 120,
        "damage": 15,
        "defense": 8,
        "mastery": "Критические удары наносят на 50% больше урона",
        "difficulty": "⭐"
    },
    "archer": {
        "name": "🏹 Лучник",
        "description": "Меткий стрелок, поражающий цели издалека. Высокое уклонение и точность.",
        "health": 100,
        "damage": 12,
        "defense": 5,
        "mastery": "Критические удары игнорируют 50% защиты",
        "difficulty": "⭐⭐"
    },
    "mage": {
        "name": "🔮 Маг",
        "description": "Повелитель стихий, обрушивающий на врагов мощь магии.",
        "health": 80,
        "magic_damage": 20,
        "defense": 3,
        "mastery": "Заклинания стоят на 20% меньше маны",
        "difficulty": "⭐⭐⭐"
    },
    "guardian": {
        "name": "🛡️ Страж",
        "description": "Несокрушимый защитник, принимающий удар на себя. Огромная защита.",
        "health": 180,
        "damage": 8,
        "defense": 15,
        "mastery": "Блокирует на 25% больше урона",
        "difficulty": "⭐"
    },
    "paladin": {
        "name": "⚔️✨ Паладин",
        "description": "Святой воин, сочетающий мощь меча с божественной магией. Растущий щит.",
        "health": 150,
        "damage": 10,
        "defense": 12,
        "magic_damage": 8,
        "mastery": "Щит растёт с каждым ударом (до 150)",
        "difficulty": "⭐⭐"
    },
    "rogue": {
        "name": "🗡️ Разбойник",
        "description": "Тень в ночи, мастер скрытности и смертоносных атак из тени.",
        "health": 90,
        "damage": 12,
        "defense": 4,
        "mastery": "Атаки из скрытности наносят +50% урона",
        "difficulty": "⭐⭐⭐"
    },
    "druid": {
        "name": "🌿 Друид",
        "description": "Хранитель леса, повелевающий силами природы. Может лечить и призывать.",
        "health": 110,
        "magic_damage": 12,
        "defense": 6,
        "mastery": "Призывы живут на 1 ход дольше",
        "difficulty": "⭐⭐⭐"
    },
    "warlock": {
        "name": "💀 Чернокнижник",
        "description": "Тёмный маг, заключивший сделку с демонами. Жертвует здоровьем ради силы.",
        "health": 100,
        "magic_damage": 18,
        "defense": 5,
        "mastery": "Заклинания, требующие здоровья, наносят +30% урона",
        "difficulty": "⭐⭐⭐"
    },
    "shaman": {
        "name": "🥁 Шаман",
        "description": "Посредник между мирами, использующий силу духов предков и тотемов.",
        "health": 120,
        "magic_damage": 12,
        "defense": 8,
        "mastery": "Тотемы работают на 1 ход дольше",
        "difficulty": "⭐⭐"
    }
}

BIOMES_INFO = {
    "forest": {
        "name": "🌲 Древний лес",
        "level": "1-15",
        "danger": 3,
        "resources": ["🪵 Древесина", "🫐 Ягоды", "🌿 Травы", "🍄 Грибы"],
        "mobs": ["🐺 Волк", "🐗 Кабан", "🐻 Медведь", "🕷️ Паук"],
        "boss": "🌿 Лесной дух"
    },
    "mountains": {
        "name": "⛰️ Горный хребет",
        "level": "15-25",
        "danger": 6,
        "resources": ["🪨 Камень", "⛏️ Железо", "⛏️ Золото", "💎 Кристаллы"],
        "mobs": ["🦅 Орёл", "🗿 Каменный тролль", "🦇 Летучая мышь"],
        "boss": "🗻 Горный великан"
    },
    "desert": {
        "name": "🏜️ Пустыня забвения",
        "level": "25-35",
        "danger": 7,
        "resources": ["🏖️ Песок", "🌵 Кактус", "🏜️ Пустынная трава"],
        "mobs": ["🦂 Скорпион", "🪱 Песчаный червь"],
        "boss": "🐉 Песчаный дракон"
    },
    "swamp": {
        "name": "🌿 Болото туманов",
        "level": "30-40",
        "danger": 8,
        "resources": ["🌿 Болотная трава", "🍄 Грибы", "🧪 Яды"],
        "mobs": ["🧟 Зомби", "🐸 Лягушка", "🐍 Змея"],
        "boss": "👹 Болотный монстр"
    },
    "ice_plains": {
        "name": "❄️ Ледяные равнины",
        "level": "35-45",
        "danger": 9,
        "resources": ["❄️ Лёд", "💎 Ледяные кристаллы", "❄️ Ледяная трава"],
        "mobs": ["🐺 Ледяной волк", "🐻❄️ Белый медведь", "👻 Ледяной дух"],
        "boss": "🧊 Ледяной гигант"
    },
    "volcanic": {
        "name": "🌋 Вулканические земли",
        "level": "40-50",
        "danger": 10,
        "resources": ["🌋 Обсидиан", "🔥 Огненные самоцветы", "🌋 Вулканический пепел"],
        "mobs": ["🔥 Огненный элементаль", "🌋 Лавовый голем"],
        "boss": "👑 Король вулкана"
    },
    "volcanic_beach": {
        "name": "🏖️ Вулканический пляж",
        "level": "20-30",
        "danger": 4,
        "resources": ["🏖️ Вулканический песок", "🥥 Кокосы", "🦪 Жемчуг"],
        "mobs": ["🦀 Краб", "🌋 Вулканический краб", "🦎 Варан"],
        "boss": "🦀👑 Король крабов"
    },
    "frozen_ocean": {
        "name": "🧊 Замёрзший океан",
        "level": "40-50",
        "danger": 8,
        "resources": ["🧊 Вечная мерзлота", "❄️ Ледяные кристаллы", "🐟 Замороженная рыба"],
        "mobs": ["🦭 Тюлень", "🦭 Морж", "👻 Ледяной дух"],
        "boss": "🐋 Левиафан"
    },
    "crystal_island": {
        "name": "💎 Кристальный остров",
        "level": "45-55",
        "danger": 9,
        "resources": ["💎 Идеальные кристаллы", "💎 Магические кристаллы", "💎 Алмазы"],
        "mobs": ["💎 Кристальный голем"],
        "boss": "✨ Кристальный дракон"
    },
    "dragon_island": {
        "name": "🐉 Остров драконов",
        "level": "50-60",
        "danger": 10,
        "resources": ["🐉 Чешуя дракона", "🩸 Кровь дракона", "🦴 Кости дракона"],
        "mobs": ["🐉 Молодой дракон"],
        "boss": "👑 Король драконов"
    }
}

# ============================================
# ОСНОВНАЯ КОМАНДА
# ============================================

def codex_command(message, bot_instance):
    """Команда /codex - энциклопедия"""
    text = "📚 *ЭНЦИКЛОПЕДИЯ DESTINY*\n\n"
    text += "Собрание всех знаний о мире игры.\n"
    text += "Выбери раздел:\n\n"
    text += "👾 *Бестиарий* — все монстры и боссы\n"
    text += "⚔️ *Предметы* — экипировка и ресурсы\n"
    text += "🗺️ *Локации* — все биомы и места\n"
    text += "🎭 *Классы* — информация о классах\n"
    text += "🐾 *Питомцы* — все виды питомцев\n"
    text += "🔨 *Крафт* — все рецепты\n"
    text += "🏆 *Достижения* — все ачивки\n"
    text += "🌈 *Радужная система* — осколки и камни"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👾 Бестиарий", callback_data="codex:bestiary"),
        InlineKeyboardButton("⚔️ Предметы", callback_data="codex:items"),
        InlineKeyboardButton("🗺️ Локации", callback_data="codex:biomes"),
        InlineKeyboardButton("🎭 Классы", callback_data="codex:classes"),
        InlineKeyboardButton("🐾 Питомцы", callback_data="codex:pets"),
        InlineKeyboardButton("🔨 Крафт", callback_data="codex:crafting"),
        InlineKeyboardButton("🏆 Достижения", callback_data="codex:achievements"),
        InlineKeyboardButton("🌈 Радуга", callback_data="codex:rainbow")
    )
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="game:back_to_start"))
    
    bot_instance.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ============================================
# БЕСТИАРИЙ
# ============================================

def show_bestiary(call, bot_instance, codex_data):
    """Показать бестиарий"""
    bestiary = codex_data.get("codex", {}).get("bestiary", {})
    categories = bestiary.get("categories", {})
    
    text = "👾 *БЕСТИАРИЙ*\n\n"
    text += "Все монстры, обитающие в мире Destiny.\n\n"
    
    # Добавляем категории
    categories_list = [
        ("forest", "🌲 Лесные монстры"),
        ("mountains", "⛰️ Горные монстры"),
        ("desert", "🏜️ Пустынные монстры"),
        ("swamp", "🌿 Болотные монстры"),
        ("ice", "❄️ Ледяные монстры"),
        ("volcanic", "🌋 Вулканические монстры"),
        ("beach", "🏖️ Пляжные монстры"),
        ("ocean", "🧊 Океанские монстры"),
        ("crystal", "💎 Кристальные монстры"),
        ("dragon", "🐉 Драконы"),
        ("bosses", "👑 Боссы"),
        ("legendary", "🌟 Легендарные боссы")
    ]
    
    for cat_id, cat_name in categories_list:
        text += f"• {cat_name}\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    for cat_id, cat_name in categories_list:
        markup.add(InlineKeyboardButton(
            cat_name.split()[1] + " " + cat_name.split()[0],
            callback_data=f"codex:bestiary_{cat_id}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_bestiary_category(call, bot_instance, codex_data, category):
    """Показать монстров категории"""
    bestiary = codex_data.get("codex", {}).get("bestiary", {})
    
    # Заглушка для демонстрации
    monsters = {
        "forest": [
            {"name": "🐺 Волк", "level": 2, "health": 45, "damage": 8, "exp": 40, "gold": 8},
            {"name": "🐗 Дикий кабан", "level": 4, "health": 70, "damage": 12, "exp": 60, "gold": 15},
            {"name": "🐻 Медведь", "level": 8, "health": 180, "damage": 25, "exp": 150, "gold": 40},
            {"name": "🕷️ Лесной паук", "level": 3, "health": 45, "damage": 8, "exp": 35, "gold": 5},
            {"name": "🧌 Лесной тролль", "level": 10, "health": 180, "damage": 25, "exp": 120, "gold": 35}
        ],
        "bosses": [
            {"name": "🗿 Каменный голем", "level": 25, "health": 300, "damage": 35, "exp": 300, "gold": 150},
            {"name": "🏛️ Древний страж", "level": 35, "health": 500, "damage": 45, "exp": 500, "gold": 250},
            {"name": "🔥 Огненный элементаль", "level": 28, "health": 400, "damage": 50, "exp": 400, "gold": 200},
            {"name": "🐉 Песчаный дракон", "level": 30, "health": 800, "damage": 60, "exp": 800, "gold": 500},
            {"name": "🧙 Болотная ведьма", "level": 35, "health": 250, "damage": 45, "exp": 200, "gold": 80}
        ],
        "legendary": [
            {"name": "👑 Король вулкана", "level": 48, "health": 1500, "damage": 80, "exp": 2000, "gold": 1000},
            {"name": "✨ Кристальный дракон", "level": 52, "health": 2000, "damage": 70, "exp": 2500, "gold": 1500},
            {"name": "👑 Король драконов", "level": 58, "health": 5000, "damage": 120, "exp": 10000, "gold": 10000},
            {"name": "🐋 Левиафан", "level": 45, "health": 1200, "damage": 60, "exp": 1000, "gold": 500}
        ]
    }
    
    cat_monsters = monsters.get(category, [])
    
    category_names = {
        "forest": "🌲 Лесные монстры",
        "mountains": "⛰️ Горные монстры",
        "desert": "🏜️ Пустынные монстры",
        "swamp": "🌿 Болотные монстры",
        "ice": "❄️ Ледяные монстры",
        "volcanic": "🌋 Вулканические монстры",
        "beach": "🏖️ Пляжные монстры",
        "ocean": "🧊 Океанские монстры",
        "crystal": "💎 Кристальные монстры",
        "dragon": "🐉 Драконы",
        "bosses": "👑 Боссы",
        "legendary": "🌟 Легендарные боссы"
    }
    
    text = f"👾 *{category_names.get(category, 'Монстры')}*\n\n"
    
    for monster in cat_monsters:
        text += f"• *{monster['name']}* (ур. {monster['level']})\n"
        text += f"  ❤️ {monster['health']} | ⚔️ {monster['damage']}\n"
        text += f"  💰 {monster['gold']} | ✨ {monster['exp']}\n\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:bestiary"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# ЛОКАЦИИ (БИОМЫ)
# ============================================

def show_biomes(call, bot_instance):
    """Показать все биомы"""
    text = "🗺️ *БИОМЫ МИРА*\n\n"
    text += "Все локации, доступные для исследования:\n\n"
    
    for biome_id, biome in BIOMES_INFO.items():
        text += f"• *{biome['name']}* (ур. {biome['level']})\n"
        text += f"  Опасность: {'💀' * biome['danger']}\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    for biome_id in BIOMES_INFO.keys():
        emoji = biome_id[:2]  # берём первые буквы для эмодзи
        markup.add(InlineKeyboardButton(
            BIOMES_INFO[biome_id]['name'].split()[0],
            callback_data=f"codex:biome_{biome_id}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_biome_details(call, bot_instance, biome_id):
    """Показать детали биома"""
    biome = BIOMES_INFO.get(biome_id)
    
    if not biome:
        bot_instance.answer_callback_query(call.id, "❌ Биом не найден")
        return
    
    text = f"{biome['name']}\n\n"
    text += f"📊 *Уровни:* {biome['level']}\n"
    text += f"☠️ *Опасность:* {'💀' * biome['danger']}\n\n"
    
    text += "📦 *Ресурсы:*\n"
    for resource in biome['resources']:
        text += f"  • {resource}\n"
    
    text += "\n👾 *Монстры:*\n"
    for mob in biome['mobs']:
        text += f"  • {mob}\n"
    
    if biome.get('boss'):
        text += f"\n👑 *Босс:* {biome['boss']}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:biomes"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# КЛАССЫ
# ============================================

def show_classes(call, bot_instance):
    """Показать все классы"""
    text = "🎭 *КЛАССЫ ПЕРСОНАЖЕЙ*\n\n"
    text += "Выбери класс для подробной информации:\n\n"
    
    for class_id, class_info in CLASS_INFO.items():
        text += f"• {class_info['name']} {class_info['difficulty']}\n"
    
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for class_id in CLASS_INFO.keys():
        emoji = CLASS_INFO[class_id]['name'].split()[0]
        buttons.append(InlineKeyboardButton(
            emoji,
            callback_data=f"codex:class_{class_id}"
        ))
    
    # Распределяем по рядам
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i+3])
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_class_details(call, bot_instance, class_id):
    """Показать детали класса"""
    class_info = CLASS_INFO.get(class_id)
    
    if not class_info:
        bot_instance.answer_callback_query(call.id, "❌ Класс не найден")
        return
    
    text = f"{class_info['name']}\n\n"
    text += f"{class_info['description']}\n\n"
    text += f"🎯 *Сложность:* {class_info['difficulty']}\n\n"
    text += f"📊 *Базовые характеристики:*\n"
    text += f"• ❤️ Здоровье: {class_info.get('health', '?')}\n"
    text += f"• ⚔️ Физ. урон: {class_info.get('damage', '?')}\n"
    text += f"• 🔮 Маг. урон: {class_info.get('magic_damage', '?')}\n"
    text += f"• 🛡️ Защита: {class_info.get('defense', '?')}\n\n"
    text += f"✨ *Мастерство:* {class_info['mastery']}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:classes"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# ПИТОМЦЫ
# ============================================

def show_pets_codex(call, bot_instance):
    """Показать энциклопедию питомцев"""
    text = "🐾 *ПИТОМЦЫ*\n\n"
    text += "Верные друзья, помогающие в приключениях.\n\n"
    
    # Группируем по редкости
    rarities = [
        ("common", "⚪ Обычные"),
        ("uncommon", "🟢 Необычные"),
        ("rare", "🔵 Редкие"),
        ("epic", "🟣 Эпические"),
        ("legendary", "🟡 Легендарные"),
        ("ancient", "🔴 Древние"),
        ("mythic", "💜 Мифические")
    ]
    
    for rarity_id, rarity_name in rarities:
        text += f"• {rarity_name}\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    for rarity_id, rarity_name in rarities:
        emoji = rarity_name.split()[0]
        markup.add(InlineKeyboardButton(
            emoji + " " + rarity_name.split()[1],
            callback_data=f"codex:pets_{rarity_id}"
        ))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def show_pets_rarity(call, bot_instance, rarity):
    """Показать питомцев определённой редкости"""
    pets_by_rarity = {
        "common": [
            ("🦊 Лесная лиса", "🌲 Лес", 5, "Находит травы и ягоды"),
            ("🐐 Горный козёл", "⛰️ Горы", 10, "+5% к добыче руды"),
            ("🦎 Пустынная ящерица", "🏜️ Пустыня", 25, "+10% к защите от жара"),
            ("🐸 Болотная лягушка", "🌿 Болото", 30, "+5% к сопротивлению ядам"),
            ("🐧 Ледяной пингвин", "❄️ Ледяные равнины", 35, "+10% к защите от холода"),
            ("🦀 Пляжный краб", "🏖️ Пляж", 15, "+2% к поиску жемчуга"),
            ("🦭 Ледяной тюлень", "🧊 Замёрзший океан", 40, "+10% к времени ныряния")
        ],
        "uncommon": [
            ("🐺 Лесной волк", "🌲 Лес", 10, "+3 к урону"),
            ("🦅 Горный орёл", "⛰️ Горы", 15, "+20% к обзору"),
            ("🐫 Пустынный верблюд", "🏜️ Пустыня", 25, "+50 к переносимому весу"),
            ("🐍 Болотная змея", "🌿 Болото", 32, "+10% к скрытности"),
            ("🦉 Ледяная сова", "❄️ Ледяные равнины", 38, "+5% к поиску магии"),
            ("🦎 Лавовая саламандра", "🌋 Вулкан", 42, "+15% к защите от огня"),
            ("🐇 Кристальный зайчик", "💎 Кристальный остров", 48, "+5 к удаче")
        ],
        "rare": [
            ("🌿 Лесной дух", "🌲 Лес", 20, "Лечит каждый ход"),
            ("🔥 Пустынный феникс", "🏜️ Пустыня", 35, "Шанс воскреснуть"),
            ("🐙 Болотный кракен", "🌿 Болото", 40, "Хватает врагов"),
            ("❄️ Ледяной элементаль", "❄️ Ледяные равнины", 45, "Замораживает врагов"),
            ("🌋 Лавовый элементаль", "🌋 Вулкан", 48, "Поджигает врагов"),
            ("🦋 Кристальная бабочка", "💎 Кристальный остров", 52, "+10 к удаче")
        ],
        "epic": [
            ("🐺👑 Вожак волков", "🌲 Лес", 30, "Усиливает всех питомцев"),
            ("🦅 Пустынный рок", "🏜️ Пустыня", 40, "Уносит врагов"),
            ("❄️🔥 Ледяной феникс", "❄️ Ледяные равнины", 48, "Замораживает при воскрешении"),
            ("🐲 Магмовый дракон", "🌋 Вулкан", 52, "Дышит лавой")
        ],
        "legendary": [
            ("🔥 Феникс", "🌋 Вулкан", 55, "Воскрешает владельца"),
            ("💎 Кристальный дракон", "💎 Кристальный остров", 55, "Увеличивает магию"),
            ("🐉 Молодой дракон", "🐉 Остров драконов", 58, "Драконья сила")
        ],
        "ancient": [
            ("👑 Детёныш короля драконов", "🐉 Остров драконов", 60, "Будущий властелин")
        ],
        "mythic": [
            ("🐢 Мировая черепаха", "🤫 Секретная локация", 70, "На спине покоится мир")
        ]
    }
    
    pets = pets_by_rarity.get(rarity, [])
    
    rarity_names = {
        "common": "⚪ Обычные питомцы",
        "uncommon": "🟢 Необычные питомцы",
        "rare": "🔵 Редкие питомцы",
        "epic": "🟣 Эпические питомцы",
        "legendary": "🟡 Легендарные питомцы",
        "ancient": "🔴 Древние питомцы",
        "mythic": "💜 Мифические питомцы"
    }
    
    text = f"🐾 *{rarity_names.get(rarity, 'Питомцы')}*\n\n"
    
    for pet in pets:
        text += f"• *{pet[0]}*\n"
        text += f"  📍 {pet[1]} | 🔓 ур. {pet[2]}\n"
        text += f"  ✨ {pet[3]}\n\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:pets"))
    
    bot_instance.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# РАДУЖНАЯ СИСТЕМА
# ============================================

def show_rainbow_codex(call, bot_instance):
    """Показать информацию о радужной системе"""
    text = "🌈 *РАДУЖНАЯ СИСТЕМА*\n\n"
    
    text += "Радужные осколки и камни — легендарные ресурсы для создания могущественных предметов.\n\n"
    
    text += "📊 *Ресурсы:*\n"
    text += "• 🌈 *Радужный осколок* — можно получить:\n"
    text += "  • 3-й и 6-й день входа (гарантия)\n"
    text += "  • Боссы (10% шанс)\n"
    text += "  • Ивенты (повышенный шанс)\n"
    text += "  • Достижения\n\n"
    
    text += "• 💎 *Радужный камень* — можно получить:\n"
    text += "  • Крафт из 9 осколков (24 часа)\n"
    text += "  • Премиум-магазин (500⭐ / 9 TON)\n"
    text += "  • Годовая подписка\n"
    text += "  • Легендарные достижения\n\n"
    
    text += "🔮 *Что можно сделать с камнями:*\n"
    text += "• ⚔️ Легендарное оружие (1💎)\n"
    text += "• 🛡️ Легендарная броня (1💎)\n"
    text += "• 🐉 Драконье оружие (2💎)\n"
    text += "• 🔥 Лук феникса (2💎)\n"
    text += "• ✨ Божественное оружие (3💎)\n"
    text += "• 🥚 Мифический питомец (2💎)\n"
    text += "• 🏠 Улучшение телепорта (1💎)\n"
    text += "• 🌟 Радужная аура (2💎)\n\n"
    
    text += "🏆 *Достижения:*\n"
    text += "• 100 осколков — титул 'Повелитель радуги'\n"
    text += "• 10 камней — титул 'Хранитель радуги'"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="codex:menu"))
    
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

def handle_callback(call, bot_instance, codex_data):
    """Обработка кнопок энциклопедии"""
    data = call.data.split(':')[1]
    
    if data == "menu":
        codex_command(call.message, bot_instance)
    
    elif data == "bestiary":
        show_bestiary(call, bot_instance, codex_data)
    
    elif data.startswith("bestiary_"):
        category = data.replace("bestiary_", "")
        show_bestiary_category(call, bot_instance, codex_data, category)
    
    elif data == "biomes":
        show_biomes(call, bot_instance)
    
    elif data.startswith("biome_"):
        biome_id = data.replace("biome_", "")
        show_biome_details(call, bot_instance, biome_id)
    
    elif data == "classes":
        show_classes(call, bot_instance)
    
    elif data.startswith("class_"):
        class_id = data.replace("class_", "")
        show_class_details(call, bot_instance, class_id)
    
    elif data == "pets":
        show_pets_codex(call, bot_instance)
    
    elif data.startswith("pets_"):
        rarity = data.replace("pets_", "")
        show_pets_rarity(call, bot_instance, rarity)
    
    elif data == "rainbow":
        show_rainbow_codex(call, bot_instance)
    
    # Заглушки для остальных разделов
    elif data in ["items", "crafting", "achievements"]:
        bot_instance.answer_callback_query(call.id, "⏳ Раздел в разработке")
        # Здесь можно добавить аналогичную структуру
    
    else:
        bot_instance.answer_callback_query(call.id, "⏳ Эта функция в разработке")
