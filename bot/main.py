import telebot
import os
import time
import logging
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

# Элементарный обработчик
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ БОТ РАБОТАЕТ! /start получен")
    logging.info(f"✅ /start от {message.from_user.id}")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(message.chat.id, f"✅ Эхо: {message.text}")
    logging.info(f"✅ Сообщение от {message.from_user.id}: {message.text}")

# Health server для Render
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

logging.info("🚀 Бот запущен, ждем команды...")

# Бесконечный polling с защитой
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logging.error(f"❌ Polling error: {e}")
        time.sleep(5)
