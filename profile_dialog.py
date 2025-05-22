import json
import os
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap, QGuiApplication
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QLineEdit, QPushButton, QMessageBox, QComboBox, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
# from modern_yoga_app import ModernYogaApp

class UserProfileDialog(QWidget):
    profile_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.setWindowTitle("YogKalp - User Profile")
        self.setMinimumSize(600, 600)
        self.user_data = user_data or {}
        self.setup_ui()
        self.center_on_screen()
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
    
    def center_on_screen(self):
        """Center teh dialog on the screen"""
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Your Profile")
        header.setFont(QFont("Google Sans", 24, QFont.Weight.Medium))
        layout.addWidget(header)
        
        # Form layout for user details
        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_card.setStyleSheet("""
            #formCard {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        # Apply card shadow effect
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        form_card.setGraphicsEffect(shadow)
        
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(16)
        
        # Basic Information Section
        basic_info = QLabel("Basic Information")
        basic_info.setFont(QFont("Google Sans", 16, QFont.Weight.Medium))
        form_layout.addWidget(basic_info)
        
        # Name
        name_layout = QVBoxLayout()
        name_label = QLabel("Full Name")
        name_label.setFont(QFont("Google Sans", 12))
        self.name_input = QLineEdit()
        self.name_input.setMinimumHeight(40)
        self.name_input.setPlaceholderText("Enter your full name")
        self.name_input.setText(self.user_data.get("name", ""))
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        form_layout.addLayout(name_layout)
        
        # Age and Gender in one row
        age_gender_layout = QHBoxLayout()
        
        # Age
        age_layout = QVBoxLayout()
        age_label = QLabel("Age")
        age_label.setFont(QFont("Google Sans", 12))
        self.age_input = QLineEdit()
        self.age_input.setMinimumHeight(40)
        self.age_input.setPlaceholderText("Years")
        self.age_input.setText(str(self.user_data.get("age", "")))
        self.age_input.setValidator(QtGui.QIntValidator(1, 120))
        age_layout.addWidget(age_label)
        age_layout.addWidget(self.age_input)
        age_gender_layout.addLayout(age_layout)
        
        # Gender
        gender_layout = QVBoxLayout()
        gender_label = QLabel("Gender")
        gender_label.setFont(QFont("Google Sans", 12))
        self.gender_input = QtWidgets.QComboBox()
        self.gender_input.setMinimumHeight(40)
        self.gender_input.addItems(["Select", "Male", "Female", "Other"])
        gender_index = self.gender_input.findText(self.user_data.get("gender", "Select"))
        self.gender_input.setCurrentIndex(gender_index if gender_index >= 0 else 0)
        gender_layout.addWidget(gender_label)
        gender_layout.addWidget(self.gender_input)
        age_gender_layout.addLayout(gender_layout)
        
        form_layout.addLayout(age_gender_layout)
        
        # Health Information Section
        health_info = QLabel("Health Information")
        health_info.setFont(QFont("Google Sans", 16, QFont.Weight.Medium))
        form_layout.addWidget(health_info)
        
        # Height and Weight in one row
        hw_layout = QHBoxLayout()
        
        # Height
        height_layout = QVBoxLayout()
        height_label = QLabel("Height")
        height_label.setFont(QFont("Google Sans", 12))
        self.height_input = QLineEdit()
        self.height_input.setMinimumHeight(40)
        self.height_input.setPlaceholderText("cm")
        self.height_input.setText(str(self.user_data.get("height", "")))
        self.height_input.setValidator(QtGui.QDoubleValidator(50, 250, 1))
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_input)
        hw_layout.addLayout(height_layout)
        
        # Weight
        weight_layout = QVBoxLayout()
        weight_label = QLabel("Weight")
        weight_label.setFont(QFont("Google Sans", 12))
        self.weight_input = QLineEdit()
        self.weight_input.setMinimumHeight(40)
        self.weight_input.setPlaceholderText("kg")
        self.weight_input.setText(str(self.user_data.get("weight", "")))
        self.weight_input.setValidator(QtGui.QDoubleValidator(1, 500, 1))
        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self.weight_input)
        hw_layout.addLayout(weight_layout)
        
        form_layout.addLayout(hw_layout)
        
        # Fitness Goals
        goals_layout = QVBoxLayout()
        goals_label = QLabel("Fitness Goals")
        goals_label.setFont(QFont("Google Sans", 12))
        self.goals_input = QLineEdit()
        self.goals_input.setMinimumHeight(40)
        self.goals_input.setPlaceholderText("e.g., Weight loss, Flexibility, Stress reduction")
        self.goals_input.setText(self.user_data.get("goals", ""))
        goals_layout.addWidget(goals_label)
        goals_layout.addWidget(self.goals_input)
        form_layout.addLayout(goals_layout)
        
        layout.addWidget(form_card)
        buttons_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(50)
        self.cancel_btn.setFont(QFont("Google Sans", 14))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #DADCE0;
                color: #202124;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        self.cancel_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.cancel_btn)
        
        # Save button
        self.save_btn = QPushButton("Save Profile")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setFont(QFont("Google Sans", 14))
        self.save_btn.clicked.connect(self.save_profile)
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)
    
    def save_profile(self):
        # Validate inputs
        if not self.name_input.text():
            QMessageBox.warning(self, "Incomplete Profile", "Please enter your name.")
            return
            
        if self.gender_input.currentText() == "Select":
            QMessageBox.warning(self, "Incomplete Profile", "Please select your gender.")
            return
            
        # Collect user data
        user_data = {
            "name": self.name_input.text(),
            "age": self.age_input.text(),
            "gender": self.gender_input.currentText(),
            "height": self.height_input.text(),
            "weight": self.weight_input.text(),
            "goals": self.goals_input.text()
        }
        
        # Save to file
        try:
            os.makedirs("user_data", exist_ok=True)
            with open("user_data/profile.json", "w") as f:
                json.dump(user_data, f)
            
            # Emit signal that profile was updated
            self.profile_updated.emit(user_data)
            
            QMessageBox.information(self, "Profile Saved", "Your profile has been saved successfully!")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save profile: {str(e)}")
