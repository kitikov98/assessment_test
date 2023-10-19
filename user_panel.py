import io
import telebot
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from database import Database

with open('keys.json', 'r', encoding='utf-8') as f:  # открыли файл с данными
    text = json.load(f)

db = Database('auction.db')
tg_group = text['tg_group']
token = text['user_panel']
bot = telebot.TeleBot(token)

user_menu = ['Мои аукционы', 'Розыгрыш', 'Топ пользователей', 'Правила', 'Статистика', 'Помощь', 'Пожаловаться']
menu_1 = InlineKeyboardMarkup()
for item in user_menu:
    menu_1.add(InlineKeyboardButton(item, callback_data='A'+item))

main_menu = 'Назад в меню'
menu_2 = InlineKeyboardMarkup()
menu_2.add(InlineKeyboardButton(main_menu, callback_data='B'+main_menu))


@bot.message_handler(commands=['start'])
def start_admin_panel(message):
    bot.send_message(message.chat.id, 'Hi', reply_markup=menu_1)

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

    elif flag == 'A':
        bot.edit_message_text("Какой-то текст", call.message.chat.id, call.message.message_id, reply_markup=menu_2)
    elif flag == 'B':
        bot.edit_message_text("Какой-то текст", call.message.chat.id, call.message.message_id, reply_markup=menu_1)


    # elif flag == 'D':
    #     msg = bot.edit_message_text('Введите отзыв', call.message.chat.id, call.message.message_id)
    #     bot.register_next_step_handler(msg, strike, data, call.message.chat.id, 'adm')

def user_panel_run():
    print('ready')
    bot.polling()


if __name__ == '__main__':
    user_panel_run()
