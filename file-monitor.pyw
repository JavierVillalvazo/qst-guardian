import tkinter as tk
import customtkinter as ctk
from tkinter import scrolledtext, messagebox
import threading
import time
import os
from file_parsing import *
from pystray import Icon, MenuItem, Menu
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuración del tema
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

ERROR_FOLDER = "C:/reports/local_qst/errores/"


class FileMonitor(FileSystemEventHandler):
    def __init__(self, log_callback, is_paused, show_error_dialog):
        self.log_callback = log_callback
        self.is_paused = is_paused
        self.show_error_dialog = show_error_dialog
    
    def show_error_dialog(self, filename, error_folder):
        messagebox.showerror(
        "Error al procesar archivo",
        f"El archivo '{filename}' no pudo ser procesado y fue movido a:\n{error_folder}"
        )
        

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".QST"):
            file_path = event.src_path
            if ERROR_FOLDER not in file_path: # Ignora los archivos que ya están en la carpeta de errores
                #self.log_callback(f"Archivo detectado: {os.path.basename(file_path)}")
                try:
                    parse_qst(file_path, self.log_callback, self.show_error_dialog) 
                    # Error: mostró como archivo procesado correctamente cuando mostroba error al procesar
                    #self.log_callback(f"Procesado correctamente: {os.path.basename(file_path)}")
                except Exception as e:
                    self.log_callback(f"Error inesperado al procesar {os.path.basename(file_path)}: {str(e)}")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QST File Monitor")
        #self.geometry("600x480")
        self.resizable(False, False)
        self.iconbitmap("qst_monitor.ico")
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        #self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.95)
        #self.attributes("-toolwindow", True)
        # Position the window to the bottom-right corner of the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 600
        window_height = 780
        x_position = screen_width - window_width - 10
        y_position = screen_height - window_height - 10
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

    def create_ui(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            self.header_frame,
            text="QST FILE MONITOR",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        self.status_indicator = ctk.CTkLabel(
            self.header_frame,
            text="ACTIVO",
            text_color="#4CAF50",
            font=self.bold_font
        )
        self.status_indicator.pack(side="right", padx=10)

        self.log_frame = ctk.CTkFrame(self.main_frame)
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

        self.control_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.control_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.pause_btn = ctk.CTkButton(
            self.control_frame,
            text="PAUSAR",
            width=100,
            command=self.toggle_pause,
            fg_color="#FFA500",
            hover_color="#CC8400"
        )
        self.pause_btn.pack(side="left", padx=5)

        self.clear_btn = ctk.CTkButton(
            self.control_frame,
            text="LIMPIAR",
            width=100,
            command=self.clear_log,
            fg_color="#607D8B",
            hover_color="#455A64"
        )
        self.clear_btn.pack(side="left", padx=5)

        ctk.CTkLabel(self.control_frame, text="", width=100).pack(side="left", expand=True)

        self.stop_btn = ctk.CTkButton(
            self.control_frame,
            text="DETENER",
            width=100,
            command=self.toggle_service,
            fg_color="#F44336",
            hover_color="#D32F2F"
        )
        self.stop_btn.pack(side="right", padx=5)

    def update_status_indicator(self):
        if not self.service_running:
            text, color = "DETENIDO", "#F44336"
        elif self.monitoring_paused:
            text, color = "PAUSADO", "#FFA500"
        else:
            text, color = "ACTIVO", "#4CAF50"
        self.status_indicator.configure(text=text, text_color=color)

    def toggle_pause(self):
        self.monitoring_paused = not self.monitoring_paused
        self.pause_btn.configure(text="REANUDAR" if self.monitoring_paused else "PAUSAR")
        self.update_status_indicator()
        self.log_message(f"Monitoreo {'pausado' if self.monitoring_paused else 'reanudado'}")
        self.update_tray()

    def toggle_service(self):
        self.service_running = not self.service_running
        self.stop_btn.configure(text="INICIAR" if not self.service_running else "DETENER")
        self.update_status_indicator()
        self.log_message(f"Servicio {'detenido' if not self.service_running else 'iniciado'}")
        self.update_tray()

    def clear_log(self):
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')
        self.log_message("Logs limpiados")

    def log_message(self, message):
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

    def start_monitoring(self):
        def monitor():
            year = time.strftime("%Y", time.localtime())
            month = time.strftime("%B", time.localtime())
            day = time.strftime("%d", time.localtime())
            path = f"C:/reports/local_qst/{year}/{month}/{day}/"
            print(f"Monitoreando: {path}")
            # Verificar si la ruta existe, y crearla si no
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except OSError as e:
                    print(f"Error al crear la carpeta {path}: {e}")
                    return
            handler = FileMonitor(self.log_message, lambda: self.monitoring_paused or not self.service_running, self.show_error_dialog)
            observer = Observer()
            observer.schedule(handler, path , recursive=True)
            # observer.schedule(handler, path="C:/reports/local_qst/", recursive=True)
            observer.start()
            try:
                while True:
                    time.sleep(1)
            finally:
                observer.stop()
                observer.join()

        threading.Thread(target=monitor, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
