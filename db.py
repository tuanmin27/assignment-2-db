import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "database": "EcommerceDB",   # đúng tên DB
    "user": "sManager",                      # đúng user bạn tạo
    "password": "123456",                   # đúng mật khẩu bạn đã set
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)
