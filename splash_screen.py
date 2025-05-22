import sys
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
from PyQt6.QtCore import Qt
from modern_yoga_app import ModernYogaApp


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YogKalp")
        self.setFixedSize(500, 400)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Center the splash screen
        self.center()
        
        # Set up the layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create a frame to hold the content
        container = QFrame()
        container.setObjectName("splash_container")
        container.setStyleSheet("""
            #splash_container {
                background-color: #FFFFFF;
                border-radius: 20px;
            }
        """)
        
        # Layout for the container
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("c:/Users/sriva/OneDrive/Desktop/YogKalp/YogKalp_logo.jpg")
        logo_label.setPixmap(logo_pixmap.scaled(400, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(logo_label)
        
        # Add loading text
        loading_label = QLabel("Loading...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setFont(QFont("Google Sans", 12))
        container_layout.addWidget(loading_label)
        
        # Add progress bar
        self.progress_bar = QProgressBar()  
        self.progress_bar.setObjectName("splash_progress")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                color: #0dd9cb;
                border-style: none;
                border-radius: 10px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                border-radius: 10px;
                background-color: qlineargradient(spread:pad, x1:0, y1:0.5, x2:1, y2:0.5, stop:0 #f21d1d, stop:1 #2cf029);
            }
        """)
        self.progress_bar.setMaximum(100)
        container_layout.addWidget(self.progress_bar)
        
        layout.addWidget(container)
        self.setLayout(layout)
        
        # Counter for progress
        self.counter = 0
        
        # Timer for progress
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_progress) 
        self.timer.start(35)
        
    def update_progress(self):
        self.counter += 1
        self.progress_bar.setValue(self.counter) 
        
        # When loading is complete
        if self.counter > 100:
            self.timer.stop()
            self.main_app = ModernYogaApp()
            self.main_app.show()
            self.close()
    
    def center(self):
        """Center the window on the screen"""
        screen_geometry = QtWidgets.QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)