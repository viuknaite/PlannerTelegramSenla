import threading
from json import JSONDecodeError

import telebot
from telebot.types import Message
import json
import logging
from datetime import datetime
import datetime
import time
from envparse import Env

from TelegramClient import TelegramClient

env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")

logger = logging.getLogger('Log')
logger.setLevel(logging.DEBUG)
log_format = logging.Formatter(u'%(levelname)-8s [%(asctime)s] %(message)s')

file_handler = logging.FileHandler('log.txt', 'a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)


class SenlaBot(telebot.TeleBot):
    def __init__(self, telegram_client: TelegramClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_client = telegram_client


telegram_client = TelegramClient(token=TOKEN, base_url="https://api.telegram.org")
bot = SenlaBot(token=TOKEN, telegram_client=telegram_client)

tconv = lambda x: time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(x))


# Registration
@bot.message_handler(commands=["start"])
def sign_up(message: Message):
    try:
        date = tconv(message.date)
        with open("users.json", "r") as f_o:
            data_from_json = json.load(f_o)

        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        full_name = message.from_user.full_name

        if str(user_id) in data_from_json:
            bot.reply_to(message=message, text=str(f"Вы уже зарегистрированы"))
            logger.info(f"User {username} already registered")

        elif str(user_id) not in data_from_json:
            data_from_json[user_id] = {"username": username, "first_name": first_name, "full_name": full_name,
                                       "reg_date": date}
            with open("users.json", "w") as f_o:
                json.dump(data_from_json, f_o, indent=4, ensure_ascii=False)
            bot.reply_to(message=message, text=str(f"Регистрация успешна, {first_name}"))
            logger.info(f"New user {username} registered")

    except JSONDecodeError:
        logger.critical('JSON error occured')


# Setting the reminder
@bot.message_handler(commands=["reminder"])
def reminder_message(message):
    bot.send_message(message.chat.id, 'Введите тему напоминания:')
    bot.register_next_step_handler(message, set_reminder_name)


def set_reminder_name(message):
    user_data = {}
    user_data[message.chat.id] = {'reminder_name': message.text}
    bot.send_message(message.chat.id,
                     'Введите дату и время, когда вы хотите получить напоминание в формате ГГГГ-ММ-ДД чч:мм:сс.')
    bot.register_next_step_handler(message, reminder_set, user_data)


def reminder_set(message, user_data):
    try:
        reminder_time = datetime.datetime.strptime(message.text, '%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.now()
        delta = reminder_time - now
        if delta.total_seconds() <= 0:
            bot.send_message(message.chat.id, 'Вы ввели прошедшую дату, попробуйте еще раз.')
        else:
            reminder_name = user_data[message.chat.id]['reminder_name']
            bot.send_message(message.chat.id,
                             'Напоминание "{}" установлено на {}.'.format(reminder_name, reminder_time))
            reminder_timer = threading.Timer(delta.total_seconds(), send_reminder, [message.chat.id, reminder_name])
            reminder_timer.start()
            with open("reminders.json", "r") as f_o:
                reminder_data_from_json = json.load(f_o)

            user_id = message.from_user.id
            username = message.from_user.username

            reminder_data_from_json[user_id] = {"username": username, "reminder_name": reminder_name, "reminder_time": reminder_time}
            with open("reminders.json", "w") as f_o:
                json.dump(reminder_data_from_json, f_o, indent=4, ensure_ascii=False, default=str)

            logger.info(f"New reminder from user {username}")
    except ValueError:
        bot.send_message(message.chat.id, 'Неправильный формат даты и времени, попробуйте еще раз.')


# Send reminder to user
def send_reminder(chat_id, reminder_name):
    bot.send_message(chat_id, 'Напоминание о событии "{}".'.format(reminder_name))


# Other cases
@bot.message_handler(func=lambda message: True)
def handle_all_message(message):
    bot.send_message(message.chat.id, 'Я вас не понимаю, попробуйте ввести другую команду')


# Test replying to bot message
# def handle_standup_speech(message: Message):
#     bot.reply_to(message, "Ок")
#
#
# @bot.message_handler(commands=["say_standup_speech"])
# def say_standup_speech(message: Message):
#     try:
#         bot.reply_to(message, text="Привет, как дела?")
#         bot.register_next_step_handler(message, handle_standup_speech)
#     except ZeroDivisionError:
#         logger.critical('ZeroDivisionError occured')


def create_error_message(err: Exception) -> str:
    return f"{err.__class__}::{err}" #{datetime.now()}::


while True:
    try:
        bot.polling()
    except Exception as err:
        bot.telegram_client.post(method="sendMessage",
                                 params={"chat_id": {ADMIN_CHAT_ID}, "text": create_error_message(err)})
