import os
import oracledb
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

# Obtener variables del entorno
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")        # Ejemplo: "localhost" o "192.168.1.100"
port = os.getenv("PORT", "1521") # Puerto típico de Oracle
service_name = os.getenv("SERVICE_NAME")  # Nombre del servicio (SID o SERVICE_NAME)

# Validar
if not all([username, password, host, port, service_name]):
    raise ValueError("Faltan variables de entorno necesarias para conectar a Oracle.")

# Mostrar (sin imprimir contraseña)
print("Parámetros de conexión:")
print(f"HOST: {host}")
print(f"PORT: {port}")
print(f"SERVICE_NAME: {service_name}")
print(f"USERNAME: {username}")
print("PASSWORD: ********")

# Construir cadena de conexión
# dsn = cx_Oracle.makedsn(host, port, service_name=service_name)

# Intentar conectar
try:
    print("\n🔌 Intentando conectar a Oracle...")
    conn = oracledb.connect(user=username, password=password, dsn=dsn)
    cursor = conn.cursor()
    cursor.execute("SELECT SYSDATE FROM DUAL")
    row = cursor.fetchone()
    print(f"Conexión exitosa. Fecha/hora actual del servidor: {row[0]}")
    conn.close()
except Exception as e:
    print("Error al conectar a la base de datos:")
    print(e)
