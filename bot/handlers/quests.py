# Пустой файл для квестов
# TODO: добавить квесты позже
def quests_command(message, bot, get_or_create_player, quests_data):
    bot.send_message(message.chat.id, "📜 Квесты временно недоступны")

def handle_callback(call, bot, get_or_create_player, quests_data):
    bot.answer_callback_query(call.id, "⏳ Квесты в разработке")
