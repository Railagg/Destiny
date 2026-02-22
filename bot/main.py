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
# ЗАГРУЗКА JSON - ЭТОТ БЛОК РАБОТАЛ!
# ============================================

# Определяем путь
if os.path.exists("/opt/render/project/src"):
    BASE_DIR = Path("/opt/render/project/src")
    logging.info("✅ Render: используем /opt/render/project/src")
else:
    BASE_DIR = Path(__file__).parent.parent
    logging.info("✅ Локально: используем родительскую папку")

DATA_DIR = BASE_DIR / "data"
logging.info(f"📁 Путь к данным: {DATA_DIR}")

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
        logging.error(f"❌ Ошибка {filename}: {e}")
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

# Считаем загруженные
loaded = [locations_data, enemies_data, items_data, crafting_data,
          classes_data, quests_data, house_data, premium_data, nft_data,
          rainbow_data, events_data, codex_data, biomes_data, pets_data,
          secrets_data, exchange_data, islands_data]
loaded_count = sum(1 for x in loaded if x)
logging.info(f"✅ Загружено JSON: {loaded_count}/17")

# ============================================
# КОМАНДЫ
# ============================================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"✅ БОТ РАБОТАЕТ!\n\n"
        f"📊 JSON: {loaded_count}/17\n"
        f"📍 Локаций: {len(locations_data.get('locations', {})) if locations_data else 0}"
    )
    logging.info(f"✅ /start от {message.from_user.id}")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(message.chat.id, f"❓ Неизвестная команда. Напиши /start")
    logging.info(f"✅ Сообщение от {message.from_user.id}")

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
