# QST Guardian - Documentación
Este documento proporciona información sobre cómo configurar y ejecutar la aplicación QST Guardian.
## Contenido
1.  [Requisitos](#requisitos)
2.  [Instalación](#instalación)
    * [Creación de un entorno virtual (.venv)](#creación-de-un-entorno-virtual-venv)
    * [Instalación de dependencias (requirements.txt)](#instalación-de-dependencias-requirementstxt)
1.  [Configuración de la base de datos](#configuración-de-la-base-de-datos)
    * [Definición de la cadena de conexión en .env](#definición-de-la-cadena-de-conexión-en-env)
    * [Prueba de la conexión a la base de datos (database.py)](#prueba-de-la-conexión-a-la-base-de-datos-databasepy)
1.  [Ejecución de la aplicación](#ejecución-de-la-aplicación)
2.  [Configuración de la ruta de monitoreo y la carpeta de errores](#configuración-de-la-ruta-de-monitoreo-y-la-carpeta-de-errores)

## 1. Requisitos
* Python 3.6 o superior instalado en tu sistema.
* Acceso a una base de datos compatible (la configuración se realiza en el `.env`).
## 2. Instalación
Sigue estos pasos para preparar el entorno de desarrollo:
### Creación de un entorno virtual (.venv)
Un entorno virtual ayuda a aislar las dependencias del proyecto.
1.  Abre tu terminal o símbolo del sistema.
2.  Navega al directorio raíz de tu proyecto.
3.  Ejecuta el siguiente comando para crear un entorno virtual llamado `.venv`:

    ```shell
    python -m venv .venv
    ```
4.  Activa el entorno virtual:
    * **En Windows:**
        ```shell
        .venv\Scripts\activate
        ```

    * **En macOS y Linux:**
        ```bash
        source .venv/bin/activate
        ```
    Una vez activado, verás `(.venv)` al principio de tu línea de comandos.
### Instalación de dependencias (requirements.txt)
El archivo `requirements.txt` lista todas las bibliotecas necesarias para el proyecto.
1.  Asegúrate de que tu entorno virtual esté activado.
2.  Ejecuta el siguiente comando desde el directorio raíz del proyecto para instalar las dependencias:

    ```shell
    pip install -r requirements.txt
    ```
    
    Esto instalará bibliotecas como `customtkinter`, `pystray`, `PIL`, `watchdog`, `python-dotenv` y el conector de base de datos que estés utilizando (por ejemplo, `pyodbc` para SQL Server, `mysql-connector-python` para MySQL, `psycopg2` para PostgreSQL).
## 3. Configuración de la base de datos
La conexión a la base de datos se configura a través de un archivo `.env`.
### Definición de la cadena de conexión en .env
El archivo `.env` contiene variables de entorno, incluyendo la cadena de conexión a tu base de datos.
1.  Crea un archivo llamado `.env` en el directorio raíz de tu proyecto (si aún no existe).
2.  Define la cadena de conexión a tu base de datos bajo una variable apropiada. El nombre de la variable dependerá de cómo esté configurado tu archivo `database.py`. Un ejemplo común para una conexión a SQL Server usando `pyodbc` sería:
3. 
    ```.env  title:"Configura tu conexión con la base de datos"
       SERVER=your_server_name
       DATABASE=your_database_name
       USERNAME=your_username
       PASSWORD=your_password
    ```
    **Importante:** Reemplaza `your_server_name`, `your_database_name`, `your_username` y `your_password` con los detalles de tu base de datos. Si utilizas otro tipo de base de datos o conector, la estructura de la cadena de conexión será diferente. Consulta la documentación del conector de tu base de datos para obtener el formato correcto.
### Prueba de la conexión a la base de datos (database.py)
El archivo `database.py` contiene la lógica para establecer la conexión a la base de datos. Puedes probar si la conexión se establece correctamente ejecutando este archivo.
1.  Asegúrate de que tu entorno virtual esté activado y que las dependencias estén instaladas (incluyendo el conector de base de datos).
2.  Abre tu terminal o símbolo del sistema.
3.  Navega al directorio donde se encuentra `database.py`.
4.  Ejecuta el archivo Python:
    ```shell
    python database.py
    ```
    Si la configuración en tu archivo `.env` es correcta y la base de datos es accesible, el script debería ejecutarse sin errores o mostrar un mensaje indicando que la conexión fue exitosa. Si hay algún problema, revisa tu cadena de conexión en el archivo `.env` y asegúrate de que los detalles sean correctos y que la base de datos esté en funcionamiento.
## 4. Ejecución de la aplicación
Para ejecutar la aplicación QST Guardian:
1.  Asegúrate de que tu entorno virtual esté activado.
2.  Navega al directorio raíz de tu proyecto.
3.  Ejecuta el script principal:
    ```shell
    python file-monitor.pyw
    ```
    Esto iniciará la aplicación, que comenzará a monitorear la carpeta configurada en busca de archivos `.QST`.
## 5. Configuración de la ruta de monitoreo y la carpeta de errores
La ruta de la carpeta que la aplicación monitorea y la carpeta donde se moverán los archivos con errores se pueden configurar de dos maneras:
* **Directamente en el script `file-monitor.pyw`:** Puedes editar las variables `MONITOR_PATH` y `ERROR_FOLDER` al principio del archivo para establecer las rutas deseadas.
* **A través de un archivo `.env`:** Puedes definir las variables de entorno `MONITOR_PATH` y `ERROR_FOLDER` en el archivo `.env`. La aplicación leerá estos valores al inicio. Si las variables no están definidas en `.env`, se utilizarán los valores predeterminados definidos en el script.
**Recomendación:** Utilizar el archivo `.env` es una mejor práctica, ya que mantiene la configuración separada del código.
---
## Preguntas Frecuentes

**P: ¿Cómo pruebo si mi archivo `database.py` se conecta correctamente a la base de datos?**
**R:** Para probar la conexión a la base de datos utilizando `database.py`  
1.  Asegúrate de haber configurado correctamente la cadena de conexión en el archivo `.env`.
2.  Asegúrate de haber instalado el conector de base de datos necesario (por ejemplo, `pyodbc`).
3.  Abre tu terminal o símbolo del sistema, navega al directorio donde se encuentra `database.py` y ejecuta `python database.py`.
4.  Si la conexión es exitosa, el script debería completarse sin errores o imprimir un mensaje de éxito (si está programado para hacerlo). Si hay errores, revisa tu cadena de conexión y asegúrate de que la base de datos esté accesible.
---
**P: ¿Cómo creo y defino la cadena de conexión de la base de datos en el archivo `.env`?**
**R:** Para crear y definir la cadena de conexión en `.env`:
 5.  Crea un archivo llamado `.env` en el directorio raíz de tu proyecto.
6.  Define una variable para tu cadena de conexión. Un nombre común es `DATABASE_CONNECTION_STRING`.
7.  El valor de esta variable será la cadena de conexión específica para tu sistema de base de datos y el conector que estés utilizando. Por ejemplo, para SQL Server con `pyodbc`:
      ```env

    DATABASE_CONNECTION_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server_name;DATABASE=your_database_name;UID=your_username;PWD=your_password"

    ```
    Reemplaza los marcadores de posición con la información real de tu base de datos. Consulta la documentación de tu conector de base de datos para obtener el formato correcto de la cadena de conexión. 
   ---
**P: ¿Cómo instalo las dependencias listadas en `requirements.txt`?**
**R:** Para instalar las dependencias:
1.  Asegúrate de haber creado y activado un entorno virtual (`.venv`).
2.  Navega al directorio raíz de tu proyecto en tu terminal o símbolo del sistema.
3.  Ejecuta el comando: `pip install -r requirements.txt`.
4.  Esto leerá el archivo `requirements.txt` e instalará todas las bibliotecas listadas dentro de tu entorno virtual.

---
**P: ¿Cómo creo un entorno virtual `.venv` para mi proyecto?**
**R:** Para crear un entorno virtual llamado `.venv`: 
5.  Abre tu terminal o símbolo del sistema.
6.  Navega al directorio raíz de tu proyecto.
7.  Ejecuta el comando: `python -m venv .venv`.
8.  Luego, activa el entorno virtual:
    * **Windows:** `.venv\Scripts\activate`
    * **macOS y Linux:** `source .venv/bin/activate`
1.  Una vez activado, verás `(.venv)` al principio de tu línea de comandos, indicando que estás trabajando dentro del entorno virtual.