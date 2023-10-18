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
        file_name TEXT, time_start DATETIME, time_finish DATETIME, type TEXT, status text)''')

        self.connection.execute('''CREATE TABLE IF NOT EXISTS pic (id INTEGER PRIMARY KEY, pic BLOB, lot_id INTEGER)''')

        self.connection.commit()

    def add_lots(self, list_info):
        with self.connection:
            self.connection.execute(f"""INSERT INTO lots (start_price, trader_link, geolocation, description,
             additional_information, file_name, time_start, time_finish, type, status)
            VALUES(?,?,?,?,?,?,?,?,?,?)""", list_info)

    def add_pic(self, pic, lot_id):
        with self.connection:
            self.connection.execute(f"""INSERT INTO pic (pic, lot_id) VALUES(?,?)""", (pic, lot_id))




db = Database('auction.db')
