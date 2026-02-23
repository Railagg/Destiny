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
    logging.error(f"❌ Ошибка авторизации: {e}")
    exit(1)

# ============================================
# ПУТЬ К JSON
# ============================================

current_dir = Path(__file__).parent          # /bot
data_dir = current_dir / "data"               # /bot/data

logging.info(f"📁 Текущая папка бота: {current_dir}")
logging.info(f"📁 Папка с данными: {data_dir}")

# Проверяем наличие JSON
if data_dir.exists():
    json_files = list(data_dir.glob("*.json"))
    logging.info(f"📄 Найдено JSON: {len(json_files)}")
else:
    logging.error(f"❌ Папка {data_dir} не найдена!")
    data_dir.mkdir(parents=True, exist_ok=True)

# ============================================
# ЗАГРУЗКА JSON
# ============================================

def load_json(filename):
    filepath = data_dir / filename
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

logging.info("🚀 Загрузка JSON файлов...")

# Загружаем все JSON
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

# ============================================
# ИМПОРТ ВСЕХ ХЕНДЛЕРОВ
# ============================================

from handlers import (
    start, game, pets, exchange, rainbow, premium, nft,
    guild, pvp, codex, events, shop, top, admin
)

# Регистрируем команды из хендлеров
if hasattr(start, 'register_handlers'):
    start.register_handlers(bot)

if hasattr(game, 'register_handlers'):
    game.register_handlers(bot, locations_data, enemies_data, items_data)

if hasattr(pets, 'register_handlers'):
    pets.register_handlers(bot, get_or_create_player, pets_data)

if hasattr(exchange, 'register_handlers'):
    exchange.register_handlers(bot, get_or_create_player, exchange_data)

if hasattr(rainbow, 'register_handlers'):
    rainbow.register_handlers(bot, get_or_create_player, rainbow_data)

if hasattr(premium, 'register_handlers'):
    premium.register_handlers(bot, get_or_create_player, premium_data)

if hasattr(nft, 'register_handlers'):
    nft.register_handlers(bot, get_or_create_player, nft_data)

if hasattr(guild, 'register_handlers'):
    guild.register_handlers(bot, get_or_create_player)

if hasattr(pvp, 'register_handlers'):
    pvp.register_handlers(bot, get_or_create_player)

if hasattr(codex, 'register_handlers'):
    codex.register_handlers(bot, codex_data)

if hasattr(events, 'register_handlers'):
    events.register_handlers(bot, events_data)

if hasattr(shop, 'register_handlers'):
    shop.register_handlers(bot, get_or_create_player, items_data)

if hasattr(top, 'register_handlers'):
    top.register_handlers(bot, get_or_create_player)

if hasattr(admin, 'register_handlers'):
    admin.register_handlers(bot, get_or_create_player)

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def get_or_create_player(telegram_id, username=None, first_name=None):
    """Временная заглушка. Позже заменим на работу с БД"""
    class DummyCharacter:
        def __init__(self):
            self.level = 1
            self.health = 100
            self.energy = 100
            self.gold = 20
            self.destiny_tokens = 0
            self.inventory = []
    
    class DummyUser:
        def __init__(self):
            self.telegram_id = telegram_id
            self.username = username
            self.first_name = first_name
            self.created_at = datetime.now()
    
    return DummyUser(), DummyCharacter()

def save_character(character):
    """Временная заглушка"""
    pass

# ============================================
# БАЗОВЫЕ КОМАНДЫ (на случай, если в хендлерах нет)
# ============================================

@bot.message_handler(commands=['start'])
def start_command(message):
    json_info = []
    if locations_data:
        json_info.append(f"📍 Локаций: {len(locations_data.get('locations', {}))}")
    if enemies_data:
        json_info.append(f"⚔️ Врагов: {len(enemies_data.get('enemies', {}))}")
    if items_data:
        json_info.append(f"📦 Предметов: {len(items_data.get('items', {}))}")
    if pets_data:
        json_info.append(f"🐾 Питомцев: {len(pets_data.get('pets', {}))}")
    
    json_text = "\n".join(json_info)
    
    bot.send_message(
        message.chat.id,
        f"✅ БОТ РАБОТАЕТ!\n\n"
        f"📂 JSON: 17/17\n"
        f"{json_text}\n\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"👤 Имя: {message.from_user.first_name}"
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    text = "❓ *Доступные команды:*\n\n"
    text += "/start - информация о боте\n"
    text += "/location - первая локация\n"
    text += "/items - список предметов\n"
    text += "/pets - список питомцев\n"
    text += "/help - это меню"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

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

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logging.error(f"❌ Polling error: {e}")
            time.sleep(5)
