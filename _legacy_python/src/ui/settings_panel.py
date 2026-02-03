import customtkinter as ctk
from customtkinter import filedialog
from ..utils.config import Config
from ..utils.settings_manager import SettingsManager

class SettingsPanel(ctk.CTkToplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title("Settings")
        self.geometry("500x450")
        
        self.settings = SettingsManager()
        
        # Make modal
        self.transient(parent)
        self.grab_set()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Tab View
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_gen = self.tab_view.add("General")
        self.tab_out = self.tab_view.add("Output Locations")
        
        self.setup_general_tab()
        self.setup_output_tab()
        
        # Close Button (Footer)
        self.btn_close = ctk.CTkButton(self, text="Close", command=self.destroy)
        self.btn_close.grid(row=1, column=0, pady=10)

    def setup_general_tab(self):
        tab = self.tab_gen
        tab.grid_columnconfigure(1, weight=1)
        
        # Theme
        ctk.CTkLabel(tab, text="Theme Mode:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.opt_theme = ctk.CTkOptionMenu(tab, values=["System", "Dark", "Light"], command=self.change_theme)
        current_theme = self.settings.get("theme", "Dark")
        if current_theme in ["System", "Dark", "Light"]:
            self.opt_theme.set(current_theme)
        tab.grid(row=0, column=0, padx=10, pady=10) # Wait, grid call on tab is auto by TabView? No, items inside tab
        self.opt_theme.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # FFmpeg Path
        ctk.CTkLabel(tab, text="FFmpeg Path:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        entry = ctk.CTkEntry(tab, width=200)
        entry.insert(0, str(Config.FFMPEG_PATH))
        entry.configure(state="disabled")
        entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        # About
        ctk.CTkButton(tab, text="About OmniConvert", command=self.open_about).grid(row=2, column=0, columnspan=2, pady=20)

    def setup_output_tab(self):
        tab = self.tab_out
        tab.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(tab, text="Save converted files to:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, pady=10)
        
        types = ["Video", "Image", "Document", "Audio"]
        self.path_vars = {} # type -> stringvar (not needed in ctk really, entry.get works)
        self.entries = {}
        
        for i, t in enumerate(types):
            key = t.lower()
            row = i + 1
            
            ctk.CTkLabel(tab, text=f"{t}:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            entry = ctk.CTkEntry(tab, width=200)
            saved_path = self.settings.get_output_path(key)
            if saved_path:
                entry.insert(0, saved_path)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            
            btn = ctk.CTkButton(tab, text="Browse", width=60, command=lambda k=key, e=entry: self.browse_folder(k, e))
            btn.grid(row=row, column=2, padx=5, pady=5)
            
            self.entries[key] = entry

    def browse_folder(self, key, entry_widget):
        path = filedialog.askdirectory(title=f"Select Output Folder for {key.capitalize()}s")
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)
            self.settings.set_output_path(key, path)

    def change_theme(self, new_theme: str):
        ctk.set_appearance_mode(new_theme)
        self.settings.set("theme", new_theme)

    def open_about(self):
        from .about_window import AboutWindow
        AboutWindow(self)

