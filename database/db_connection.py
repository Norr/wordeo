import os

from dotenv import load_dotenv
from cryptography.fernet import Fernet
from sqlalchemy import create_engine

load_dotenv()
DB_PASSWD= os.getenv("DB_PASSWD")
KEY = os.getenv("KEY")
F = Fernet(KEY)
DB_NAME = "baza67_wordeo"
DB_HOST = "22267.m.tld.pl"
DB_USERNAME = "admin67_wordeo"
DB_PASSWD = F.decrypt(DB_PASSWD.encode()).decode()
DB_PORT = 3306

class Database:
    def __init__(self) -> None:
        __connector = f'mysql+mysqlconnector:'\
                    f'//{DB_USERNAME}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        
        self.engine = create_engine(__connector)
    def _get_engine(self):
        return self.engine
        