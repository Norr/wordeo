import sys
sys.path.append("..")
import os

from dotenv import load_dotenv
from cryptography.fernet import Fernet
from sqlalchemy import create_engine

load_dotenv()

DB_PASSWD= os.getenv("DB_PASSWD")
KEY = os.getenv("KEY")
KEY = KEY if KEY.endswith("=") else KEY + "="
F = Fernet(KEY)
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_USERNAME = os.getenv("DB_USER")
DB_PASSWD = F.decrypt(DB_PASSWD.encode()).decode()
DB_PORT = 3306

class Database:
    def __init__(self) -> None:
        __connector = f'mysql+mysqlconnector:'\
                    f'//{DB_USERNAME}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        self.engine = None
        try:
            self.engine = create_engine(__connector)
        except BaseException:
            print("Can't connect to database")

    def _get_engine(self):
        return self.engine
        