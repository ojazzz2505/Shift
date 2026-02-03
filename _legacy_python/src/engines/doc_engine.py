import fitz  # PyMuPDF
import os
import subprocess
from .base_engine import BaseEngine
from ..utils.logger import logger
from ..utils.config import Config
from ..utils.pandoc_downloader import PandocDownloader

class DocEngine(BaseEngine):
    def __init__(self):
        self._cancelled = False
        self._process = None

    def convert(self, input_path: str, output_path: str, progress_callback=None):
        self._cancelled = False
        
        _, ext_in = os.path.splitext(input_path)
        _, ext_out = os.path.splitext(output_path)
        ext_in = ext_in.lower()
        ext_out = ext_out.lower()

        # 1. Special Handling for PDF Input (PyMuPDF)
        if ext_in == ".pdf":
            self._convert_pdf_input(input_path, output_path, ext_out, progress_callback)
            return

        # 2. General Doc Conversion (Pandoc)
        self._convert_pandoc(input_path, output_path, progress_callback)

    def _convert_pdf_input(self, input_path, output_path, ext_out, progress_callback):
        """Handle PDF -> Image/Text using PyMuPDF"""
        try:
            doc = fitz.open(input_path)
            total_pages = len(doc)
            
            if ext_out in [".png", ".jpg", ".jpeg", ".bmp"]:
                # Render pages to images. If multi-page, we might need a directory or just render 1st page
                # For this MVP, let's render Page 1 only OR Append numeric suffix? 
                # User expects 1 input -> 1 output usually, but PDF->Images is 1->N.
                # Let's save ONLY the first page for now to adhere to 1-to-1 file mapping in UI.
                
                if progress_callback: progress_callback(10, "Rendering Page 1...")
                page = doc.load_page(0)
                pix = page.get_pixmap()
                pix.save(output_path)
                
            elif ext_out == ".txt":
                # Extract text
                with open(output_path, "w", encoding="utf-8") as f:
                    for i, page in enumerate(doc):
                        if self._cancelled: break
                        text = page.get_text()
                        f.write(text)
                        
                        prog = ((i + 1) / total_pages) * 90
                        if progress_callback: progress_callback(prog, f"Extracting page {i+1}...")
            
            elif ext_out == ".docx" or ext_out == ".html":
                # PyMuPDF can do some layout preservation, but Pandoc is better IF we can extract structure?
                # Actually, PDF -> Word is hard. PyMuPDF doesn't do it natively well.
                # Attempt to use Pandoc if possible? Pandoc reads PDF via `pdftocairo` usually.
                # Let's try basic text extraction -> Pandoc? No, losing layout.
                # Fallback: Just extract text for now if format is widely different.
                logger.warning("PDF -> Word is experimental. Extracting text only.")
                text = ""
                for page in doc: text += page.get_text()
                
                # Write temp md/txt
                import tempfile
                tmp = tempfile.mktemp(suffix=".txt")
                with open(tmp, 'w', encoding='utf-8') as f: f.write(text)
                
                # Now convert text to target using pandoc
                self._convert_pandoc(tmp, output_path, progress_callback)
                os.remove(tmp)

            doc.close()
            if progress_callback: progress_callback(100, "Done")

        except Exception as e:
            logger.error(f"PDF Engine failed: {e}")
            raise e

    def _convert_pandoc(self, input_path, output_path, progress_callback):
        """Use Pandoc for conversion"""
        pandoc_bin = Config.PANDOC_PATH
        
        # Check if installed
        if not os.path.exists(pandoc_bin):
            if not PandocDownloader.check_pandoc():
                logger.error("Pandoc not found. Cannot convert.")
                if progress_callback: progress_callback(0, "Pandoc Missing - Check Logs")
                raise FileNotFoundError("Pandoc is missing. Please restart app to download.")
        
        try:
            cmd = [str(pandoc_bin), input_path, "-o", output_path]
            
            # Special flags for some formats
            if output_path.endswith(".pdf"):
                # Requires pdf engine
                # We can try using wkhtmltopdf if available, or basic
                # For now let defaults run, if it fails, it fails.
                pass

            if progress_callback: progress_callback(20, "Converting with Pandoc...")
            
            # Run
            logger.info(f"Running Pandoc: {' '.join(cmd)}")
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            self._process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )
            
            stdout, stderr = self._process.communicate()
            
            if self._process.returncode != 0:
                err_msg = stderr.decode('utf-8', errors='ignore')
                logger.error(f"Pandoc Error: {err_msg}")
                raise Exception(f"Pandoc failed: {err_msg}")
            
            if progress_callback: progress_callback(100, "Done")

        except Exception as e:
            logger.error(f"Pandoc conversion failed: {e}")
            raise e
        finally:
            self._process = None

    def cancel(self):
        self._cancelled = True
        if self._process:
            try:
                self._process.kill()
            except: pass
