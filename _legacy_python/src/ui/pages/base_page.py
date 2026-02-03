import customtkinter as ctk

class BasePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
    
    def on_show(self):
        """Called when page is switched to"""
        pass
        
    def on_hide(self):
        """Called when page is switched away from"""
        pass
