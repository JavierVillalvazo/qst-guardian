import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_8")  # Cambia la ruta si es necesario

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
port = os.getenv("PORT")
service_name = os.getenv("SERVICE_NAME")

dsn = oracledb.makedsn(host, port, service_name=service_name)

try:
    print("\n🔌 Intentando conectar a Oracle en modo THICK...")
    connection = oracledb.connect(user=username, password=password, dsn=dsn)
    cursor = connection.cursor()
    cursor.execute("SELECT SYSDATE FROM DUAL")
    print(f"✅ Conexión exitosa. Fecha/hora actual del servidor: {cursor.fetchone()[0]}")
    connection.close()
except Exception as e:
    print("❌ Error al conectar a la base de datos:")
    print(e)
