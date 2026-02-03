import customtkinter as ctk
from customtkinter import filedialog
from .base_page import BasePage
from ...utils.config import Config
from ...utils.settings_manager import SettingsManager

class SettingsPage(BasePage):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.settings = SettingsManager()
        
        # Header
        self.lbl_head = ctk.CTkLabel(self, text="Settings", font=("Roboto Medium", 24))
        self.lbl_head.pack(pady=30, padx=40, anchor="w")
        
        # Tabview for Structure
        self.tab_view = ctk.CTkTabview(self, width=600, height=400)
        self.tab_view.pack(padx=40, pady=0, fill="both", expand=True)
        
        self.tab_gen = self.tab_view.add("General")
        self.tab_out = self.tab_view.add("Output Locations")
        
        self.setup_general_tab()
        self.setup_output_tab()

    def setup_general_tab(self):
        tab = self.tab_gen
        
        # Theme
        frame_theme = ctk.CTkFrame(tab, fg_color="transparent")
        frame_theme.pack(pady=20, fill="x", padx=10)
        
        ctk.CTkLabel(frame_theme, text="Theme Mode", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        
        self.opt_theme = ctk.CTkOptionMenu(frame_theme, values=["System", "Dark", "Light"], command=self.change_theme)
        current_theme = self.settings.get("theme", "Dark")
        if current_theme in ["System", "Dark", "Light"]:
            self.opt_theme.set(current_theme)
        self.opt_theme.pack(side="right", padx=10)
        
        # FFmpeg Path
        frame_ffmpeg = ctk.CTkFrame(tab, fg_color="transparent")
        frame_ffmpeg.pack(pady=20, fill="x", padx=10)
        
        ctk.CTkLabel(frame_ffmpeg, text="FFmpeg Path", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        entry = ctk.CTkEntry(frame_ffmpeg, width=250)
        entry.insert(0, str(Config.FFMPEG_PATH))
        entry.configure(state="disabled")
        entry.pack(side="right", padx=10)
        
        # About Button
        ctk.CTkButton(tab, text="About OmniConvert", width=200, command=self.open_about).pack(pady=40)

    def setup_output_tab(self):
        tab = self.tab_out
        
        ctk.CTkLabel(tab, text="Default Output Directories", font=("Arial", 16, "bold")).pack(pady=(20, 10), anchor="w", padx=10)
        
        types = ["Video", "Image", "Document", "Audio"]
        self.entries = {}
        
        for t in types:
            key = t.lower()
            frame = ctk.CTkFrame(tab, fg_color="transparent")
            frame.pack(pady=10, fill="x", padx=10)
            
            ctk.CTkLabel(frame, text=f"{t}:", width=80, anchor="w").pack(side="left", padx=5)
            
            entry = ctk.CTkEntry(frame)
            saved_path = self.settings.get_output_path(key)
            if saved_path: entry.insert(0, saved_path)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            
            btn = ctk.CTkButton(frame, text="Browse", width=60, command=lambda k=key, e=entry: self.browse_folder(k, e))
            btn.pack(side="right", padx=5)
            
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
        from ..about_window import AboutWindow
        AboutWindow(self.master) # Toplevel
