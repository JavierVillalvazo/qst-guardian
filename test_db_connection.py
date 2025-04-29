import os
import pyodbc
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

# Obtener variables del entorno
server = os.getenv("SERVER")
database = os.getenv("DATABASE")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

# Mostrar los parámetros (sin imprimir la contraseña)
print("Parámetros de conexión:")
print(f"SERVER: {server}")
print(f"DATABASE: {database}")
print(f"USERNAME: {username}")
print("PASSWORD: ********")

# Construir cadena de conexión
con_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password}"
)

# with open(".env", "r") as f:
#     print("\n Contenido actual del .env:")
#     print(f.read())

# Intentar conectar
try:
    print("\n🔌 Intentando conectar a la base de datos...")
    conn = pyodbc.connect(con_str)
    cursor = conn.cursor()
    cursor.execute("SELECT GETDATE() AS CurrentDateTime")
    row = cursor.fetchone()
    print(f"Conexión exitosa. Fecha/hora actual del servidor: {row.CurrentDateTime}")
    conn.close()
except Exception as e:
    print("Error al conectar a la base de datos:")
    print(e)
