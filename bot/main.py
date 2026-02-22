import telebot
import os
import time
import logging
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Простейшее логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("❌ НЕТ ТОКЕНА")
    exit(1)

logging.info(f"✅ Токен получен: {BOT_TOKEN[:10]}...")

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Проверка бота
try:
    me = bot.get_me()
    logging.info(f"✅ Бот авторизован: @{me.username}")
except Exception as e:
    logging.error(f"❌ Ошибка авторизации: {e}")
    exit(1)

# ============================================
# ЗАГРУЗКА JSON ФАЙЛОВ
# ============================================

# Путь к папке data (Render)
DATA_DIR = Path("/opt/render/project/src/data")
logging.info(f"📁 Путь к данным: {DATA_DIR}")

# Проверяем, существует ли папка
if not DATA_DIR.exists():
    logging.error(f"❌ Папка {DATA_DIR} не найдена!")
    # Пробуем альтернативный путь
    DATA_DIR = Path(__file__).parent.parent / "data"
    logging.info(f"📁 Пробуем альтернативный путь: {DATA_DIR}")

# Загружаем JSON
def load_json(filename):
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.info(f"✅ Загружен {filename}")
            return data
    except FileNotFoundError:
        logging.warning(f"⚠️ Файл не найден: {filename}")
        return {}
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки {filename}: {e}")
        return {}

# Загружаем все JSON
logging.info("🚀 Загрузка JSON...")
locations_data = load_json("locations.json")
enemies_data = load_json("enemies.json")
items_data = load_json("items.json")
crafting_data = load_json("crafting.json")
classes_data = load_json("classes.json")
quests_data = load_json("quests.json")
house_data = load_json("house.json")
premium_data = load_json("premium.json")
nft_data = load_json("nft.json")
rainbow_data = load_json("rainbow.json")
events_data = load_json("events.json")
codex_data = load_json("codex.json")
biomes_data = load_json("biomes.json")
pets_data = load_json("pets.json")
secrets_data = load_json("secrets.json")
exchange_data = load_json("exchange.json")
islands_data = load_json("islands.json")

# Считаем, сколько загрузилось
loaded_count = sum(1 for data in [
    locations_data, enemies_data, items_data, crafting_data, 
    classes_data, quests_data, house_data, premium_data, nft_data,
    rainbow_data, events_data, codex_data, biomes_data, pets_data,
    secrets_data, exchange_data, islands_data
] if data)

logging.info(f"✅ Загружено JSON: {loaded_count}/17")

# ============================================
# КОМАНДЫ
# ============================================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        f"✅ БОТ РАБОТАЕТ!\n\n"
        f"📊 Загружено JSON: {loaded_count}/17\n"
        f"📍 Локаций: {len(locations_data.get('locations', {})) if locations_data else 0}\n"
        f"⚔️ Врагов: {len(enemies_data.get('enemies', {})) if enemies_data else 0}\n"
        f"📦 Предметов: {len(items_data.get('items', {})) if items_data else 0}"
    )
    logging.info(f"✅ /start от {message.from_user.id}")

@bot.message_handler(commands=['location'])
def location_command(message):
    if locations_data and locations_data.get("locations"):
        loc = list(locations_data["locations"].values())[0]
        bot.send_message(
            message.chat.id,
            f"📍 *{loc.get('name', 'Локация')}*\n\n{loc.get('description', '')}",
            parse_mode='Markdown'
        )
    else:
        bot.send_message(message.chat.id, "❌ Локации не загружены")

@bot.message_handler(commands=['items'])
def items_command(message):
    if items_data and items_data.get("items"):
        items = list(items_data["items"].items())[:5]
        text = "📦 *Предметы:*\n\n"
        for item_id, item in items:
            text += f"• {item.get('name', item_id)} ({item.get('rarity', 'обычный')})\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Предметы не загружены")

@bot.message_handler(commands=['enemies'])
def enemies_command(message):
    if enemies_data and enemies_data.get("enemies"):
        enemies = list(enemies_data["enemies"].items())[:5]
        text = "⚔️ *Враги:*\n\n"
        for enemy_id, enemy in enemies:
            text += f"• {enemy.get('name', enemy_id)} (ур.{enemy.get('level', 1)})\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Враги не загружены")

@bot.message_handler(commands=['quests'])
def quests_command(message):
    if quests_data and quests_data.get("quests"):
        quests = list(quests_data["quests"].items())[:5]
        text = "📜 *Квесты:*\n\n"
        for quest_id, quest in quests:
            text += f"• {quest.get('name', quest_id)} (+{quest.get('reward', {}).get('gold', 0)}💰)\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Квесты не загружены")

@bot.message_handler(commands=['pets'])
def pets_command(message):
    if pets_data and pets_data.get("pets"):
        pets = list(pets_data["pets"].items())[:5]
        text = "🐾 *Питомцы:*\n\n"
        for pet_id, pet in pets:
            text += f"• {pet.get('name', pet_id)} ({pet.get('rarity', 'обычный')})\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Питомцы не загружены")

@bot.message_handler(commands=['rainbow'])
def rainbow_command(message):
    if rainbow_data:
        text = "🌈 *Радужные камни*\n\n"
        if rainbow_data.get("shards"):
            text += f"💎 Осколков нужно: {rainbow_data.get('shards_per_stone', 9)}\n"
        if rainbow_data.get("islands"):
            text += f"🏝️ Островов: {len(rainbow_data['islands'])}"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Радужные камни не загружены")

@bot.message_handler(commands=['exchange'])
def exchange_command(message):
    if exchange_data:
        text = "💱 *Обмен валют*\n\n"
        if exchange_data.get("rates"):
            for rate in list(exchange_data["rates"].items())[:3]:
                text += f"• {rate[0]}: {rate[1]}\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Обмен не загружен")

@bot.message_handler(commands=['help'])
def help_command(message):
    text = "❓ *Доступные команды:*\n\n"
    text += "/start - информация\n"
    text += "/location - первая локация\n"
    text += "/items - предметы\n"
    text += "/enemies - враги\n"
    text += "/quests - квесты\n"
    text += "/pets - питомцы\n"
    text += "/rainbow - радужные камни\n"
    text += "/exchange - обмен\n"
    text += "/help - это меню"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(message.chat.id, f"❓ Неизвестная команда. Напиши /help")
    logging.info(f"✅ Сообщение от {message.from_user.id}: {message.text}")

# ============================================
# HEALTH SERVER
# ============================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running')
    def log_message(self, *args): pass

def run_health():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logging.info(f"✅ Health server on port {port}")
    server.serve_forever()

threading.Thread(target=run_health, daemon=True).start()

# ============================================
# ЗАПУСК
# ============================================
logging.info("🚀 Бот запущен, ждем команды...")

while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logging.error(f"❌ Polling error: {e}")
        time.sleep(5)
