import pyodbc
from database import get_connection_string 

def get_connection():
    """
    Establece y devuelve una conexión a la base de datos de SQL Server
    obteniendo la cadena de conexión desde database.py.

    Returns:
        pyodbc.Connection: Un objeto de conexión a la base de datos, o None si la conexión falla.
    """ 
    conn_str = get_connection_string()
    conn = None
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Error al conectar a SQL Server en fpy_calculate: {sqlstate}")
        return None
    except Exception as e:
        print(f"Error general al conectar a SQL Server en fpy_calculate: {e}")
        return None

def get_fpy_from_db(conn):
    """
    Obtiene el valor del First Pass Yield (FPY) por nodo desde la vista vw_FPY_ByModelNode
    usando una conexión existente.

    Args:
        conn (pyodbc.Connection): Un objeto de conexión a la base de datos de SQL Server.

    Returns:
        dict: Un diccionario donde las claves son los nodos y los valores son los FPY correspondientes.
              Devuelve un diccionario vacío si ocurre un error o no hay datos.
    """
    fpy_by_node = {}
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Node, FPY
            FROM vw_FPY_ByModelNode;
        """)
        rows = cursor.fetchall()
        for row in rows:
            node, fpy = row
            fpy_by_node[node] = fpy
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Error de SQL Server al consultar FPY: {sqlstate}")
    except Exception as e:
        print(f"Error general al consultar FPY: {e}")
    finally:
        if cursor:
            cursor.close()
    return fpy_by_node