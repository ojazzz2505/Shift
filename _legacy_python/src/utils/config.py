import os
import sys
from pathlib import Path

class Config:
    APP_NAME = "OmniConvert"
    VERSION = "1.0.0"
    
    # Paths
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller Bundle
        BASE_DIR = Path(sys.executable).parent
    else:
        # Running as Script
        BASE_DIR = Path(__file__).parent.parent.parent
        
    BIN_DIR = BASE_DIR / "bin"
    FFMPEG_PATH = BIN_DIR / "ffmpeg.exe"
    PANDOC_PATH = BIN_DIR / "pandoc.exe"
    
    # Settings (Defaults)
    DEFAULT_THEME = "Dark"
    DEFAULT_COLOR_THEME = "blue"
