import os

import zipfile
import shutil
import subprocess
from pathlib import Path
from ..utils.config import Config
from ..utils.logger import logger

class PandocDownloader:
    # Using a fixed version known to work.
    PANDOC_URL = "https://github.com/jgm/pandoc/releases/download/3.6.1/pandoc-3.6.1-windows-x86_64.zip"
    
    @staticmethod
    def get_pandoc_path():
        # Look in the bin directory
        pandoc_exe = Config.BIN_DIR / "pandoc.exe"
        if pandoc_exe.exists():
            return str(pandoc_exe)
        return None

    @staticmethod
    def check_pandoc():
        path = PandocDownloader.get_pandoc_path()
        if path:
            try:
                # Verify it runs
                subprocess.run([path, "--version"], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                return True
            except:
                logger.warning("Pandoc binary found but failed to run.")
                return False
        return False

    @staticmethod
    def download_pandoc(progress_callback=None):
        """
        Downloads Pandoc zip, extracts pandoc.exe to ./bin/
        progress_callback(percent, status_text)
        """
        try:
            Config.BIN_DIR.mkdir(parents=True, exist_ok=True)
            zip_path = Config.BIN_DIR / "pandoc.zip"
            
            if progress_callback: progress_callback(0, "Connecting to GitHub...")
            
            logger.info(f"Downloading Pandoc from {PandocDownloader.PANDOC_URL}")
            
            import urllib.request
            
            with urllib.request.urlopen(PandocDownloader.PANDOC_URL) as response:
                total_length = int(response.getheader('Content-Length') or 0)
                dl = 0
                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk: break
                        dl += len(chunk)
                        f.write(chunk)
                        if total_length and progress_callback:
                            pct = int((dl / total_length) * 100)
                            progress_callback(pct, f"Downloading Pandoc ({pct}%)")
            
            if progress_callback: progress_callback(100, "Extracting...")
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # The zip contains a folder likely named 'pandoc-3.6.1-windows-x86_64'
                # We need to find pandoc.exe inside
                exe_name = "pandoc.exe"
                target_file = None
                
                for file in zip_ref.namelist():
                    if file.endswith(exe_name):
                        target_file = file
                        break
                
                if target_file:
                    zip_ref.extract(target_file, Config.BIN_DIR)
                    # Move explicit path to ./bin/pandoc.exe
                    extracted_path = Config.BIN_DIR / target_file
                    final_path = Config.BIN_DIR / exe_name
                    shutil.move(str(extracted_path), str(final_path))
                    
                    # Cleanup the 'pandoc-x.x' folder properties
                    # (optional, but clean)
                else:
                    raise Exception("pandoc.exe not found in downloaded archive")

            # Cleanup Zip
            os.remove(zip_path)
            
            # Cleanup source folder if empty or just remains
            # (Logic simplified: we moved the exe, the folder structure remains in bin/pandoc-x.x/, we can ignore or delete)
            
            logger.info("Pandoc installed successfully.")
            if progress_callback: progress_callback(100, "Ready")
            return True

        except Exception as e:
            logger.error(f"Failed to download Pandoc: {e}")
            if progress_callback: progress_callback(0, "Download Failed")
            return False
