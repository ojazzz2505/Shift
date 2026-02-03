import customtkinter as ctk
from ..utils.logger import logger
from ..core.conversion_context import ConversionContext, FileType

class JobWidget(ctk.CTkFrame):
    def __init__(self, master, file_name, file_type: FileType, task_id, callbacks, **kwargs):
        """
        callbacks: dict with keys 'start', 'cancel', 'remove', 'open_folder'
        """
        # Reference Style: Rounded, Dark Gray Card
        super().__init__(master, fg_color="#2B2B2B", corner_radius=12, height=60, **kwargs)
        self.task_id = task_id
        self.callbacks = callbacks
        self.file_type = file_type
        self.output_path = None
        
        # Grid: [Icon] [Name] [Stats] [Format] [Status] [Actions]
        self.grid_columnconfigure(1, weight=1)
        
        # 1. Icon (Placeholder for now, just a colored square/indicator)
        # Using a soft teal accent for the icon background if possible, or just the indicator
        color = "#2CC985" # Teal (Reference)
        
        self.icon_frame = ctk.CTkFrame(self, width=40, height=40, fg_color="#3A3A3A", corner_radius=8)
        self.icon_frame.grid(row=0, column=0, rowspan=2, padx=12, pady=10)
        
        self.lbl_ext = ctk.CTkLabel(self.icon_frame, text=file_name.split('.')[-1][0:3].upper(), 
                                    font=("Arial", 10, "bold"), text_color="gray80")
        self.lbl_ext.place(relx=0.5, rely=0.5, anchor="center")

        # 2. File Name (Roboto, White)
        self.lbl_name = ctk.CTkLabel(self, text=file_name, font=("Roboto Medium", 13), anchor="w", text_color="white")
        self.lbl_name.grid(row=0, column=1, padx=0, pady=(12, 0), sticky="ew")
        
        # 3. File Size / Stats (Gray, smaller)
        self.lbl_stats = ctk.CTkLabel(self, text="Waiting...", font=("Arial", 11), text_color="gray60", anchor="w")
        self.lbl_stats.grid(row=1, column=1, padx=0, pady=(0, 12), sticky="ew")
        
        # 4. Format Selector (Accent Color?)
        # Keeping it local for now, but style it nicely
        formats = ConversionContext.get_formats_for_type(file_type)
        if not formats: formats = ["N/A"]
        
        self.opt_format = ctk.CTkOptionMenu(self, values=formats, width=85, height=26, 
                                            dynamic_resizing=False, fg_color="#3A3A3A", 
                                            button_color="#444444", text_color="white", font=("Arial", 12),
                                            dropdown_fg_color="#2B2B2B", dropdown_hover_color="#3A3A3A")
        self.opt_format.grid(row=0, column=2, rowspan=2, padx=10, pady=10)
        self.opt_format.set(formats[0])

        # 5. Status Pill (Right)
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=0, column=3, rowspan=2, padx=10)
        
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Ready", font=("Arial", 11), text_color="gray")
        self.lbl_status.pack()
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=80, height=4, progress_color=color)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=3)

        # 6. Actions (X Button)
        self.btn_remove = ctk.CTkButton(self, text="×", width=24, height=24, fg_color="transparent", 
                                        text_color="gray50", hover_color="#C42B1C", font=("Arial", 16), 
                                        command=self.on_remove)
        self.btn_remove.grid(row=0, column=4, rowspan=2, padx=(0, 12))

    def get_target_format(self):
        return self.opt_format.get()
    
    def set_target_format(self, fmt):
        # Allow external controller to set this
        # formatting check? just basic
        if fmt in self.opt_format.cget("values"):
             self.opt_format.set(fmt)
    
    def set_status(self, text, progress=None):
        self.lbl_status.configure(text=text)
        if progress is not None:
             self.progress_bar.set(progress)

    def set_stats(self, old_size_str, new_size_str, percent):
        stats_text = f"{old_size_str} -> {new_size_str}"
        self.lbl_stats.configure(text=stats_text)

    def set_finished(self, output_path=None):
        self.set_status("Done", 1.0)
        self.output_path = output_path
        self.lbl_status.configure(text_color="#2CC985")
        self.icon_frame.configure(fg_color="#2CC985") # Highlight icon on done use Teal
        self.lbl_ext.configure(text_color="white")

    def update_progress(self, progress, status_text):
        self.set_status(status_text, progress)
        # Notify parent dashboard to update global bar
        if hasattr(self.master, 'master') and hasattr(self.master.master, 'update_total_progress'):
             # scroll_tasks -> panel_left -> DashboardPage
             self.master.master.master.update_total_progress()
        # Alternative: Just monkey patch a callback during creation? 
        # Actually, self.master is scrollable frame. master.master is dashboard?
        # Let's try to store a reference or use a callback in __init__
        if 'on_progress' in self.callbacks and self.callbacks['on_progress']:
             self.callbacks['on_progress']()

    # We need to add 'on_progress' to callbacks in DashboardPage before passing here
    # But for now, let's just try to be safe.
    
    def set_converting(self):
        self.opt_format.configure(state="disabled")
        self.btn_remove.configure(state="disabled")
        self.configure(fg_color="#333333", border_width=1, border_color="#2CC985") # "Pop" effect

    def set_finished(self, output_path=None):
        self.set_status("Done", 1.0)
        self.output_path = output_path
        self.lbl_status.configure(text_color="#2CC985")
        self.icon_frame.configure(fg_color="#2CC985") # Highlight icon
        self.lbl_ext.configure(text_color="white")
        self.configure(fg_color="#2B2B2B", border_width=0) # Return to normal depth
        
        # Trigger global update
        if 'on_progress' in self.callbacks and self.callbacks['on_progress']:
             self.callbacks['on_progress']()
