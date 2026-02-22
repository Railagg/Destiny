import telebot
import json
import os
import sys
import logging
import requests
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

# ============================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    stream=sys.stdout,
    force=True
)

sys.stdout.reconfigure(line_buffering=True)

logging.info("🚀 Запуск бота Destiny...")

# ============================================
# ТОКЕН БОТА
# ============================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("❌ НЕТ ТОКЕНА")
    exit(1)

logging.info(f"✅ Токен получен: {BOT_TOKEN[:10]}...")

# ============================================
# ОТКЛЮЧЕНИЕ ВЕБХУКА
# ============================================
try:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    logging.info("✅ Webhook отключён")
except:
    logging.warning("⚠️ Не удалось отключить вебхук")

# ============================================
# СОЗДАНИЕ БОТА
# ============================================
bot = telebot.TeleBot(BOT_TOKEN)

try:
    me = bot.get_me()
    logging.info(f"✅ Бот авторизован: @{me.username}")
except Exception as e:
    logging.error(f"❌ Ошибка: {e}")
    exit(1)

# ============================================
# ЖЁСТКИЙ ПУТЬ К JSON
# ============================================

# Путь к папке data (по структуре GitHub)
DATA_DIR = Path("/opt/render/project/src/data")
logging.info(f"📁 Путь к данным: {DATA_DIR}")

# Проверяем существование папки
if DATA_DIR.exists():
    logging.info(f"✅ Папка существует")
    files = list(DATA_DIR.glob("*.json"))
    logging.info(f"📄 Найдено JSON файлов: {len(files)}")
    if files:
        logging.info(f"📋 Список файлов:")
        for f in files:
            logging.info(f"   - {f.name}")
else:
    logging.error(f"❌ Папка НЕ НАЙДЕНА!")
    # Пробуем альтернативный путь
    alt_path = Path("/data")
    if alt_path.exists():
        DATA_DIR = alt_path
        logging.info(f"✅ Используем альтернативный путь: {DATA_DIR}")
    else:
        DATA_DIR = Path("/")
        logging.info(f"⚠️ Используем корневую папку: {DATA_DIR}")

# ============================================
# ЗАГРУЗКА JSON
# ============================================

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
    except json.JSONDecodeError as e:
        logging.error(f"❌ Ошибка в JSON {filename}: {e}")
        return {}
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки {filename}: {e}")
        return {}

logging.info("🚀 Загрузка JSON файлов...")

# Загружаем все JSON из твоей папки
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

# Считаем загруженные
loaded = [
    locations_data, enemies_data, items_data, crafting_data,
    classes_data, quests_data, house_data, premium_data, nft_data,
    rainbow_data, events_data, codex_data, biomes_data, pets_data,
    secrets_data, exchange_data, islands_data
]
loaded_count = sum(1 for x in loaded if x)
logging.info(f"✅ Загружено JSON: {loaded_count}/17")

# ============================================
# КОМАНДЫ
# ============================================

@bot.message_handler(commands=['start'])
def start(message):
    json_info = []
    if locations_data:
        json_info.append(f"📍 Локаций: {len(locations_data.get('locations', {}))}")
    if enemies_data:
        json_info.append(f"⚔️ Врагов: {len(enemies_data.get('enemies', {}))}")
    if items_data:
        json_info.append(f"📦 Предметов: {len(items_data.get('items', {}))}")
    if pets_data:
        json_info.append(f"🐾 Питомцев: {len(pets_data.get('pets', {}))}")
    if quests_data:
        json_info.append(f"📜 Квестов: {len(quests_data.get('quests', {}))}")
    
    json_text = "\n".join(json_info) if json_info else "📊 JSON не загружены"
    
    bot.send_message(
        message.chat.id,
        f"✅ БОТ РАБОТАЕТ!\n\n"
        f"📂 JSON: {loaded_count}/17\n"
        f"{json_text}\n\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"👤 Имя: {message.from_user.first_name}"
    )
    logging.info(f"✅ /start от {message.from_user.id}")

@bot.message_handler(commands=['location'])
def location_command(message):
    if locations_data and locations_data.get("locations"):
        first_loc = list(locations_data["locations"].values())[0]
        text = f"📍 *{first_loc.get('name', 'Локация')}*\n\n"
        text += first_loc.get('description', 'Описание отсутствует')
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Локации не загружены")

@bot.message_handler(commands=['items'])
def items_command(message):
    if items_data and items_data.get("items"):
        items = list(items_data["items"].items())[:10]
        text = "📦 *Предметы:*\n\n"
        for item_id, item in items:
            name = item.get('name', item_id)
            rarity = item.get('rarity', 'обычный')
            text += f"• {name} ({rarity})\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Предметы не загружены")

@bot.message_handler(commands=['pets'])
def pets_command(message):
    if pets_data and pets_data.get("pets"):
        pets = list(pets_data["pets"].items())[:10]
        text = "🐾 *Питомцы:*\n\n"
        for pet_id, pet in pets:
            name = pet.get('name', pet_id)
            rarity = pet.get('rarity', 'обычный')
            text += f"• {name} ({rarity})\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Питомцы не загружены")

@bot.message_handler(commands=['help'])
def help_command(message):
    text = "❓ *Доступные команды:*\n\n"
    text += "/start - информация о боте\n"
    text += "/location - первая локация\n"
    text += "/items - список предметов\n"
    text += "/pets - список питомцев\n"
    text += "/help - это меню"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(
        message.chat.id, 
        f"❓ Неизвестная команда. Напиши /help\n\n"
        f"Твоё сообщение: {message.text}"
    )
    logging.info(f"✅ Сообщение от {message.from_user.id}: {message.text}")

# ============================================
# HEALTH СЕРВЕР
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
