import customtkinter as ctk
import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import threading
from .job_widget import JobWidget
from ..core.router import MagicRouter
from ..core.task_queue import TaskQueue
from ..core.conversion_context import FileType
from ..utils.logger import logger
from ..utils.config import Config

# Workaround for CustomTkinter + TkinterDnD2
class TkWrapper(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

# Components
from .sidebar import Sidebar
from .pages.dashboard_page import DashboardPage
from .pages.history_page import HistoryPage
from .pages.settings_page import SettingsPage
from .pages.base_page import BasePage

from ..core.router import MagicRouter
from ..core.task_queue import TaskQueue
from ..core.conversion_context import FileType
from ..utils.logger import logger
from ..utils.config import Config

# Workaround for CustomTkinter + TkinterDnD2
class TkWrapper(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class MainWindow(TkWrapper):
    def __init__(self):
        super().__init__()

        self.title(f"{Config.APP_NAME} v{Config.VERSION}")
        self.geometry("1000x700")
        
        # Configuration
        c_mode = Config.DEFAULT_THEME
        ctk.set_appearance_mode(c_mode)
        ctk.set_default_color_theme(Config.DEFAULT_COLOR_THEME)

        # Core Components
        self.router = MagicRouter()
        self.task_queue = TaskQueue()
        
        # Layout: 2 Columns
        # Col 0: Sidebar (Fixed width)
        # Col 1: Content (Expand)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar
        self.sidebar = Sidebar(self, navigate_callback=self.switch_page)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 2. Page Container
        self.page_container = ctk.CTkFrame(self, fg_color="transparent")
        self.page_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Page Map
        self.pages = {}
        
        # Define Callbacks for Dashboard
        self.dashboard_callbacks = {
            'start_single_task': self.start_single_task,
            'cancel_task': self.cancel_task
        }
        
        # Initialize Pages
        self.pages['dashboard'] = DashboardPage(self.page_container, self.router, self.task_queue, self.dashboard_callbacks)
        self.pages['history'] = HistoryPage(self.page_container)
        self.pages['settings'] = SettingsPage(self.page_container)
        
        # Show Start Page
        self.switch_page('dashboard')
        
    def switch_page(self, page_id):
        # Update Sidebar
        self.sidebar.set_active(page_id)
        
        # Update Content
        # Hide all
        for p in self.pages.values():
            p.pack_forget()
            p.grid_forget() # Just in case
            
        # Show target
        if page_id in self.pages:
            page = self.pages[page_id]
            page.pack(fill="both", expand=True)

    def start_single_task(self, task_id, target_format):
        # Logic is similar to before, but we access widget via DashboardPage
        dash = self.pages['dashboard']
        if task_id not in dash.tasks: return
        
        widget = dash.tasks[task_id]
        if not hasattr(widget, 'file_path'): return
        
        file_path = widget.file_path
        
        # Determine Output Path
        from ..utils.settings_manager import SettingsManager
        from tkinter import messagebox
        settings = SettingsManager()
        
        base, _ = os.path.splitext(file_path)
        base_name_only = os.path.basename(base)
        
        # 0. Check Dashboard Overrides
        custom_folder = dash.entry_output.get().strip()
        
        # 1. Fallback to Settings if empty
        if not custom_folder:
             cat_key = widget.file_type.value
             custom_folder = settings.get_output_path(cat_key)
        
        # 2. Fallback to Source with Prompt if still empty
        if not custom_folder or not os.path.exists(custom_folder):
             # Only prompt if it really isn't set
             if not custom_folder:
                 custom_folder = os.path.dirname(file_path)
             else:
                 # It was set but invalid? Use source.
                 custom_folder = os.path.dirname(file_path)
        
        widget.set_converting()
        
        # Construct output
        new_name = base_name_only + "_converted" + target_format
        output_path = os.path.join(custom_folder, new_name)

        self.task_queue.submit_task(task_id, self.process_file, file_path, output_path, widget.file_type, task_id)

    def process_file(self, input_path, output_path, ftype, task_id):
        # Stats Capture
        size_before = 0
        try:
             size_before = os.path.getsize(input_path)
        except: pass

        # Callback for progress
        def on_progress(prog, status):
            dash = self.pages['dashboard']
            if task_id in dash.tasks:
                widget = dash.tasks[task_id]
                widget.update_progress(prog, status)
                if prog >= 1.0 or status == "Done":
                    # Calculate stats
                    size_after = 0
                    try:
                        if os.path.exists(output_path):
                            size_after = os.path.getsize(output_path)
                    except: pass
                    
                    # Format stats
                    def fmt_size(b):
                        for u in ['B', 'KB', 'MB', 'GB']:
                            if b < 1024.0: return f"{b:.1f}{u}"
                            b /= 1024.0
                        return f"{b:.1f}TB"
                    
                    s_old = fmt_size(size_before)
                    s_new = fmt_size(size_after)
                    pct = 0
                    if size_before > 0:
                        pct = int((1 - (size_after / size_before)) * 100)
                    
                    widget.set_stats(s_old, s_new, f"-{pct}%" if pct > 0 else f"+{abs(pct)}%")
                    widget.set_finished(output_path)

        # ---------------------------------------------------------
        # Engine Execution Logic (Multi-Hop)
        # ---------------------------------------------------------
        from ..core.pathfinder import Pathfinder
        from ..engines.video_engine import VideoEngine
        from ..engines.image_engine import ImageEngine
        from ..engines.doc_engine import DocEngine
        import tempfile
        import shutil

        # 1. Determine Path
        source_ext = os.path.splitext(input_path)[1]
        target_ext = os.path.splitext(output_path)[1]
        
        path_steps = Pathfinder.find_path(source_ext, target_ext)
        
        if not path_steps:
            logger.error(f"No conversion path found from {source_ext} to {target_ext}")
            on_progress(0, "Path Not Found")
            return

        logger.info(f"Execution Path: {path_steps}")
        
        # 2. Execute Steps
        total_steps = len(path_steps)
        current_input = input_path
        temp_files_created = []

        try:
            for i, step in enumerate(path_steps):
                engine_key = step['engine']
                tgt_fmt = "." + step['tgt'].strip('.')
                
                # Determine Output for this step
                step_output = ""
                if i == total_steps - 1:
                    # Final step targets the actual output path
                    step_output = output_path
                else:
                    # Intermediate step targets a temp file
                    fd, tmp = tempfile.mkstemp(suffix=tgt_fmt)
                    os.close(fd)
                    step_output = tmp
                    temp_files_created.append(tmp)

                # Get Engine
                engine = None
                if engine_key == "ffmpeg": engine = VideoEngine()
                elif engine_key == "image_engine": engine = ImageEngine()
                elif engine_key == "doc_engine": engine = DocEngine()
                else:
                    raise ValueError(f"Unknown engine: {engine_key}")

                # Register engine reference just in case we need to cancel (only holds last one)
                dash = self.pages['dashboard']
                if task_id in dash.tasks:
                    dash.tasks[task_id].engine_ref = engine
                
                # Define scaled progress callback
                def step_cb(p, s):
                    # p is 0.0 to 1.0 for this step
                    # global progress = (step_index + p) / total_steps
                    
                    # Normalize p just in case
                    if p < 0: p = 0
                    if p > 1: p = 1
                    
                    current_global = (i + p) / total_steps
                    
                    # If this is the last step and done, ensure we hit 1.0
                    if i == total_steps - 1 and (p >= 1.0 or s == "Done"):
                        current_global = 1.0
                        
                    step_desc = f"Step {i+1}/{total_steps} ({step['tgt'].upper()})"
                    if total_steps == 1: step_desc = s # Simple case
                    
                    on_progress(current_global, step_desc)

                logger.info(f"Running Step {i+1}: {step['src']} -> {step['tgt']} via {engine_key}")
                engine.convert(current_input, step_output, step_cb)

                # Prepare for next step
                current_input = step_output
            
            # 3. Cleanup
            for t in temp_files_created:
                try:
                    if os.path.exists(t): os.remove(t)
                except: pass

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            on_progress(0, "Error")
            # Cleanup on failure
            for t in temp_files_created:
                try:
                    if os.path.exists(t): os.remove(t)
                except: pass

    def cancel_task(self, task_id):
        dash = self.pages['dashboard']
        if task_id in dash.tasks and hasattr(dash.tasks[task_id], 'engine_ref'):
             if dash.tasks[task_id].engine_ref:
                 dash.tasks[task_id].engine_ref.cancel()
        
        self.task_queue.cancel_task(task_id)
        if task_id in dash.tasks:
            dash.tasks[task_id].update_progress(0, "Cancelled")

    def on_closing(self):
        self.task_queue.shutdown()
        self.destroy()

    # --- Dependencies ---
    def check_dependencies(self):
        from ..utils.ffmpeg_downloader import FFmpegDownloader
        from ..utils.pandoc_downloader import PandocDownloader
        
        if not FFmpegDownloader.check_ffmpeg():
            self.show_dependency_dialog("FFmpeg", FFmpegDownloader.download_ffmpeg, "~80MB")
            return
        
        if not PandocDownloader.check_pandoc():
             self.show_dependency_dialog("Pandoc", PandocDownloader.download_pandoc, "~50MB")

    def show_dependency_dialog(self, tool_name, download_func, size_hint):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Missing Dependency: {tool_name}")
        dialog.geometry("450x250")
        dialog.attributes("-topmost", True)
        dialog.transient(self)
        dialog.grab_set()
        
        msg = (
            f"{tool_name} is missing!\n\n"
            f"OmniConvert requires {tool_name} for advanced conversions.\n"
            f"Would you like to download it automatically?\n\n"
            f"({size_hint} download from GitHub)"
        )
        
        lbl = ctk.CTkLabel(dialog, text=msg, wraplength=400, font=("Arial", 14))
        lbl.pack(pady=30)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def on_yes():
            dialog.destroy()
            self.show_download_dialog(tool_name, download_func)
            
        def on_no():
            dialog.destroy()
            if tool_name == "FFmpeg":
                self.after(500, self.check_dependencies) # Try next?
            
        ctk.CTkButton(btn_frame, text="Download", command=on_yes).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Skip", fg_color="transparent", border_width=1, command=on_no).pack(side="right", padx=10)

    def show_download_dialog(self, tool_name, download_func):
        dl_win = ctk.CTkToplevel(self)
        dl_win.title(f"Downloading {tool_name}...")
        dl_win.geometry("300x150")
        dl_win.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(dl_win, text="Initializing...")
        lbl.pack(pady=20)
        
        prog = ctk.CTkProgressBar(dl_win)
        prog.pack(pady=10, padx=20)
        prog.set(0)
        
        def update_ui(pct, status):
             self.after(0, lambda: _update(pct, status))
             
        def _update(pct, status):
             lbl.configure(text=status)
             prog.set(pct/100)
             if pct >= 100:
                 dl_win.after(1000, dl_win.destroy)
                 self.after(1500, self.check_dependencies)

        def run_dl():
            download_func(progress_callback=update_ui)
            
        threading.Thread(target=run_dl, daemon=True).start()

    def open_settings(self):
        self.switch_page('settings')

if __name__ == "__main__":
    app = MainWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    # Schedule check
    app.after(1000, app.check_dependencies)
    app.mainloop()

