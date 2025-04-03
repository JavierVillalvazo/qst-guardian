import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import sys
import os
import pystray
from PIL import Image, ImageDraw
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Clase para manejar el monitoreo de archivos (personaliza según tu proyecto)
class FileMonitor(FileSystemEventHandler):
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".qst"):
            self.log_callback(f"file(s) detected: {os.path.basename(event.src_path)}")

# Interfaz gráfica
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana
        self.title("Fyle System Watcher - Monitoring...")
        self.geometry("500x400")
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Log de actividades
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled')
        self.log_area.pack(expand=True, fill='both')
        
        # Icono en la bandeja del sistema
        self.tray_icon = None
        self.create_tray_icon()
        
        # Iniciar monitoreo en segundo plano
        self.monitor_thread = threading.Thread(target=self.start_monitoring, daemon=True)
        self.monitor_thread.start()

    def log_message(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)  # Auto-scroll

    def start_monitoring(self):
        event_handler = FileMonitor(self.log_message)
        observer = Observer()
        observer.schedule(event_handler, path="C:/Users/J.Villalvazo/OneDrive - Inventronics Global/Desktop/reports/local_qst/", recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            observer.stop()
        observer.join()

    # Configurar el icono en la bandeja
    def create_tray_icon(self):
        from infi.systray import SysTrayIcon
        try:
            image = Image.open("icon.ico")
        except FileNotFoundError:
            image = Image.new('RGB', (64, 64), 'green')

        #menu_options = (("Open", None, app.show_window), ("Exit", None, app.on_quit))
        # Menú de la bandeja
        menu = (
            pystray.MenuItem("Open", self.show_window),
            pystray.MenuItem("Exit", self.exit_app)
        )
        
        self.tray_icon = pystray
        icon = pystray.Icon("qst_monitor", image, "Monitor QST", menu)
        #app.tray_icon = SysTrayIcon("icon.ico", "Monitor QST", menu_options, on_quit=app.on_quit)
        #app.tray_icon.start()
        return  icon

    def show_window(self, *args):
        self.deiconify()
        self.update()

    def minimize_to_tray(self):
        self.withdraw()  # Ocultar ventana

    def exit_app(self, *args):
        self.tray_icon.stop()
        self.destroy()
        os._exit(0)

    def on_quit(app, sysTrayIcon):
        app.destroy()
        os._exit(0)

if __name__ == "__main__":
    app = App()
    app.mainloop()