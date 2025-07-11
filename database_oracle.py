# database.py
import os
from dotenv import load_dotenv
import pyodbc
import oracledb


# loading environment variables from .env file
load_dotenv()

# oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_12_2")  

or_lib_dir = os.getenv("ORACLE_CLIENT_LIB_DIR")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
port = os.getenv("PORT")
service_name = os.getenv("SERVICE_NAME")

try:
    oracledb.init_oracle_client(lib_dir=or_lib_dir)
    print(f"Info: Cliente Oracle inicializado exitosamente desde: {or_lib_dir}")
except oracledb.Error as e:
    print(f"ERROR: Fallo al inicializar el cliente Oracle. Verifica la ruta '{or_lib_dir}'.")
    print(f"Detalle del error: {e}")
    exit(1) # Salir si el cliente no puede inicializarse
except Exception as e:
    print(f"ERROR inesperado al inicializar el cliente Oracle: {e}")
    exit(1)
    
    
    
    
def get_connection():
    dsn = oracledb.makedsn(host, port, service_name=service_name)

    try:
        # Attempt to establish a connection to the database
        conn = oracledb.connect(user=username, password=password, dsn=dsn)
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
