from PIL import Image
import os
from .base_engine import BaseEngine
from ..utils.logger import logger

class ImageEngine(BaseEngine):
    def __init__(self):
        self._cancelled = False

    def convert(self, input_path: str, output_path: str, progress_callback=None):
        self._cancelled = False
        try:
            if progress_callback:
                progress_callback(10, "Opening image...")
                
            img = Image.open(input_path)
            
            # Simulate steps if needed, but Pillow save is usually blocking and fast for single image
            # For massive images, we might want to check cancellation, but Pillow is C-based
            if self._cancelled:
                return

            if progress_callback:
                progress_callback(50, "Converting...")
                
            # Basic conversion logic (handle RGBA -> RGB for JPEG)
            if output_path.lower().endswith(".jpg") or output_path.lower().endswith(".jpeg"):
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

            img.save(output_path)
            
            if progress_callback:
                progress_callback(100, "Done")
                
        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
            raise e

    def cancel(self):
        self._cancelled = True
