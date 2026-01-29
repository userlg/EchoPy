"""EchoPy - Modern Music Visualizer
Main entry point for the application.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from utils import setup_logging


def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("EchoPy")
    app.setOrganizationName("EchoPy")
    
    # Fix for Windows Taskbar Icon (separates app from python.exe)
    if os.name == 'nt':
        import ctypes
        myappid = 'echopy.visualizer.modern.1.0' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    # Set application icon
    from PySide6.QtGui import QIcon
    from utils import get_resource_path
    icon_path = get_resource_path(os.path.join("resources", "favicon.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
