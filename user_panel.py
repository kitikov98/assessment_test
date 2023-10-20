import io
import telebot
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from database import Database
from admin_panel import convert_to_pic

with open('keys.json', 'r', encoding='utf-8') as f:  # открыли файл с данными
    text = json.load(f)

db = Database('auction.db')
tg_group = text['tg_group']
token = text['user_panel']
bot = telebot.TeleBot(token)

user_menu = ['Мои аукционы', 'Розыгрыш', 'Топ пользователей', 'Правила', 'Статистика', 'Помощь', 'Пожаловаться',
             'Баланс']
user_info = {'Розыгрыш': "Пока розыгрышей не проводится",
             'Топ пользователей': "Сколько букв Ж в слове ЖОПА? В ЖОПЕ только вы",
             'Правила': """После окончания торгов,победитель или продавец должены выйти на связь в течении суток‼️
Победитель обязан выкупить лот в течении ТРЁХ дней,после окончания аукциона🔥
НЕ ВЫКУП ЛОТА - ПЕРМАНЕНТНЫЙ БАН ВО ВСЕХ НУМИЗМАТИЧЕСКИХ СООБЩЕСТВАХ И АУКЦИОНАХ🤬
Что бы узнать время окончания аукциона,нажмите на ⏰
Антиснайпер - Ставка сделанная за 5 минут до конца,автоматически переносит
Аукцион на 5 минут вперёд ‼️

Работают только проверенные продавцы.
Дополнительные Фото можно запросить у продавца.
Случайно сделал ставку?🤔
Напиши продавцу‼️


Отправка почтой,стоимость пересылки зависит от общего веса отправления и страны. Обсуждается с продавцом. 
Лоты можно копить ,экономя при этом на почте.
Отправка в течении трёх дней после оплаты‼️""",
             'Помощь': """Свяжитесь с нами, если у вас возникли вопросы @kitikov98

Удачных торгов и выгодных покупок."""}
menu_1 = InlineKeyboardMarkup()
for item in user_menu:
    menu_1.add(InlineKeyboardButton(item, callback_data='A' + item))

main_menu = 'Назад в меню'
menu_2 = InlineKeyboardMarkup()
menu_2.add(InlineKeyboardButton(main_menu, callback_data='B' + main_menu))


def discription_text(list1):
    text = f"""
Начальная стоимость: {list1[1]}
id продавца: tg://openmessage?user_id={list1[2]}
местонахождение: {list1[3]}
описание: {list1[4]}
время начало торгов: {list1[7]}
время окончания торгов: {list1[8]}
тип лота: {list1[9]}
"""
    return text


def strike(message, who, whom, role=None):
    if role == 'user':
        with db.connection:
            db.connection.execute(f"""INSERT INTO reports (admin_id, user_id, status, description, relationship)
             VALUES(?,?,?,?,?)""", (whom, who, 'на рассмотрении', message.text, 'user-to admin'))
    bot.send_message(message.chat.id, 'Спасибо, ваш отзыв будет рассмотрен в ближайшее время')

@bot.message_handler(commands=['start'])
def start_admin_panel(message):
    try:
        with db.connection:
            db.connection.execute(f"""INSERT INTO user (tg_id, balance, number_of_payments,
             status_auto_bid, strike_status) VALUES(?,?,?,?,?)""", (message.chat.id, 400, 0, 0, 0))
    except:
        pass

    if message.text != '/start':
        with db.connection:
            lot = db.connection.execute(f'SELECT * FROM lots WHERE id={message.text.split(" ")[1]}').fetchone()
        lot_menu = InlineKeyboardMarkup()
        lot_menu.add(InlineKeyboardButton('time', callback_data='t' + str(message.text.split(" ")[1])),
                     InlineKeyboardButton('описание', callback_data='i'),
                     InlineKeyboardButton('документы', callback_data='d' + str(message.text.split(" ")[1])))
        lot_menu.add(InlineKeyboardButton('30 ₩', callback_data='p' + str(message.text.split(" ")[1]) + '.30'),
                     InlineKeyboardButton('50 ₩', callback_data='p' + str(message.text.split(" ")[1]) + '.50'),
                     InlineKeyboardButton('150 ₩', callback_data='p' + str(message.text.split(" ")[1]) + '.150'))
        bot.send_photo(message.chat.id, convert_to_pic(lot[11]), caption=f'{discription_text(lot)}',
                       reply_markup=lot_menu)
    else:
        bot.send_message(message.chat.id, 'Меню пользователя', reply_markup=menu_1)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    id = call.message.chat.id
    flag = call.data[0]
    data = call.data[1:]
    if flag == 't':
        with db.connection:
            lots = db.connection.execute(f'SELECT * FROM lots WHERE id ={data}').fetchone()
        date_finish = lots[8]
        date_finish = datetime.strptime(date_finish, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        delta = date_finish - now
        delta = str(delta).split('.')[0]
        bot.answer_callback_query(callback_query_id=call.id,
                                  text='Осталось времени ' + str(delta)[-8:-6] + ' часов ' + str(delta)[
                                                                                             -5:-3] + ' минут ' +
                                       str(delta)[-2:] + ' секунд')
    elif flag == 'i':
        bot.answer_callback_query(callback_query_id=call.id,
                                  text="""1. Делаем ставку и чёто-там, не забудь поменять""",
                                  show_alert=True)

    elif flag == 'd':
        with db.connection:
            lot = db.connection.execute(f'SELECT * FROM lots WHERE id ={data}').fetchone()
        file_obj = io.BytesIO(lot[5])
        file_obj.name = lot[6]
        # text_1 = discription_text(lot)
        bot.send_document(call.message.chat.id, file_obj, caption="Вот ваш документ")

    elif flag == 'p':
        lot_id = data.split('.')[0]
        bid = int(data.split('.')[1])
        with db.connection:
            message_id = db.connection.execute(f'SELECT message_id FROM lots WHERE id={lot_id}').fetchone()[0]
            lots = db.connection.execute(f'SELECT * FROM lots WHERE id ={lot_id}').fetchone()
        print(message_id)
        bot.send_message(call.message.chat.id, f'Ваша ставка в {int(lots[1]) + bid} принята')
        with db.connection:
            user_id = db.connection.execute(f'SELECT id FROM user WHERE tg_id = {call.message.chat.id}').fetchone()[0]
            db.connection.execute(f'INSERT INTO bids (lot_id, bid, user_id) VALUES (?,?,?)',
                                  (lot_id, (int(lots[1]) + bid), user_id))

    elif flag == 'A':
        if data == 'Баланс':
            with db.connection:
                user_balance = db.connection.execute(f"""SELECT balance FROM user 
                WHERE tg_id = {call.message.chat.id}""").fetchone()[0]
            bot.edit_message_text(f'Пользователь {call.message.chat.id} имеет баланс в {user_balance} золотох монет',
                                  call.message.chat.id, call.message.message_id, reply_markup=menu_2)
        elif data == 'Мои аукционы':
            with db.connection:
                user_id = db.connection.execute(f'SELECT id FROM user WHERE tg_id = {call.message.chat.id}').fetchone()[
                    0]
                bids = db.connection.execute(f'SELECT * FROM bids WHERE user_id ={user_id} ').fetchall()
            if type(bids) == tuple:
                bids = [bids]
            text_bids = f'Пользователь {user_id} осуществляет торги:\n'
            for bid in bids:
                text_bids += f'Лот № {bid[1]} со ставкой в {bid[2]}\n'
            bot.edit_message_text(text_bids, call.message.chat.id, call.message.message_id, reply_markup=menu_2)
        elif data == 'Пожаловаться':
            admin_report_menu = InlineKeyboardMarkup()
            with db.connection:
                admin_id = db.connection.execute(f"""SELECT tg_id FROM admin""").fetchall()
            if type(admin_id) == tuple:
                admin_id = [admin_id]
            for admin in admin_id:
                admin_report_menu.add(InlineKeyboardButton(str(admin[0]), callback_data='C' + str(admin[0])))
            bot.edit_message_text(f'Выберите администратора', call.message.chat.id, call.message.message_id,
                                  reply_markup=admin_report_menu)
        else:
            bot.edit_message_text(user_info[data], call.message.chat.id, call.message.message_id, reply_markup=menu_2)
    elif flag == 'B':
        bot.edit_message_text("Меню пользователя", call.message.chat.id, call.message.message_id, reply_markup=menu_1)
    elif flag == 'C':
        msg = bot.send_message(call.message.chat.id, 'Введите отзыв')
        bot.register_next_step_handler(msg, strike, call.message.chat.id, data, 'user')

    # elif flag == 'D':
    #     msg = bot.edit_message_text('Введите отзыв', call.message.chat.id, call.message.message_id)
    #     bot.register_next_step_handler(msg, strike, data, call.message.chat.id, 'adm')


def user_panel_run():
    print('ready')
    bot.polling()


if __name__ == '__main__':
    user_panel_run()
