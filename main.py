import sys
import os
from PyQt6 import QtWidgets
from PyQt6.QtGui import QPalette, QColor
from ui.splash_screen import SplashScreen
from modern_yoga_app import ModernYogaApp
from PyQt6.QtWidgets import QApplication, QProgressBar

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Set palette for a more modern look
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(249, 249, 249))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(32, 33, 36))
    
    app.setPalette(palette)
    
    # Make sure the logo file exists before showing splash screen
    logo_path = "c:/Users/sriva/OneDrive/Desktop/YogKalp/YogKalp_logo.jpg"
    if not os.path.exists(logo_path):
        # If logo doesn't exist, show main app directly
        print("Logo file not found. Starting application without splash screen.")
        main_app = ModernYogaApp()
        main_app.show()
    else:
        # Show splash screen
        splash = SplashScreen()
        splash.show()
    
    sys.exit(app.exec())