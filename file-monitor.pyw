import tkinter as tk
import customtkinter as ctk
from tkinter import scrolledtext, messagebox
import threading
import time
import os
import sys
from file_parsing import *
from pystray import Icon, MenuItem, Menu
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuración del tema
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

def is_running():
    """Checks if an instance of the application is already running.
    Uses a lock file to determine if another instance is active.
    """
    lock_path = "qst_monitor.lock"
    try:
        with open(lock_path, "x") as f:
            f.write(str(os.getpid()))    
        return False
    except FileExistsError:
        return True

# def bring_to_front():
#     """Brings the existing window to the front if it exists."""
#     root = tk.Tk()
#     root.withdraw()  
#     try:
#         for window in root.winfo_children():
#             if window.winfo_toplevel().title() == "QST File Monitor":
#                 window.winfo_toplevel().lift()
#                 break
#     except Exception as e:
#         print(f"Error al intentar traer al frente: {e}")
#     finally:
#         root.destroy()

class FileMonitor(FileSystemEventHandler):
    """EventHandler for detecting file creation events in the monitored directory.

    Attributes:
        log_callback (callable): Function to send log messages to the application's log area.
        is_paused (callable): Function that returns True if monitoring is paused, False otherwise.
        show_error_dialog (callable): Function to display an error dialog to the user.
        is_service_running (callable): Function that returns True if the monitoring service is active, False otherwise.
    """
    
    def __init__(self, log_callback, is_paused, show_error_dialog_callback,is_service_running):
        self.log_callback = log_callback
        self.is_paused = is_paused
        self.show_error_dialog = show_error_dialog_callback
        self.is_service_running = is_service_running # Recibe la función para verificar el estado del servicio
        

    def on_created(self, event):
        if not self.is_service_running() or self.is_paused(): 
            return 
        
        if not event.is_directory and event.src_path.lower().endswith(".qst"): # Convertir a minúsculas para robustez
            file_path = event.src_path
            error_folder_path = get_error_folder()
            
            if error_folder_path.lower() in file_path.lower(): # Comprobar si ya está en una carpeta de errores
                # Si el archivo se detecta en la carpeta de errores, lo ignoramos.
                return
            
            
            if error_folder_path not in file_path: 
                try:
                    processing_successful = parse_qst(file_path, self.log_callback, self.show_error_dialog)
                    filename = os.path.basename(file_path)
                    if processing_successful is not True:
                        error_message = f"El archivo '{filename}' no pudo ser procesado correctamente y fue movido a la carpeta de errores."
                        move_to_error_folder(file_path, self.log_callback, self.show_error_dialog_callback)
                        self.show_message_dialog("Error al procesar archivo", error_message)
                except Exception as e:
                    error_message = f"Ocurrió un error inesperado al procesar el archivo '{os.path.basename(file_path)}':\n{str(e)}\nEl archivo fue movido a:\n{error_folder_path}"
                    move_to_error_folder(file_path, lambda *args: None, self.show_error_dialog_callback)
                    self.show_message_dialog("Error inesperado", error_message)

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

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QST File Monitor")
        self.resizable(False, False)
        self.iconbitmap("qst_monitor.ico")
        self.protocol("WM_DELETE_WINDOW", self.exit_app)
        #self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)
        window_width = 520
        window_height = 500
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x_position = int((screen_width - window_width) / 2)
        y_position = int((screen_height - window_height) / 2)
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        self.service_running = True
        self.monitoring_paused = False

        self.bold_font = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        self.mono_font = ctk.CTkFont(family="Consolas", size=15, weight="normal")

        self.create_ui()
        self.setup_tray_icon()
        self.start_monitoring()
    
    def show_error_dialog(self, filename, error_folder):
        messagebox.showerror(
        "Error al procesar archivo",
        f"El archivo '{filename}' no pudo ser procesado y fue movido a:\n{error_folder}"
        )

    def show_message_dialog(self, title, message):
        messagebox.showerror(title, message)  

    def create_ui(self):
        """Create the main UI components."""
        #self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        #self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))

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

        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        #self.control_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.pause_btn = ctk.CTkButton(
            self.control_frame,
            text="PAUSAR",
            width=100,
            command=self.toggle_pause,
            fg_color="#FFA500",
            hover_color="#CC8400"
        )
        self.pause_btn.pack(side="left", padx=5)

        # self.clear_btn = ctk.CTkButton(
        #     self.header_frame,
        #     text="LIMPIAR LOGS",
        #     width=100,
        #     command=self.clear_log,
        #     fg_color="#607D8B",
        #     hover_color="#455A64",
        #     font=self.bold_font
        # )
        # self.clear_btn.pack(side="left", padx=5)

        ctk.CTkLabel(self.control_frame, text="", width=100).pack(side="left", expand=True)

        self.stop_btn = ctk.CTkButton(
            self.header_frame,
            text="DETENER",
            width=100,
            command=self.toggle_service,
            fg_color="#F44336",
            hover_color="#D32F2F",
            font=self.bold_font
        )
        self.stop_btn.pack(side="left", padx=5)

    def update_status_indicator(self):
        """Update the status indicator based on the current state of the service."""
        if not self.service_running:
            text, color = "DETENIDO", "#F44336"
        elif self.monitoring_paused:
            text, color = "PAUSADO", "#FFA500"
        else:
            text, color = "ACTIVO", "#4CAF50"
        self.status_indicator.configure(text=text, text_color=color)

    def toggle_pause(self):
        """Toggle the monitoring pause state."""
        self.monitoring_paused = not self.monitoring_paused
        self.pause_btn.configure(text="REANUDAR" if self.monitoring_paused else "PAUSAR")
        self.update_status_indicator()
        self.log_message(f"Monitoreo {'pausado' if self.monitoring_paused else 'reanudado'}")
        self.update_tray()

    def toggle_service(self):
        """Toggle the monitoring service on or off."""
        if self.service_running:
            dialog = PasswordDialog(self)
            password = dialog.get_password()
            if password == "Qst2025#":
                self._stop_service()
            elif password is not None:
                self.show_message_dialog("Contraseña Incorrecta", "La contraseña ingresada no es válida.")
        else:
            self._start_service()
                
    def _stop_service(self):
        """Stop the monitoring service and update the UI accordingly."""
        self.service_running = False
        self.stop_btn.configure(text="INICIAR")
        self.stop_btn.configure(text_color="#f3f3f3", fg_color="#4CAF50", hover_color="#388E3C")
        self.update_status_indicator()
        self.log_message("Servicio detenido")
        self.update_tray()
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
    
    def _start_service(self):
        """Start the monitoring service and update the UI accordingly."""
        self.service_running = True
        self.stop_btn.configure(text="DETENER")
        self.stop_btn.configure(text_color="#f3f3f3", fg_color="#F44336", hover_color="#D32F2F")
        self.update_status_indicator()
        self.log_message("Servicio iniciado")
        self.update_tray()
        self.start_monitoring()     

    def clear_log(self):
        """Clear the log area."""
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')
        self.log_message("Logs limpiados")

    def log_message(self, message):
        """Log a message to the log area with a timestamp.
        Args: message (str): The message to log.
        """
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_area.configure(state='normal')
        if "PASS" in message:
            self.log_area.insert(tk.END, formatted_message, "pass_color")
            self.log_area.tag_config("pass_color", foreground="#4CAF50") 
        elif "FAIL" in message or "ERROR" in message or "Advertencia" in message:
            self.log_area.insert(tk.END, formatted_message, "fail_color")
            self.log_area.tag_config("fail_color", foreground="#F44336") 
        elif "MOVIDO" in message:
            self.log_area.insert(tk.END, formatted_message, "moved_color")
            self.log_area.tag_config("moved_color", foreground="#FFA500")
        else:
            self.log_area.insert(tk.END, formatted_message) # Color por defecto        
        #self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

    def minimize_to_tray(self):
        self.withdraw()

    def exit_app(self, icon=None, item=None):
        self.tray_icon.stop()
        self.quit()
        # self.destroy()
        #os._exit(0)

    def update_tray(self):
        self.tray_icon.menu = self.build_tray_menu()

    def setup_tray_icon(self):
        try:
            icon_image = Image.open("qst_monitor.ico")
        except Exception:
            icon_image = Image.new("RGB", (64, 64), "blue")

        self.tray_icon = Icon("QST File Monitor", icon_image, "QST File Monitor", self.build_tray_menu())
        threading.Thread(target=self.tray_icon.run_detached, daemon=True).start()

    def build_tray_menu(self):
        return Menu(
            MenuItem(
                f"Estado: {'Pausado' if self.monitoring_paused else 'Activo' if self.service_running else 'Detenido'}",
                None,
                enabled=False
            ),
            MenuItem("Reanudar" if self.monitoring_paused else "Pausar", lambda icon, item: self.toggle_pause(),
                     enabled=self.service_running),
            MenuItem("Reiniciar" if self.service_running else "Iniciar", lambda icon, item: self.toggle_service()),
            MenuItem("Limpiar Logs", lambda icon, item: self.clear_log()),
            #MenuItem("Cambiar ruta", )
            MenuItem("Salir", self.exit_app)
        )
        
    def get_monitoring_path(self):
        """Return the path where the QST files are monitored."""
        year = time.strftime("%Y", time.localtime())
        month = time.strftime("%B", time.localtime())
        day = time.strftime("%d", time.localtime())
        return f"C:/reports/local_qst/{year}/{month}/{day}/"

    def start_monitoring(self):
        self.log_message("Conectando a la base de datos...")
        self.observer = None  
        
        def monitor():
            db_connection = get_connection()
            if db_connection is None:
                self.after(0, lambda: self.show_message_dialog("Error de conexión", "No se pudo conectar a la base de datos."))
                self._stop_service()
                return
        
            try:
                is_closed = False
                if hasattr(db_connection, 'closed'):
                    is_closed = db_connection.closed
                elif hasattr(db_connection, 'is_closed'):
                    is_closed = db_connection.is_closed()

                if is_closed:
                    self.log_message("La conexión a la base de datos está cerrada.")
                    self._stop_service()
                    return  
                else:
                    # year = time.strftime("%Y", time.localtime())
                    # month = time.strftime("%B", time.localtime())
                    # day = time.strftime("%d", time.localtime())
                    path = self.get_monitoring_path()
                    # Verificar si la ruta existe, y crearla si no
                    if not os.path.exists(path):
                        try:
                            os.makedirs(path, exist_ok=True)
                        except OSError as e:
                            print(f"Error al crear la carpeta {path}: {e}")
                            self.show_message_dialog("Error", f"No se pudo crear la carpeta de monitoreo: {path}")
                            return
                    print(f"Monitoreando: {path}")
                    messagebox.showinfo("Conexión Exitosa", "La conexión a la base de datos se estableció correctamente.", icon="info")
                    self.log_message(f"Conexión a la base de datos establecida ")
                    self.log_message("Cargando configuración............")
                    self.log_message(f"Monitoreando: {path}")
                    self.log_message("Esperando resultados de pruebas...")
                    handler = FileMonitor(self.log_message, lambda: self.monitoring_paused or not self.service_running, self.show_error_dialog, lambda: self.service_running)
                    observer = Observer()
                    observer.schedule(handler, path , recursive=True)
                    observer.start()
                    self.observer = observer  
                    try:
                        while True:
                            time.sleep(1)
                    finally:
                        observer.stop()
                        observer.join()
            except Exception as e:
                self.log_message(f"Error al verificar o iniciar el monitoreo: {e}")
                self.show_message_dialog("Error", f"Ocurrió un error al iniciar el monitoreo: {e}")
                self._stop_service()
        threading.Thread(target=monitor, daemon=True).start()

if __name__ == "__main__":
    if is_running():
        messagebox.showinfo("QST File Monitor", "La aplicación ya se está ejecutando.")
        # bring_to_front()
        sys.exit()
    else:
        app = App()
        app.mainloop()
    try:
        os.remove("qst_monitor.lock")
    except FileNotFoundError:
        pass
