import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, navigate_callback, current_page="dashboard", **kwargs):
        # Clean Dark Style: No border, just dark bg
        super().__init__(master, width=220, corner_radius=0, fg_color="#181818", **kwargs)
        self.navigate_callback = navigate_callback
        
        # Header / App Name
        self.lbl_title = ctk.CTkLabel(self, text="OmniConvert", font=("Roboto Medium", 22), text_color="#2CC985")
        self.lbl_title.pack(pady=(40, 40), padx=20, anchor="w")
        
        # Navigation Buttons (Clean, capitalized, left aligned)
        self.btn_dashboard = self._create_nav_button("Dashboard", "dashboard")
        self.btn_history = self._create_nav_button("History", "history")
        self.btn_settings = self._create_nav_button("Settings", "settings")

        self.active_btn = None
        self.set_active("dashboard")

        # Version Footer
        from ..utils.config import Config
        self.lbl_version = ctk.CTkLabel(self, text=f"v{Config.VERSION}", text_color="gray30", font=("Arial", 11))
        self.lbl_version.pack(side="bottom", pady=30, padx=20, anchor="w")

    def _create_nav_button(self, text, page_id):
        btn = ctk.CTkButton(
            self, 
            corner_radius=8, 
            height=45, 
            border_spacing=15, 
            text=text,
            fg_color="transparent", 
            text_color="gray70", 
            hover_color="#222222",
            anchor="w", 
            font=("Roboto Medium", 14),
            command=lambda: self.navigate_callback(page_id)
        )
        btn.pack(fill="x", pady=2, padx=10) # Padding for "floating" look
        return btn

    def set_active(self, page_id):
        # Reset all
        for btn in [self.btn_dashboard, self.btn_history, self.btn_settings]:
             btn.configure(fg_color="transparent", text_color="gray70")
        
        # Highlight active
        target = None
        if page_id == "dashboard": target = self.btn_dashboard
        elif page_id == "history": target = self.btn_history
        elif page_id == "settings": target = self.btn_settings
        
        if target:
            # Active state: Tealized background or text? Reference has dark mode. 
            # Let's use a subtle dark gray bg + white text
            target.configure(fg_color="#2B2B2B", text_color="white")
