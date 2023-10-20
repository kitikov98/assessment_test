import sqlite3
from io import BytesIO
from base64 import b64decode
from PIL import Image
from datetime import datetime, timedelta


def convert_to_pic(str1):
    image = BytesIO(b64decode(str1))
    pillow = Image.open(image)
    return pillow


class Database:
    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        # self.connection = self.connection.connection()
        self.create_tables()

    def create_tables(self):
        self.connection.execute('''CREATE TABLE IF NOT EXISTS lots (id INTEGER PRIMARY KEY,
        start_price INTEGER, trader_link TEXT, geolocation TEXT, description TEXT, additional_information BLOB,
        file_name TEXT, time_start DATETIME, time_finish DATETIME, type TEXT,
        status text, pic BLOB, message_id INTEGER)''')

        self.connection.execute('''CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY, tg_id INTEGER,
         rights INTEGER, balance INTEGER, strike_status INTEGER)''')

        self.connection.execute('''CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY, admin_id INTEGER,
                 user_id INTEGER, status TEXT, description TEXT, relationship TEXT)''')

        self.connection.execute('''CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, tg_id INTEGER UNIQUE,
                 balance INTEGER, number_of_payments INTEGER, status_auto_bid BOOL, strike_status INTEGER)''')

        self.connection.execute('''CREATE TABLE IF NOT EXISTS bids (id INTEGER PRIMARY KEY, lot_id INTEGER,
                         bid INTEGER, user_id INTEGER)''')

        self.connection.commit()

    def add_lots(self, list_info):
        with self.connection:
            self.connection.execute(f"""INSERT INTO lots (start_price, trader_link, geolocation, description,
             additional_information, file_name, time_start, time_finish, type, status, pic)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""", list_info)

    def add_admin(self, tg_id):
        with self.connection:
            self.connection.execute(f"""INSERT INTO admin (tg_id, rights, balance, strike_status)
             VALUES(?,?,?,?)""", (tg_id, 0, 0, 0))

    def super_admin_init(self, tg_id):
        with self.connection:
            self.connection.execute(f"""UPDATE admin SET rights = 3 WHERE tg_id = {tg_id}""")


db = Database('auction.db')
