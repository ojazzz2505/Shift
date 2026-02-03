import customtkinter as ctk
from .base_page import BasePage

class HistoryPage(BasePage):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.lbl = ctk.CTkLabel(self, text="Conversion History", font=("Roboto Medium", 24))
        self.lbl.pack(pady=(40, 20))
        
        self.lbl_sub = ctk.CTkLabel(self, text="(Coming Soon)", font=("Arial", 16), text_color="gray")
        self.lbl_sub.pack()
