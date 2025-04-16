# database.py
import os
from dotenv import load_dotenv
import pyodbc

# Cargar las variables desde el archivo .env
load_dotenv()

server = os.getenv("SERVER")
database = os.getenv("DATABASE")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

def get_connection():
    con_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}"
    )
    return pyodbc.connect(con_str)
# print("Database connection string loaded successfully.")
# print(f"Server: {server}, Database: {database}, Username: {username}")