import customtkinter as ctk
from ..utils.logger import logger

class ProgressWidget(ctk.CTkFrame):
    def __init__(self, master, file_name, task_id, cancel_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.task_id = task_id
        self.cancel_callback = cancel_callback
        
        self.grid_columnconfigure(1, weight=1)
        
        # Icon/Label
        self.lbl_name = ctk.CTkLabel(self, text=file_name, anchor="w", width=150)
        self.lbl_name.grid(row=0, column=0, padx=10, pady=5)
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Status Label call
        self.lbl_status = ctk.CTkLabel(self, text="Queued", width=80)
        self.lbl_status.grid(row=0, column=2, padx=10, pady=5)
        
        # Cancel Button
        self.btn_cancel = ctk.CTkButton(self, text="X", width=30, fg_color="red", command=self.on_cancel)
        self.btn_cancel.grid(row=0, column=3, padx=10, pady=5)
        
    def update_progress(self, progress: float, status_text: str = None):
        if status_text:
            self.lbl_status.configure(text=status_text)
        self.progress_bar.set(progress)
        
    def on_cancel(self):
        logger.info(f"Cancel requested for task {self.task_id}")
        self.cancel_callback(self.task_id)
        self.lbl_status.configure(text="Cancelled")
