# database.py
import os
from dotenv import load_dotenv
import pyodbc

# loading environment variables from .env file
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
    try:
        # Attempt to establish a connection to the database
        conn = pyodbc.connect(con_str)
        # print("Database connection string loaded successfully.")
        # print(f"Server: {server}, Database: {database}, Username: {username}")
        return conn
    except pyodbc.OperationalError as e:
        # Error connection to database in get_connection()
        print(f"Error al conectar a la base de datos en get_connection(): {e}") # Para depuración en la terminal
        return None
    except Exception as e:
        print(f"Ha ocurrido un error inesperado intentando conectar a la base de datos {e}") # Para otros errores
        return None

connection_string = get_connection()
if connection_string is not None:
    print("Conexión a la base de datos establecida correctamente.")
else:
    print("No se pudo establecer la conexión a la base de datos. Verifique las credenciales y la configuración.")
