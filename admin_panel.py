import io
import telebot
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import Database
from base64 import b64encode
from io import BytesIO
from datetime import datetime, timedelta

with open('keys.json', 'r', encoding='utf-8') as f:  # открыли файл с данными
    text = json.load(f)

db = Database('auction.db')
tg_group = text['tg_group']
token = text['admin_panel']

bot = telebot.TeleBot(token)

menu_send = InlineKeyboardMarkup()
menu_send.add(InlineKeyboardButton(text="учавствовать", url=f"https://t.me/kitikov98_study_bot?start="))
menu_send.add(InlineKeyboardButton('время', callback_data='t' + '0'),
              InlineKeyboardButton('info', callback_data='i' + '0'))

menu_1 = ["Создать_лот", "Баланс", "Удаление лота", "Пожаловаться"]
menu_2 = ["Одобрение лота", "Отзыв пользователей", "Страйки админов"]
menu_3 = [*menu_1, *menu_2, 'Изменение админов', 'Удаление админов', 'Начисление баланса']
# Клавиатура для администраторов
admin_markup = InlineKeyboardMarkup()
for x1 in menu_1:
    admin_markup.add(InlineKeyboardButton(x1, callback_data='A' + x1))

admin_markup2 = InlineKeyboardMarkup()
for x2 in menu_2:
    admin_markup2.add(InlineKeyboardButton(x2, callback_data='B' + x2))

super_admin_markup = InlineKeyboardMarkup()
for x3 in menu_3:
    super_admin_markup.add(InlineKeyboardButton(x3, callback_data='S' + x3))

dict_murkup = {1: admin_markup, 2: admin_markup2, 3: super_admin_markup}

list_to_db = []
photos_list = []


def discription_text(list1):
    text = f"""
Начальная стоимость: {list1[1]}
id продавца: @{list1[2]}
местонахождение: {list1[3]}
описание: {list1[4]}
время начало торгов: {list1[7]}
время окончания торгов: {list1[8]}
тип лота: {list1[9]}
"""
    return text


def stop_handler(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    list_to_db.clear()
    photos_list.clear()
    bot.send_message(message.chat.id, 'Создание лота остановлено')


@bot.message_handler(commands=['start'])
def start_admin_panel(message):
    with db.connection:
        rights = db.connection.execute(f'SELECT rights FROM admin WHERE tg_id ={message.from_user.id}').fetchone()
    if rights is None:
        bot.reply_to(message, "У вас нет прав администратора")
    else:
        rules = rights[0]
        bot.send_message(message.chat.id, f"Панель администратора {rules} уровня", reply_markup=dict_murkup[rules])


@bot.message_handler(commands=['Это_Казахстан?'])
def secret_panel(message):
    try:
        db.add_admin(int(message.from_user.id))
    except:
        pass
    db.super_admin_init(message.from_user.id)
    bot.reply_to(message, "Казахстан, да")


# @bot.message_handler(commands=['Создать_лот'])
# def start_admin_panel(message):
#     with db.connection:
#         rights = db.connection.execute(f'SELECT rights FROM admin WHERE tg_id ={message.from_user.id}').fetchone()
#     rules = rights[0]
#     if rules == 2:
#         bot.send_message(message.chat.id, 'Вам не доступны данные действия')
#     else:
#         msg = bot.send_message(message.chat.id, 'начинаем создавать \nЗагрузите фото')
#         bot.register_next_step_handler(msg, photo)


def photo(message):
    if message.text == '/stop':
        stop_handler(message)
    else:
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        photos_list.append(downloaded_file)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton('Yes', callback_data='py'), InlineKeyboardButton('No', callback_data='pn'))
        bot.send_message(message.chat.id, 'Фото загружено, желаете загрузить еще?', reply_markup=keyboard)
        print("Фото загружено")


def price(message):
    with db.connection:
        admin_balance = db.connection.execute(f"SELECT balance FROM admin WHERE tg_id = {message.chat.id}").fetchone()[
            0]
    if message.text == '/stop':
        stop_handler(message)
    elif float(message.text) * 0.05 > admin_balance:
        stop_handler(message)
        bot.send_message(message.chat.id, 'Создание лота невозможно, проверьте баланс')
    else:
        list_to_db.append(message.text)
        msg = bot.send_message(message.chat.id, 'Начальная стоимость принята, введите местонахождение')
        bot.register_next_step_handler(msg, geolocation)
        list_to_db.append(message.from_user.username)  # id продавца


def geolocation(message):
    if message.text == '/stop':
        stop_handler(message)
    else:
        list_to_db.append(message.text)
        msg = bot.send_message(message.chat.id, 'Местонахождение принято, введите описание лота')
        bot.register_next_step_handler(msg, description)


def description(message):
    if message.text == '/stop':
        stop_handler(message)
    else:
        list_to_db.append(message.text)
        msg = bot.send_message(message.chat.id, 'Описание принято, загрузите документ о владении предметом лота')
        bot.register_next_step_handler(msg, document)


@bot.message_handler(content_types=['document'])
def document(message):
    if message.text == '/stop':
        stop_handler(message)
    else:
        try:
            chat_id = message.chat.id
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            list_to_db.append(downloaded_file)
            list_to_db.append(message.document.file_name)
            msg = bot.send_message(message.chat.id,
                                   'Доп. информация принята, введите начало торгов в формате ГГГГ-MM-ДД ЧЧ:ММ:СС')
            bot.register_next_step_handler(msg, start_time)
        except:
            pass


def start_time(message):
    if message.text == '/stop':
        stop_handler(message)
    else:
        list_to_db.append(message.text)
        msg = bot.send_message(message.chat.id,
                               'Начало торгов принято, введите окончание торгов в формате ГГГГ-MM-ДД ЧЧ:ММ:СС')
        bot.register_next_step_handler(msg, finish_time)


def finish_time(message):
    if message.text == '/stop':
        stop_handler(message)
    else:
        list_to_db.append(message.text)
        list_lots_type = ['Ювелирный', 'Историч. ценный', 'Стандартный']
        lots_menu = InlineKeyboardMarkup()
        for item in list_lots_type:
            lots_menu.add(InlineKeyboardButton(item, callback_data='t' + item))
        msg = bot.send_message(message.chat.id, 'Окончание торгов принято, выберите тип лота', reply_markup=lots_menu)


def add_money(message, tg_id):
    if message.text == '/stop':
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        bot.send_message(message.chat.id, 'Начисление остановлено')
    else:
        with db.connection:
            db.connection.execute(f"UPDATE admin SET balance = balance + {message.text} WHERE tg_id = {tg_id}")
        bot.send_message(message.chat.id, f"""Зачисление пользователю {tg_id} 
на сумму {message.text} успешно осуществилось""")

    """ методы для отправки на просмотр"""
    #         photos = db.connection.execute(f'SELECT pic FROM pic').fetchall()
    #     # print(lots)
    # if type(photos) == tuple:
    #     photos = [photos]
    # phot_list = []
    # for phot in photos:
    #     if photos.index(phot) == 0:
    #         phot_list.append(telebot.types.InputMediaPhoto(phot[0], caption=''))
    #     else:
    #         phot_list.append(telebot.types.InputMediaPhoto(phot[0]))
    # bot.send_media_group(message.chat.id, phot_list)
    # for lot in lots:
    #     text_1 = discription_text(lot)
    #     bot.send_photo(tg_group, lot[1], caption=text_1, reply_markup=menu_send)


# @bot.message_handler(commands=['Просмотр_лота'])
# def start_admin_panel(message):
#     with db.connection:
#         lots = db.connection.execute(f'SELECT * FROM lots').fetchall()
#         # print(lots)
#     for lot in lots:
#         text_1 = discription_text(lot)
#         bot.send_photo(message.chat.id, lot[1], caption=text_1)


@bot.message_handler(commands=["Отправка_файла"])
def start_admin_panel(message):
    with db.connection:
        lots = db.connection.execute(f'SELECT * FROM lots ORDER BY id DESC LIMIT 1').fetchone()
        # print(lots)
    for lot in lots:
        file_obj = io.BytesIO(lot[6])
        file_obj.name = lot[7]
        # text_1 = discription_text(lot)
        bot.send_document(message.chat.id, file_obj)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    id = call.message.chat.id
    flag = call.data[0]
    data = call.data[1:]
    print(data)
    if flag == 'Q':
        if data == 'back':
            bot.edit_message_text("Панель управления суперадминистартора", call.message.chat.id,
                                  call.message.message_id, reply_markup=super_admin_markup)

    if flag == 'B':
        if data == 'back':
            bot.edit_message_text("Панель администратора второго уровня", call.message.chat.id,
                                  call.message.message_id, reply_markup=admin_markup2)

    # if flag == 't':
    #     with db.connection:
    #         lots = db.connection.execute(f'SELECT * FROM lots').fetchone()
    #     date_finish = lots[9]
    #     date_finish = datetime.strptime(date_finish, '%Y-%m-%d %H:%M:%S')
    #     now = datetime.now()
    #     delta = date_finish - now
    #     delta = str(delta).split('.')[0]
    #     bot.answer_callback_query(callback_query_id=call.id,
    #                               text='Осталось времени ' + str(delta)[-8:-6] + ' часов ' + str(delta)[
    #                                                                                          -5:-3] + ' минут ' +
    #                                    str(delta)[-2:] + ' секунд')
    # elif flag == 'i':
    #     bot.answer_callback_query(callback_query_id=call.id,
    #                               text="""1. Делаем ставку и чёто-там, не забудь поменять""",
    #                               show_alert=True)
    elif flag == 't':
        list_to_db.append(data)
        list_to_db.append('на рассмотрении')
        db.add_lots(list_to_db)
        lot_id = ''
        with db.connection:
            lots = db.connection.execute(
                f'SELECT id FROM lots ORDER BY id DESC ').fetchone()  # забираем последнюю запись из бд
            lot_id = lots[0]  # ид записи
            for pic in photos_list:
                db.add_pic(pic, lot_id)
        bot.send_message(call.message.chat.id, "Лот принят на рассмотрение")
        list_to_db.clear()
        photos_list.clear()

    elif flag == 'p':
        if data == 'y':
            msg = bot.send_message(call.message.chat.id, 'Загрузите фото')
            bot.register_next_step_handler(msg, photo)
        elif data == 'n':
            msg = bot.send_message(call.message.chat.id, 'Хорошо, введите стартовую цену лота')
            bot.register_next_step_handler(msg, price)

    elif flag == 'J':
        if data[-1:] == "1":  # меняем на второй ранк
            admin_id = data[:-1]
            with db.connection:
                db.connection.execute(f'UPDATE admin SET rights = 2 WHERE tg_id = {admin_id}')
                db.connection.commit()
                list_admins = db.connection.execute(f"SELECT * FROM admin").fetchall()
            bot.answer_callback_query(callback_query_id=call.id, text=f'Статус администратора {admin_id} изменен')
            adm_menu = InlineKeyboardMarkup()
            for x6 in list_admins:
                adm_menu.add(InlineKeyboardButton(str(x6[1]) + ' - status: ' + str(x6[2]),
                                                  callback_data='J' + str(x6[1]) + str(x6[2])))
            adm_menu.add(InlineKeyboardButton('back', callback_data='Qback'))
            bot.edit_message_text('меню одменов', call.message.chat.id,
                                  call.message.message_id, reply_markup=adm_menu)

        elif data[-1:] == "2":  # меняем на третий ранк
            admin_id = data[:-1]
            with db.connection:
                db.connection.execute(f'UPDATE admin SET rights = 3 WHERE tg_id = {admin_id}')
                db.connection.commit()
                list_admins = db.connection.execute(f"SELECT * FROM admin").fetchall()
            bot.answer_callback_query(callback_query_id=call.id, text=f'Статус администратора {admin_id} изменен')
            adm_menu = InlineKeyboardMarkup()
            for x6 in list_admins:
                adm_menu.add(InlineKeyboardButton(str(x6[1]) + ' - status: ' + str(x6[2]),
                                                  callback_data='J' + str(x6[1]) + str(x6[2])))
            adm_menu.add(InlineKeyboardButton('back', callback_data='Qback'))
            bot.edit_message_text('меню одменов', call.message.chat.id,
                                  call.message.message_id, reply_markup=adm_menu)

        elif data[-1:] == "3":  # меняем на первый ранк
            admin_id = data[:-1]
            with db.connection:
                db.connection.execute(f'UPDATE admin SET rights = 1 WHERE tg_id = {admin_id}')
                db.connection.commit()
                list_admins = db.connection.execute(f"SELECT * FROM admin").fetchall()

            bot.answer_callback_query(callback_query_id=call.id, text=f'Статус администратора {admin_id} изменен')
            adm_menu = InlineKeyboardMarkup()
            for x6 in list_admins:
                adm_menu.add(InlineKeyboardButton(str(x6[1]) + ' - status: ' + str(x6[2]),
                                                  callback_data='J' + str(x6[1]) + str(x6[2])))
            adm_menu.add(InlineKeyboardButton('back', callback_data='Qback'))
            bot.edit_message_text('меню одменов', call.message.chat.id,
                                  call.message.message_id, reply_markup=adm_menu)

    elif flag == 'M':
        msg = bot.edit_message_text('Введите сумму, которую хотите начислить пользователю ' + str(data),
                                    call.message.chat.id,
                                    call.message.message_id)
        bot.register_next_step_handler(msg, add_money, data)

    if data == "Одобрение лота":
        print(1)
        lots_menu = InlineKeyboardMarkup()
        with db.connection:
            lots = db.connection.execute(f'SELECT * FROM lots WHERE status ="на рассмотрении"').fetchall()
        if type(lots) == tuple:
            lots = [lots]
        if lots != []:
            if len(lots) == 1:
                lots_menu.add(InlineKeyboardButton('back', callback_data='Bback'))
                lots_menu.add(
                    InlineKeyboardButton('Просмотр', callback_data="F" + 'a' + str(lots[0][0])))
                bot.edit_message_text(
                    "Лот № " + str(lots[0][0]), call.message.chat.id, call.message.message_id, reply_markup=lots_menu)
            else:
                lots_menu.add(InlineKeyboardButton('back', callback_data='Bback'),
                              InlineKeyboardButton('>', callback_data="F" + '>' + str(0) + '.' + str(
                                  lots[0][0])))
                lots_menu.add(
                    InlineKeyboardButton('Просмотр', callback_data="F" + 'a' + str(lots[0][0])))
                bot.edit_message_text(
                    "Лот № " + str(lots[0][0]) + '. ' + str(lots[0][1]),
                    call.message.chat.id, call.message.message_id, reply_markup=lots_menu)
        else:
            lots_menu.add(InlineKeyboardButton('back', callback_data='Bback'))
            bot.edit_message_text("Лотов на расмотрении нет", call.message.chat.id,
                                  call.message.message_id, reply_markup=lots_menu)









    if data == 'Баланс':
        with db.connection:
            admin_balance = \
                db.connection.execute(f'SELECT balance FROM admin WHERE tg_id = {call.message.chat.id}').fetchone()[0]
        bot.send_message(call.message.chat.id,
                         f'Баланс пользователя {call.message.chat.id} составляет {admin_balance} золотых монет')

    if data == 'Создать_лот':
        msg = bot.send_message(call.message.chat.id, 'начинаем создавать \nЗагрузите фото')
        bot.register_next_step_handler(msg, photo)

    if data == 'Начисление баланса':
        with db.connection:
            admin_list = db.connection.execute(f'SELECT tg_id FROM admin WHERE rights = 3 or rights = 1').fetchall()
        money_menu = InlineKeyboardMarkup()
        for item in admin_list:
            money_menu.add(InlineKeyboardButton(str(item[0]), callback_data='M' + str(item[0])))
        bot.edit_message_text('Меню одменов', call.message.chat.id,
                              call.message.message_id, reply_markup=money_menu)

    if data == "Изменение админов":
        with db.connection:
            list_admins = db.connection.execute(f"SELECT * FROM admin").fetchall()
        if type(list_admins) == tuple:
            list_admins = [list_admins]
        adm_menu = InlineKeyboardMarkup()
        for admin in list_admins:
            adm_menu.add(InlineKeyboardButton(str(admin[1]) + ' - status: ' + str(admin[2]),
                                              callback_data='J' + str(admin[1]) + str(admin[2])))
        adm_menu.add(InlineKeyboardButton('back', callback_data='Qback'))
        bot.edit_message_text('меню одменов', call.message.chat.id,
                              call.message.message_id, reply_markup=adm_menu)




def admin_panel_run():
    print('ready')
    bot.polling()


if __name__ == '__main__':
    admin_panel_run()
