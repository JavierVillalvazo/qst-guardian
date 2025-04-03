import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import os
import pystray
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Clase para monitoreo de archivos
class FileMonitor(FileSystemEventHandler):
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".qst"):
            self.log_callback(f"file(s) detected: {os.path.basename(event.src_path)}")

# Aplicación principal
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Configuración inicial
        self.title("File System Watcher")
        self.geometry("500x400")
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Área de logs
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled')
        self.log_area.pack(expand=True, fill='both')
        
        # Configurar ícono de bandeja
        self.tray_icon = None
        self.setup_tray_icon()
        
        # Iniciar monitoreo
        self.start_monitoring()

    def log_message(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

    def start_monitoring(self):
        def monitor():
            event_handler = FileMonitor(self.log_message)
            observer = Observer()
            observer.schedule(
                event_handler,
                path=os.path.expanduser("C:/Users/J.Villalvazo/OneDrive - Inventronics Global/Desktop/reports/local_qst/"),
                recursive=True
            )
            observer.start()
            try:
                while True:
                    time.sleep(1)
            finally:
                observer.stop()
                observer.join()
        
        threading.Thread(target=monitor, daemon=True).start()

    def setup_tray_icon(self):
        # Cargar ícono o crear uno por defecto
        try:
            image = Image.open("icon.ico")
        except FileNotFoundError:
            # Crear ícono temporal si no se encuentra el archivo
            image = Image.new('RGB', (64, 64), 'blue')
        
        # Menú de la bandeja
        menu = (
            pystray.MenuItem('Abrir', self.show_app),
            pystray.MenuItem('Salir', self.exit_app)
        )
        
        # Configurar ícono
        self.tray_icon = pystray.Icon(
            "file_monitor",
            image,
            "File Monitor",
            menu
        )
        
        # Iniciar en hilo separado
        threading.Thread(
            target=self.tray_icon.run,
            daemon=True
        ).start()

    def show_app(self):
        self.deiconify()
        self.update()

    def minimize_to_tray(self):
        self.withdraw()

    def exit_app(self):
        self.tray_icon.stop()
        self.destroy()
        os._exit(0)

if __name__ == "__main__":
    app = App()
    app.mainloop()