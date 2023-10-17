import io
import telebot
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import Database
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database

with open('keys.json', 'r', encoding='utf-8') as f:  # открыли файл с данными
    text = json.load(f)

db = Database('auction.db')
tg_group = text['tg_group']
token = text['user_panel']
bot = telebot.TeleBot(token)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    id = call.message.chat.id
    flag = call.data[0]
    data = call.data[1:]
    if flag == 't':
        with db.connection:
            lots = db.connection.execute(f'SELECT * FROM lots').fetchone()
        date_finish = lots[9]
        date_finish = datetime.strptime(date_finish, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        delta = date_finish - now
        delta = str(delta).split('.')[0]
        bot.answer_callback_query(callback_query_id=call.id,
                                  text='Осталось времени ' + str(delta)[-8:-6] + ' часов ' + str(delta)[-5:-3] + ' минут ' +
                                       str(delta)[-2:] + ' секунд')
    elif flag == 'i':
        bot.answer_callback_query(callback_query_id=call.id,
                                  text="""1. Делаем ставку и чёто-там, не забудь поменять""",
                                  show_alert=True)

def user_panel_run():
    print('ready')
    bot.polling()


if __name__ == '__main__':
    user_panel_run()
