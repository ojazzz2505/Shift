import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.ui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    # Schedule startup check
    app.after(1000, app.check_dependencies)
    app.mainloop()
