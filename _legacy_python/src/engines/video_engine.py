import subprocess
import re
import threading
import os
import sys
from .base_engine import BaseEngine
from ..utils.config import Config
from ..utils.logger import logger

class VideoEngine(BaseEngine):
    def __init__(self):
        self.process = None
        self._cancelled = False

    def get_duration(self, input_path):
        """Returns duration in seconds using ffmpeg/ffprobe logic"""
        # We can use ffmpeg -i and parse duration from stderr
        cmd = [str(Config.FFMPEG_PATH), "-i", input_path]
        try:
            result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            # Duration: 00:00:10.50, ...
            match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", result.stderr)
            if match:
                h, m, s = match.groups()
                return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception as e:
            logger.error(f"Error getting duration: {e}")
        return 0

    def parse_time(self, time_str):
        # time=00:00:05.20
        try:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
        except:
            return 0

    def convert(self, input_path: str, output_path: str, progress_callback=None):
        self._cancelled = False
        
        # 0. Check FFmpeg Exists
        if not os.path.exists(Config.FFMPEG_PATH):
             # Fallback to system path provided? OR Error out
             # For now, if not in bin, assume system path if we implement lookup
             # But Config.FFMPEG_PATH is hardcoded to bin/ffmpeg.exe
             # If strictly following "hub & spoke", we might need a dynamic lookup in Config or here
             if "ffmpeg" not in str(Config.FFMPEG_PATH) and shutil.which("ffmpeg"):
                 ffmpeg_cmd = "ffmpeg"
             elif os.path.exists(Config.FFMPEG_PATH):
                 ffmpeg_cmd = str(Config.FFMPEG_PATH)
             else:
                 # Check system path
                 import shutil
                 if shutil.which("ffmpeg"):
                     ffmpeg_cmd = "ffmpeg"
                 else:
                     raise FileNotFoundError("FFmpeg executable not found.")
        else:
             ffmpeg_cmd = str(Config.FFMPEG_PATH)

        duration = self.get_duration(input_path)
        if duration == 0:
            duration = 1 # Prevent divide by zero

        # 1. Start Process
        cmd = [ffmpeg_cmd, "-i", input_path, "-y", output_path]
        
        creation_flags = 0
        if sys.platform == 'win32':
            creation_flags = subprocess.CREATE_NO_WINDOW
            
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creation_flags,
            encoding='utf-8', 
            errors='replace'
        )

        # 2. Read Progress
        while True:
            if self._cancelled:
                self.process.terminate()
                break
                
            line = self.process.stderr.readline()
            if not line and self.process.poll() is not None:
                break
            
            if line:
                # Parse time=...
                # frame=  155 fps=0.0 q=-1.0 size=       0kB time=00:00:05.16 bitrate=   0.1kbits/s speed=10.3x
                match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
                if match and progress_callback:
                    current_time = self.parse_time(match.group(1))
                    percent = (current_time / duration) * 100
                    # Clamp
                    percent = min(max(percent, 0), 99)
                    progress_callback(percent, f"Converting... {int(percent)}%")
        
        if self._cancelled:
            if progress_callback: progress_callback(0, "Cancelled")
            return

        if self.process.returncode == 0:
            if progress_callback: progress_callback(100, "Done")
        else:
            raise Exception("FFmpeg conversion failed.")

    def cancel(self):
        self._cancelled = True
        if self.process:
            self.process.terminate()
