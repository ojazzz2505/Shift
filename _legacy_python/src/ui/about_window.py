import customtkinter as ctk
import webbrowser

class AboutWindow(ctk.CTkToplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title("About OmniConvert")
        self.geometry("500x400")
        
        # App Info
        ctk.CTkLabel(self, text="OmniConvert v1.0", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(self, text="The Universal Offline Converter", font=("Arial", 14)).pack(pady=5)
        
        # Disclaimer
        text = (
            "This software uses code of FFmpeg licensed under the LGPLv2.1 "
            "and its source can be downloaded here:"
        )
        ctk.CTkLabel(self, text=text, wraplength=450).pack(pady=20)
        
        # Link
        link_lbl = ctk.CTkLabel(self, text="https://ffmpeg.org", text_color="blue", cursor="hand2")
        link_lbl.pack(pady=5)
        link_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://ffmpeg.org"))
        
        # Build Info
        ctk.CTkLabel(self, text="Built with Python, CustomTkinter, Pillow, PyMuPDF", font=("Arial", 10)).pack(pady=30)
        
        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=10)
