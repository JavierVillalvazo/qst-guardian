import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

or_lib_dir =os.getenv("ORACLE_CLIENT_LIB_DIR")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
port = os.getenv("PORT")
service_name = os.getenv("SERVICE_NAME")

oracledb.init_oracle_client(lib_dir=or_lib_dir) 
dsn = oracledb.makedsn(host, port, service_name=service_name)

try:
    connection = oracledb.connect(user='mes', password=password, dsn=dsn)
    cursor = connection.cursor()
    cursor.execute("SELECT SYSDATE FROM DUAL")
    print(f"Connection successful. \n Current server date/time: {cursor.fetchone()[0]}")
    connection.close()
except Exception as e:
    print("❌ Error connecting to the database:")
    print(e)
