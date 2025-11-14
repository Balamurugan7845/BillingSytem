import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'bala1234')
    MYSQL_DB = os.getenv('MYSQL_DB', 'shop_billing')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))