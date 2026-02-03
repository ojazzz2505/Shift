import os
import shutil
import urllib.request
import zipfile
import threading
from tkinter import messagebox
from ..utils.config import Config
from ..utils.logger import logger

class FFmpegDownloader:
    """
    Helpers to check for FFmpeg and download it if missing.
    """
    
    @staticmethod
    def check_ffmpeg():
        """Returns True if ffmpeg is found in bin or path."""
        if os.path.exists(Config.FFMPEG_PATH):
            return True
        if shutil.which("ffmpeg"):
            return True
        return False
        
    @staticmethod
    def download_ffmpeg(progress_callback=None, completion_callback=None):
        """
        Downloads a static build of FFmpeg for Windows.
        This is a blocking call if run on main thread, so run in thread.
        """
        # URL for Windows build (e.g., from gyan.dev)
    @staticmethod
    def download_ffmpeg(progress_callback=None, completion_callback=None):
        """
        Downloads a static build of FFmpeg for Windows.
        This is a blocking call if run on main thread, so run in thread.
        """
        # Switching to GitHub release mirror for better speed/reliability
        url = "https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip"
        
        dest_zip = os.path.join(Config.BASE_DIR, "ffmpeg_temp.zip")
        extract_dir = os.path.join(Config.BASE_DIR, "ffmpeg_temp_extract")
        
        try:
            # 1. Cleanup previous attempts
            if os.path.exists(dest_zip):
                os.remove(dest_zip)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
            
            if not os.path.exists(Config.BIN_DIR):
                os.makedirs(Config.BIN_DIR)

            logger.info(f"Downloading FFmpeg from {url}")
            if progress_callback: progress_callback(0, "Downloading FFmpeg (GitHub)...")
            
            # Streaming download to track progress
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                chunk_size = 1024*1024 # 1MB
                
                with open(dest_zip, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        downloaded += len(chunk)
                        f.write(chunk)
                        if progress_callback and total_size > 0:
                            pct = int(downloaded / total_size * 50) 
                            progress_callback(pct, "Downloading...")
            
            if progress_callback: progress_callback(50, "Extracting...")
            
            with zipfile.ZipFile(dest_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            # Move ffmpeg.exe to bin
            found = False
            for root, dirs, files in os.walk(extract_dir):
                if "ffmpeg.exe" in files:
                    src = os.path.join(root, "ffmpeg.exe")
                    
                    # Ensure destination is clear
                    if os.path.exists(Config.FFMPEG_PATH):
                        try:
                            os.remove(Config.FFMPEG_PATH)
                        except OSError:
                            pass # Might be locked, copy will fail typically usage error
                            
                    # Use copy + remove instead of move to avoid cross-device errors or weird locks
                    # Add a tiny sleep to let AV release the extracted file
                    import time
                    time.sleep(1.0) 
                    
                    shutil.copy2(src, Config.FFMPEG_PATH)
                    found = True
                    break
            
            # Cleanup
            try:
                os.remove(dest_zip)
                shutil.rmtree(extract_dir, ignore_errors=True)
            except:
                pass # Non-critical
            
            if found:
                if progress_callback: progress_callback(100, "FFmpeg Ready!")
                if completion_callback: completion_callback(True)
            else:
                if progress_callback: progress_callback(0, "Extraction Failed (exe not found)")
                if completion_callback: completion_callback(False)

        except Exception as e:
            logger.error(f"Download failed: {e}")
            if progress_callback: progress_callback(0, f"Error: {e}")
            if completion_callback: completion_callback(False)
