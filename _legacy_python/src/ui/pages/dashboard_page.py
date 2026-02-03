import customtkinter as ctk
from tkinterdnd2 import DND_FILES
from .base_page import BasePage
from ..job_widget import JobWidget
from ...core.conversion_context import FileType
from ...utils.logger import logger
import os

class DashboardPage(BasePage):
    def __init__(self, master, router, task_queue, app_callbacks, **kwargs):
        super().__init__(master, **kwargs)
        self.router = router
        self.task_queue = task_queue
        self.app_callbacks = app_callbacks 
        
        self.tasks = {} # task_id -> widget
        
        # Grid Layout: 2 Columns
        # Column 0: Queue (Weight 3)
        # Column 1: Controls (Weight 1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1) # Main Content
        self.grid_rowconfigure(1, weight=0) # Global Progress Bar

        # ==========================
        # LEFT PANEL (Queue & Drop) - Transparent/Base Level
        # ==========================
        self.panel_left = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_left.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.panel_left.grid_rowconfigure(1, weight=1) 
        self.panel_left.grid_columnconfigure(0, weight=1)

        # 1. Drop Zone (Recessed Depth)
        # Use a darker color + border to emulate "sink"
        self.frame_drop = ctk.CTkFrame(self.panel_left, height=160, corner_radius=15, 
                                       fg_color="#141414", border_width=2, border_color="#222222")
        self.frame_drop.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        # Content
        self.lbl_icon = ctk.CTkLabel(self.frame_drop, text="☁", font=("Arial", 48), text_color="#333333")
        self.lbl_icon.place(relx=0.5, rely=0.35, anchor="center")
        
        self.lbl_main = ctk.CTkLabel(self.frame_drop, text="Drag & Drop Files Here", font=("Roboto Medium", 18), text_color="gray60")
        self.lbl_main.place(relx=0.5, rely=0.65, anchor="center")
        
        self.frame_drop.drop_target_register(DND_FILES)
        self.frame_drop.dnd_bind('<<Drop>>', self.drop_files)
        
        self.frame_drop.bind("<Button-1>", self.browse_files)
        self.lbl_main.bind("<Button-1>", self.browse_files)
        self.lbl_icon.bind("<Button-1>", self.browse_files)
        
        # 2. Task Scroll Area
        self.scroll_tasks = ctk.CTkScrollableFrame(self.panel_left, fg_color="transparent")
        self.scroll_tasks.grid(row=1, column=0, sticky="nsew")

        # ==========================
        # RIGHT PANEL (Controls) - Elevated Level
        # ==========================
        # Lighter background + Shadow/Border effect
        self.panel_right = ctk.CTkFrame(self, fg_color="#202020", corner_radius=0, border_width=0)
        self.panel_right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=0, pady=0)
        
        # Add a subtle left border using a separator line or frame?
        # Just use a frame on the left edge
        self.sep = ctk.CTkFrame(self.panel_right, width=1, fg_color="#333333")
        self.sep.pack(side="left", fill="y")
        
        # Controls Container
        self.frame_ctrl = ctk.CTkFrame(self.panel_right, fg_color="transparent")
        self.frame_ctrl.pack(fill="both", expand=True, padx=20, pady=40)
        
        # Control Widgets...
        ctk.CTkLabel(self.frame_ctrl, text="Global Settings", font=("Roboto Medium", 18), text_color="white", anchor="w").pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.frame_ctrl, text="Target Format", font=("Arial", 12, "bold"), text_color="gray60", anchor="w").pack(fill="x")
        self.global_format_var = ctk.StringVar(value="Select...")
        self.opt_global_format = ctk.CTkOptionMenu(self.frame_ctrl, values=["MP4", "MP3", "PNG", "PDF", "DOCX"], 
                                                   variable=self.global_format_var, command=self.on_global_format_change,
                                                   fg_color="#2B2B2B", button_color="#333333", text_color="white",
                                                   dropdown_fg_color="#2B2B2B", dropdown_hover_color="#3A3A3A")
        self.opt_global_format.pack(fill="x", pady=(5, 20))
        
        ctk.CTkLabel(self.frame_ctrl, text="Output Folder", font=("Arial", 12, "bold"), text_color="gray60", anchor="w").pack(fill="x")
        self.entry_output = ctk.CTkEntry(self.frame_ctrl, placeholder_text="Default (Source)", fg_color="#2B2B2B", border_color="#333333", text_color="gray90")
        self.entry_output.pack(fill="x", pady=(5, 5))
        
        self.btn_browse_out = ctk.CTkButton(self.frame_ctrl, text="Select Folder", fg_color="transparent", border_width=1, border_color="gray40", 
                                            text_color="gray80", hover_color="#2B2B2B", command=self.browse_output_folder)
        self.btn_browse_out.pack(fill="x", pady=(0, 20))
        
        # Convert All Button
        self.btn_convert_all = ctk.CTkButton(self.frame_ctrl, text="START CONVERSION", height=50, corner_radius=8,
                                             fg_color="#2CC985", hover_color="#25A970", text_color="white", 
                                             font=("Roboto Medium", 14), command=self.start_all_tasks)
        self.btn_convert_all.pack(fill="x", pady=20, side="bottom")

        # ==========================
        # BOTTOM BAR (Global Progress)
        # ==========================
        self.frame_bottom = ctk.CTkFrame(self, height=30, fg_color="#121212", corner_radius=0)
        self.frame_bottom.grid(row=1, column=0, sticky="ew")
        
        self.prog_global = ctk.CTkProgressBar(self.frame_bottom, height=4, progress_color="#2CC985", border_width=0)
        self.prog_global.pack(fill="x", padx=0, pady=0)
        self.prog_global.set(0)
        
        self.lbl_global_status = ctk.CTkLabel(self.frame_bottom, text="", font=("Arial", 11), text_color="gray60")
        self.lbl_global_status.pack(side="left", padx=10, pady=2)

    def browse_files(self, event=None):
        from customtkinter import filedialog
        files = filedialog.askopenfilenames()
        if files:
            for f in files: self.add_task(f)

    def drop_files(self, event):
        files = self.parse_drop_files(event.data)
        for f in files: self.add_task(f)

    def parse_drop_files(self, data):
        if data.startswith('{') and data.endswith('}'):
             import re
             paths = re.findall(r'\{.*?\}|\S+', data)
             return [p.strip('{}') for p in paths]
        return data.split()

    def add_task(self, file_path):
        task_id = str(len(self.tasks) + 1)
        while task_id in self.tasks: task_id += "_1"
        
        file_name = os.path.basename(file_path)
        ftype = self.router.detect_file_type(file_path)
        
        if ftype == FileType.UNKNOWN:
             logger.warning(f"Unknown: {file_name}")
             return

        cbs = {
            'start': self.app_callbacks['start_single_task'],
            'remove': self.remove_task,
            'cancel': self.app_callbacks['cancel_task'],
            'open_folder': None, 
            'on_progress': self.update_total_progress # Explicit callback
        }
        
        widget = JobWidget(self.scroll_tasks, file_name, ftype, task_id, cbs)
        widget.pack(fill="x", padx=0, pady=6) # Increased spacing for cards
        widget.file_path = file_path 
        
        self.tasks[task_id] = widget
        self.update_total_progress() # Initial update

    def remove_task(self, task_id):
        if task_id in self.tasks:
            self.app_callbacks['cancel_task'](task_id)
            w = self.tasks.pop(task_id)
            w.destroy()
            self.update_total_progress()

    def browse_output_folder(self):
        from customtkinter import filedialog
        path = filedialog.askdirectory()
        if path:
            self.entry_output.delete(0, "end")
            self.entry_output.insert(0, path)

    def on_global_format_change(self, choice):
        tgt = choice.strip()
        if not tgt.startswith('.'): tgt = '.' + tgt
        tgt = tgt.lower()
        
        for tid, widget in self.tasks.items():
            if widget.opt_format.cget("state") != "disabled":
                 vals = widget.opt_format.cget("values")
                 if vals and tgt in vals:
                     widget.set_target_format(tgt) 

    def start_all_tasks(self):
        for tid, widget in self.tasks.items():
            state = widget.opt_format.cget("state")
            if state != "disabled": 
                 fmt = widget.get_target_format()
                 self.app_callbacks['start_single_task'](tid, fmt)
                 
    def update_total_progress(self):
        # Calculate active progress
        total_p = 0
        active_count = 0
        
        for widget in self.tasks.values():
            # Check if task is running/done
            # We can infer state from progress value or status text
            # Better to assume all tasks contribute to "Queue Progress" if they are active?
            # Or just show "Busy" ones.
            # User wants: "if nothing to convert, don't add small progress"
            
            # Let's simple check if progress > 0
            p = widget.progress_bar.get()
            if p > 0 or widget.lbl_status.cget("text") == "Done":
                total_p += p
                active_count += 1
        
        if active_count > 0:
            avg = total_p / len(self.tasks) # Average of ALL tasks or just active? 
            # Usually users want "Batch Progress". If 1/5 is done, bar is 20%.
            avg = total_p / len(self.tasks)
            self.prog_global.set(avg)
            self.lbl_global_status.configure(text=f"Progress: {int(avg*100)}%")
        else:
            self.prog_global.set(0)
            self.lbl_global_status.configure(text=f"{len(self.tasks)} files in queue")
