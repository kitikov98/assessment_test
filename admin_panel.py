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
menu_send.add(InlineKeyboardButton(text="учавствовать", url="https://t.me/kitikov98_study_bot?start=11"))
menu_send.add(InlineKeyboardButton('время', callback_data='t'+'0'), InlineKeyboardButton('info', callback_data='i'+'0'))

menu_1 = ["/Создать_лот", "/Отправка_файла"]
menu_2 = ["Добавление", "Изменение", "Удаление", "Назад"]

# Клавиатура для администраторов
admin_markup = ReplyKeyboardMarkup()

for x1 in menu_1:
    admin_markup.add(KeyboardButton(x1))


list_to_db = []


def discription_text(list1):
    text = f"""
Начальная стоимость: {list1[2]}
id продавца: @{list1[3]}
местонахождение: {list1[4]}
описание: {list1[5]}
время начало торгов: {list1[8]}
время окончания торгов: {list1[9]}
тип лота: {list1[10]}
"""
    return text


@bot.message_handler(commands=['start'])
def start_admin_panel(message):
    # Проводим проверку является ли пользователь администратором
    bot.send_message(message.chat.id, 'Hi', reply_markup=admin_markup)


@bot.message_handler(commands=['Создать_лот'])
def start_admin_panel(message):
    # Проводим проверку является ли пользователь администратором
    msg = bot.send_message(message.chat.id, 'начинаем создавать \nЗагрузите фото')
    bot.register_next_step_handler(msg, photo)


@bot.message_handler(content_types=['photo'])
def photo(message):
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    list_to_db.append(downloaded_file)
    msg = bot.send_message(message.chat.id, 'Фото загружено, введите стартовую цену лота')
    bot.register_next_step_handler(msg, price)
    print("файл закрыт")


def price(message):
    list_to_db.append(message.text)
    msg = bot.send_message(message.chat.id, 'Начальная стоимость принята, введите местонахождение')
    bot.register_next_step_handler(msg, geolocation)
    list_to_db.append(message.from_user.username)  # id продавца


def geolocation(message):
    list_to_db.append(message.text)
    msg = bot.send_message(message.chat.id, 'Местонахождение принято, введите описание лота')
    bot.register_next_step_handler(msg, description)


def description(message):
    list_to_db.append(message.text)
    msg = bot.send_message(message.chat.id, 'Описание принято, загрузите дополнительную информацию, если есть')
    bot.register_next_step_handler(msg, document)


@bot.message_handler(content_types=['document'])
def document(message):
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
    list_to_db.append(message.text)
    msg = bot.send_message(message.chat.id,
                           'Начало торгов принято, введите окончание торгов в формате ГГГГ-MM-ДД ЧЧ:ММ:СС')
    bot.register_next_step_handler(msg, finish_time)


def finish_time(message):
    list_to_db.append(message.text)
    msg = bot.send_message(message.chat.id, 'Окончание торгов принято, введите тип лота')
    bot.register_next_step_handler(msg, lot_type)


def lot_type(message):
    list_to_db.append(message.text)
    # bot.send_message(message.chat.id, 'Тип лота принят, лот выставлен на рассмотрение')
    list_to_db.append('на рассмотрении')
    db.add_lots(list_to_db)
    with db.connection:
        lots = db.connection.execute(f'SELECT * FROM lots ORDER BY id DESC LIMIT 1').fetchall()
        # print(lots)
    for lot in lots:
        text_1 = discription_text(lot)
        bot.send_photo(tg_group, lot[1], caption=text_1, reply_markup=menu_send)


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

def admin_panel_run():
    print('ready')
    bot.polling()


if __name__ == '__main__':
    admin_panel_run()
