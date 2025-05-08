import tkinter as tk
import customtkinter as ctk

class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Contraseña Requerida")
        self.geometry("300x150")
        self.resizable(False, False)
        self.grab_set()  # Hace que esta ventana sea modal
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
        self.wait_window()  # Espera hasta que la ventana se cierre
        return self.result