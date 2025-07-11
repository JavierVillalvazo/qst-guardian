import tkinter as tk
import customtkinter as ctk
from tkinter import scrolledtext, messagebox
import threading
import time
import os
import sys
from datetime import datetime # Importar datetime directamente
import shutil
# Importa las funciones de tus módulos. Asegúrate que estos archivos existan y estén accesibles.
from file_parsing import parse_qst, get_error_folder, move_to_error_folder
from database_oracle import get_connection # Asume que esta función está en database_oracle.py
#from password_validate import PasswordDialog # Ya la tienes definida en este archivo, puedes eliminar esta línea si no la usas externamente
from pystray import Icon, MenuItem, Menu
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuración del tema
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

# --- Funciones globales ---

def is_running():
    """Verifica si una instancia de la aplicación ya se está ejecutando usando un archivo de bloqueo."""
    lock_path = "qst_monitor.lock"
    try:
        # Intenta crear el archivo de bloqueo; si existe, otra instancia está corriendo.
        with open(lock_path, "x") as f:
            # Escribe el PID para depuración
            f.write(str(os.getpid()))
        return False
    except FileExistsError:
        return True

def bring_to_front():
    """Trae la ventana existente al frente si ya está abierta."""
    # CustomTkinter no se lleva bien con un tk.Tk() desnudo para esto.
    # La forma más robusta es buscar la ventana por su título si ya está creada.
    # Si la aplicación ya está corriendo, el sys.exit() en __main__ previene que esto se ejecute realmente.
    # Esta función podría ser más compleja si la app ya está minimizada a la bandeja.
    # Por ahora, solo informamos que ya está corriendo.
    pass # La lógica de mostrar el mensaje ya se encarga de esto.

# --- Diálogo de Contraseña (ya existente y funcional) ---

class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Contraseña Requerida")
        self.geometry("300x150")
        self.resizable(False, False)
        self.grab_set() 
        self.focus()

        self.password = tk.StringVar()
        self.result = None

        self._create_widgets()

    def _create_widgets(self):
        ctk.CTkLabel(self, text="Ingrese la contraseña:").pack(pady=10)
        self.password_entry = ctk.CTkEntry(self, show="*", textvariable=self.password)
        self.password_entry.pack(padx=20, pady=5)
        self.password_entry.focus()
        self.bind('<Return>', self._submit)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=15)

        ctk.CTkButton(button_frame, text="Aceptar", command=self._submit).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=10)

    def _submit(self, event=None):
        self.result = self.password.get()
        self.destroy()

    def get_password(self):
        self.wait_window()
        return self.result

# --- Clase FileMonitor ---

class FileMonitor(FileSystemEventHandler):
    """Manejador de eventos para detectar la creación de archivos .QST en el directorio monitoreado."""
    
    def __init__(self, log_callback, is_paused, show_message_dialog_callback, is_service_running):
        self.log_callback = log_callback
        self.is_paused = is_paused
        self.show_message_dialog = show_message_dialog_callback # Renombrado para ser más general
        self.is_service_running = is_service_running
        
    def on_created(self, event):
        # Solo procesar si el servicio está activo y no pausado
        if not self.is_service_running() or self.is_paused(): 
            return 
        
        # Solo procesar archivos, no directorios, y que terminen en .QST
        if not event.is_directory and event.src_path.lower().endswith(".qst"): # Convertir a minúsculas para robustez
            file_path = event.src_path
            current_error_base_path = get_error_folder() # Define una ruta base para los errores
            
            if current_error_base_path.lower() in file_path.lower(): # Comprobar si ya está en una carpeta de errores
                # Si el archivo se detecta en la carpeta de errores, lo ignoramos.
                return

            self.log_callback("Detectado archivo .QST: ")
            
            try:
                # parse_qst ahora retorna True/False y maneja el movimiento a errores internamente si falla la BD o el parsing.
                # También debería emitir mensajes de log y show_error_dialog directamente.
                processing_successful = parse_qst(file_path, self.log_callback, self.show_message_dialog)
                
                # Si processing_successful es False, parse_qst ya habrá movido el archivo
                # a la carpeta de errores y mostrado el diálogo. No necesitamos hacerlo aquí de nuevo.
                if not processing_successful:
                    self.log_callback(f"El procesamiento de '{os.path.basename(file_path)}' falló. Ya fue movido a la carpeta de errores.")
                
            except Exception as e:
                # Esto captura errores *inesperados* que parse_qst no manejó internamente.
                # En un diseño ideal, parse_qst debería manejar la mayoría de los errores de procesamiento.
                error_message = f"Ocurrió un error crítico inesperado al procesar '{os.path.basename(file_path)}':\n{str(e)}"
                self.log_callback(f"ERROR CRÍTICO: {error_message}")
                # Mover a la carpeta de errores y mostrar diálogo si hubo una excepción aquí
                move_to_error_folder(file_path, self.log_callback, self.show_message_dialog)
                self.show_message_dialog("Error Inesperado", error_message)

# --- Clase de la Aplicación Principal ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QST File Monitor")
        self.resizable(False, False)
        self.iconbitmap(self.resource_path("qst_monitor.ico")) # Usar resource_path para iconos
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray) # Minimizar a bandeja al cerrar
        # self.overrideredirect(True) # Quitar bordes de la ventana
        # self.wm_attributes("-transparentcolor", "black") # Hacer la ventana transparente
        self.attributes("-topmost", True) # Mantener en la parte superior
        self.attributes("-alpha", 0.92) # Transparencia
        
        window_width = 520
        window_height = 500
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x_position = int((screen_width - window_width) / 2)
        y_position = int((screen_height - window_height) / 2)
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        self.service_running = True # Controla si el servicio de monitoreo está activo
        self.monitoring_paused = False # Controla si el procesamiento de archivos está pausado

        self.bold_font = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        self.mono_font = ctk.CTkFont(family="Consolas", size=15, weight="normal")

        self.observer = None # Inicializar el observador aquí

        self.create_ui()
        self.setup_tray_icon()
        self.start_monitoring() # Iniciar el monitoreo al arrancar la app

    def resource_path(self, relative_path):
        """Obtiene la ruta absoluta a un recurso, útil para ejecutables empaquetados."""
        try:
            base_path = sys._MEIPASS # Ruta para PyInstaller
        except Exception:
            base_path = os.path.abspath(".") # Ruta para desarrollo
        return os.path.join(base_path, relative_path)

    def show_message_dialog(self, title, message, is_error=True):
        """Muestra un diálogo de mensaje (error o información) al usuario."""
        if is_error:
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)

    def create_ui(self):
        """Crea los componentes principales de la interfaz de usuario."""
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Indicador de estado
        self.status_indicator = ctk.CTkLabel(
            self.header_frame,
            text="ACTIVO",
            text_color="#4CAF50",
            font=self.bold_font
        )
        self.status_indicator.pack(side="right", padx=10)
        
        ctk.CTkLabel(
            self.header_frame,
            text="STATUS:",
            text_color="white" if ctk.get_appearance_mode() == "Dark" else "black",
            font=self.bold_font
        ).pack(side="right", padx=5)

        # Marco para el área de logs
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(
            self.log_frame,
            wrap=tk.WORD,
            state='disabled',
            font=self.mono_font,
            bg="#333333" if ctk.get_appearance_mode() == "Dark" else "#f5f5f5",
            fg="white" if ctk.get_appearance_mode() == "Dark" else "black"
        )
        self.log_area.pack(fill="both", expand=True)

        # Marco de control para botones (movido a la parte inferior)
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(fill="x", padx=10, pady=(5, 10)) # Empaqueta al final

        # self.pause_btn = ctk.CTkButton(
        #     self.control_frame,
        #     text="PAUSAR",
        #     width=100,
        #     command=self.toggle_pause,
        #     fg_color="#FFA500",
        #     hover_color="#CC8400"
        # )
        # self.pause_btn.pack(side="left", padx=5)
        
        # self.clear_btn = ctk.CTkButton(
        #     self.control_frame,
        #     text="LIMPIAR LOGS",
        #     width=100,
        #     command=self.clear_log,
        #     fg_color="#607D8B",
        #     hover_color="#455A64",
        #     font=self.bold_font
        # )
        # self.clear_btn.pack(side="left", padx=5)

        # Etiqueta vacía para empujar el botón "DETENER" a la derecha
        ctk.CTkLabel(self.control_frame, text="", width=100).pack(side="left", expand=True)

        self.stop_btn = ctk.CTkButton(
            self.control_frame, # Ahora en el control_frame
            text="DETENER",
            width=100,
            command=self.toggle_service,
            fg_color="#F44336",
            hover_color="#D32F2F",
            font=self.bold_font
        )
        self.stop_btn.pack(side="right", padx=5) # Empaqueta a la derecha

    def update_status_indicator(self):
        """Actualiza el indicador de estado en la UI según el estado del servicio."""
        if not self.service_running:
            text, color = "DETENIDO", "#F44336"
        elif self.monitoring_paused:
            text, color = "PAUSADO", "#FFA500"
        else:
            text, color = "ACTIVO", "#4CAF50"
        self.status_indicator.configure(text=text, text_color=color)

    def toggle_pause(self):
        """Alterna el estado de pausa del monitoreo."""
        if not self.service_running: # No se puede pausar si el servicio está detenido
            self.log_message("Advertencia: El servicio está detenido, no se puede pausar el monitoreo.")
            return

        self.monitoring_paused = not self.monitoring_paused
        self.pause_btn.configure(text="REANUDAR" if self.monitoring_paused else "PAUSAR")
        self.update_status_indicator()
        self.log_message(f"Monitoreo {'pausado' if self.monitoring_paused else 'reanudado'}.")
        self.update_tray()

    def toggle_service(self):
        """Alterna el servicio de monitoreo (iniciar/detener). Requiere contraseña para detener."""
        if self.service_running:
            dialog = PasswordDialog(self)
            password = dialog.get_password()
            if password == "Qst2025#": # Contraseña quemada, considera usar una variable de entorno o archivo de configuración
                self._stop_service()
            elif password is not None: # Si no es None, el usuario ingresó algo incorrecto
                self.show_message_dialog("Contraseña Incorrecta", "La contraseña ingresada no es válida.", is_error=True)
        else:
            self._start_service()
            
    def _stop_service(self):
        """Detiene el servicio de monitoreo y actualiza la UI."""
        self.service_running = False
        self.stop_btn.configure(text="INICIAR")
        self.stop_btn.configure(text_color="#f3f3f3", fg_color="#4CAF50", hover_color="#388E3C")
        self.update_status_indicator()
        self.log_message("Servicio detenido.")
        self.update_tray()
        if self.observer:
            self.observer.stop() # Detiene el observador de watchdog
            self.observer.join() # Espera a que el hilo del observador termine
            self.observer = None
        
    def _start_service(self):
        """Inicia el servicio de monitoreo y actualiza la UI."""
        self.service_running = True
        self.stop_btn.configure(text="DETENER")
        self.stop_btn.configure(text_color="#f3f3f3", fg_color="#F44336", hover_color="#D32F2F")
        self.update_status_indicator()
        self.log_message("Servicio iniciado.")
        self.update_tray()
        self.start_monitoring() # Llama a la función para iniciar el monitoreo real

    def clear_log(self):
        """Limpia el área de logs."""
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')
        self.log_message("Logs limpiados.")

    def log_message(self, message):
        """Registra un mensaje en el área de logs con un timestamp y color."""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_area.configure(state='normal')
        
        # Define tags para colores
        self.log_area.tag_configure("pass_color", foreground="#4CAF50") 
        self.log_area.tag_configure("fail_color", foreground="#F44336") 
        self.log_area.tag_configure("info_color", foreground="#2196F3") # Nuevo color para información
        self.log_area.tag_configure("warn_color", foreground="#FFA500") # Nuevo color para advertencias
        self.log_area.tag_configure("default_color", foreground="white" if ctk.get_appearance_mode() == "Dark" else "black")

        # elif "FAIL" in message or "ERROR" in message or "detenido" in message or "Fallo al conectar" in message:
        if "ERROR" in message or "detenido" in message or "Error al procesar" in message or "Línea omitida." in message or "El procesamiento de" in message or "falló" in message or "Fallo al conectar" in message:
            self.log_area.insert(tk.END, formatted_message, "fail_color")
        # if "PASS" in message or "Registrado correctamente en DB" in message or "reanudado" in message or "iniciado" in message or "Cliente Oracle/MES inicializado" in message:
        elif "PASS" in message or "Registrado correctamente en DB" in message or "reanudado" in message or "iniciado" in message or "Cliente Oracle/MES inicializado" in message:
            self.log_area.insert(tk.END, formatted_message, "pass_color") 
        elif "ADVERTENCIA" in message or "movido" in message or "pausado" in message or "Warning" in message: # Capturar advertencias
            self.log_area.insert(tk.END, formatted_message, "warn_color")
        elif "Info" in message or "Conexión a la base de datos establecida" in message or "Monitoreando" in message or "validada" in message: 
            self.log_area.insert(tk.END, formatted_message, "info_color")
        else:
            self.log_area.insert(tk.END, formatted_message, "default_color")
            
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END) # Auto-scroll al final

    def minimize_to_tray(self):
        """Minimiza la ventana a la bandeja del sistema."""
        self.withdraw()

    def exit_app(self, icon=None, item=None):
        """Detiene el icono de la bandeja y cierra la aplicación."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        if hasattr(self, 'tray_icon') and self.tray_icon: # Asegurarse de que el icono exista
            self.tray_icon.stop()
        self.quit()
        # os._exit(0) # Esto es una salida forzada, generalmente es mejor usar self.quit()

    def update_tray(self):
        """Actualiza el menú del icono de la bandeja."""
        self.tray_icon.menu = self.build_tray_menu()

    def setup_tray_icon(self):
        """Configura el icono de la bandeja del sistema."""
        try:
            icon_image = Image.open(self.resource_path("qst_monitor.ico"))
        except Exception:
            self.log_message("ADVERTENCIA: No se encontró el icono 'qst_monitor.ico'. Usando un icono genérico.")
            icon_image = Image.new("RGB", (64, 64), "blue") # Icono de respaldo
            
        # Asegurarse de que el icono no se inicie dos veces
        if not hasattr(self, 'tray_icon') or self.tray_icon is None:
            self.tray_icon = Icon("QST File Monitor", icon_image, "QST File Monitor", self.build_tray_menu())
            self.tray_icon.run_detached() # Inicia el icono en un hilo separado
        else:
            self.update_tray() # Si ya existe, solo actualiza el menú

    def build_tray_menu(self):
        """Construye el menú para el icono de la bandeja."""
        return Menu(
            MenuItem(
                f"Estado: {'Pausado' if self.monitoring_paused else 'Activo' if self.service_running else 'Detenido'}",
                None,
                enabled=False # No se puede hacer clic
            ),
            MenuItem("Abrir", lambda icon, item: self.deiconify()), # Opción para mostrar la ventana
            MenuItem("Reanudar" if self.monitoring_paused else "Pausar", 
                     lambda icon, item: self.toggle_pause(),
                     enabled=self.service_running), # Habilitar solo si el servicio está corriendo
            MenuItem("Reiniciar Servicio" if self.service_running else "Iniciar Servicio", 
                     lambda icon, item: self.toggle_service()), # Usar toggle_service
            MenuItem("Limpiar Logs", lambda icon, item: self.clear_log()),

            MenuItem("Salir", self.exit_app)
        )
        
    def get_monitoring_path(self):
        """Return the path where the QST files are monitored."""
        year = time.strftime("%Y", time.localtime())
        month = time.strftime("%B", time.localtime())
        day = time.strftime("%d", time.localtime())
        return f"C:/reports/local_qst/{year}/{month}/{day}/"

    def start_monitoring(self):
        """Inicia el monitoreo de archivos en un hilo separado."""
        # Evitar iniciar el observador si ya está activo
        if self.observer and self.observer.is_alive():
            self.log_message("Advertencia: El monitoreo ya está activo.")
            return

        self.log_message("Iniciando monitoreo...")
        
        # Crear un nuevo observador en cada inicio para asegurar un estado limpio
        self.observer = Observer() 

        # Función que se ejecutará en un hilo separado para el monitoreo
        def monitor_thread_func():
            # Intentar obtener la conexión a la base de datos dentro del hilo de monitoreo
            # Esto puede ser mejor si la conexión se refresca o se gestiona aquí.
            # Sin embargo, 'parse_qst' ya obtiene su propia conexión y la cierra.
            # Para evitar múltiples conexiones abiertas, se recomienda que parse_qst
            # sea el único que maneje la apertura y cierre de la conexión para cada archivo.
            # Aquí, solo verificamos si la base de datos es accesible inicialmente.
            
            initial_db_connection = get_connection() # Obtener la conexión inicial
            if initial_db_connection is None:
                self.after(0, lambda: self.show_message_dialog("Error de Conexión", "No se pudo conectar a la base de datos al iniciar el monitoreo. Servicio detenido.", is_error=True))
                self.after(0, self._stop_service) # Detener el servicio a través de la UI thread
                return
            else:
                try:
                    # Verificar si la conexión está viva (ping)
                    cursor = initial_db_connection.cursor()
                    cursor.execute("SELECT 1 FROM DUAL") # Consulta simple para verificar
                    cursor.close()
                    initial_db_connection.close() # Cerrar la conexión inicial
                    self.after(0, lambda: self.show_message_dialog("Conexión Exitosa", "La conexión inicial a la base de datos se estableció correctamente.", is_error=False))
                    self.after(0, lambda: self.log_message("Conexión a la base de datos validada."))
                except Exception as e:
                    self.after(0, lambda: self.show_message_dialog("Error de Conexión", f"La conexión a la base de datos falló la validación inicial: {e}. Servicio detenido.", is_error=True))
                    self.after(0, self._stop_service)
                    return

            # Obtener y crear la ruta de monitoreo
            path_to_monitor = self.get_monitoring_path()
            if not os.path.exists(path_to_monitor):
                try:
                    os.makedirs(path_to_monitor, exist_ok=True)
                    self.after(0, lambda: self.log_message(f"Carpeta de monitoreo creada: {path_to_monitor}"))
                except OSError as e:
                    self.after(0, lambda: self.show_message_dialog("Error de Carpeta", f"No se pudo crear la carpeta de monitoreo: {path_to_monitor}\nDetalle: {e}. Servicio detenido.", is_error=True))
                    self.after(0, self._stop_service)
                    return
            
            self.after(0, lambda: self.log_message(f"Monitoreando la carpeta: {path_to_monitor}"))
            self.after(0, lambda: self.log_message("Esperando nuevos archivos .QST..."))

            # Configurar el manejador de eventos y el observador
            handler = FileMonitor(self.log_message, 
                                  lambda: self.monitoring_paused, 
                                  self.show_message_dialog, # Usar el show_message_dialog general
                                  lambda: self.service_running)
            
            try:
                self.observer.schedule(handler, path_to_monitor, recursive=True)
                self.observer.start()
                while self.service_running: # Mantener el hilo vivo mientras el servicio esté activo
                    time.sleep(1)
            except Exception as e:
                self.after(0, lambda: self.log_message(f"ERROR: Fallo en el hilo de monitoreo: {e}"))
                self.after(0, lambda: self.show_message_dialog("Error de Monitoreo", f"Ocurrió un error en el servicio de monitoreo: {e}. Servicio detenido.", is_error=True))
                self.after(0, self._stop_service) # Asegurar que el servicio se detenga en la UI thread
            finally:
                # Asegurarse de que el observador se detenga cuando el hilo termine
                if self.observer and self.observer.is_alive():
                    self.observer.stop()
                    self.observer.join()
                self.after(0, lambda: self.log_message("Monitoreo detenido."))


        # Iniciar el hilo del monitoreo
        threading.Thread(target=monitor_thread_func, daemon=True).start()

# --- Punto de entrada de la aplicación ---

if __name__ == "__main__":
    lock_path = "qst_monitor.lock"
    if is_running():
        messagebox.showinfo("QST File Monitor", "La aplicación ya se está ejecutando.")
        # No es necesario llamar a bring_to_front() aquí si el messagebox ya notifica al usuario.
        # Si se desea, la lógica para traer la ventana al frente en CustomTkinter es más compleja
        # y generalmente implica guardar una referencia a la ventana principal.
        sys.exit() # Salir si ya está corriendo
    else:
        app = App()
        app.mainloop()
        
        # Limpiar el archivo de bloqueo al salir
        try:
            os.remove(lock_path)
        except FileNotFoundError:
            pass # El archivo ya fue removido o nunca existió