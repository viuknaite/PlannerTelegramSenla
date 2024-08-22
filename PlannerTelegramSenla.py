import telebot
from telebot.types import Message
import json

bot_client = telebot.TeleBot(token="7175797246:AAEeYWrUkHRl7zAbwV-q7fRr_6W0n-9vHT4")
ADMIN_CHAT_ID = 5218304059


@bot_client.message_handler(commands=["start"])
def sign_up(message: Message):
    with open("users.json", "r") as f_o:
        data_from_json = json.load(f_o)

    user_id = message.from_user.id
    username = message.from_user.username

    if str(user_id) not in data_from_json:
        data_from_json[user_id] = {"username": username}

    with open("users.json", "w") as f_o:
        json.dump(data_from_json, f_o, indent=4, ensure_ascii=False)
    bot_client.reply_to(message=message, text=str(f"Регистрация успешна, {username}"))


def handle_standup_speech(message: Message):
    bot_client.reply_to(message, "Ок")


@bot_client.message_handler(commands=["say_standup_speech"])
def say_standup_speech(message: Message):
    bot_client.reply_to(message, text="Привет, как дела?")
    # попробовать убрать message, возможно будет обрабатываться сообщение от любого пользователя в чате
    bot_client.register_next_step_handler(message, handle_standup_speech)


bot_client.polling()
