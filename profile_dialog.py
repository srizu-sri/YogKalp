import json
import os
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap, QGuiApplication
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QLineEdit, QPushButton, QMessageBox, QComboBox, QHBoxLayout, QTextEdit, QGridLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from .ui_styles import StyleSheet, TailwindColors

class UserProfileDialog(QWidget):
    profile_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.setWindowTitle("YogKalp - User Profile")
        self.setMinimumSize(800, 600)
        self.user_data = user_data or {}
        self.setup_ui()
        self.center_on_screen()
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
    
    def center_on_screen(self):
        """Center the dialog on the screen"""
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Header with back button
        header_layout = QHBoxLayout()
        header = QLabel("Your Profile")
        header.setFont(StyleSheet.get_font(24, "Bold"))
        header_layout.addWidget(header)
        main_layout.addLayout(header_layout)
        
        # Main content grid (form on left, summary on right)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Left side - Form
        form_card = QFrame()
        # Form card styling
        form_card.setObjectName("formCard")
        form_card.setStyleSheet(StyleSheet.card())
        form_card.setGraphicsEffect(StyleSheet.card_shadow())
        
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(16)
        
        # Basic Information Section
        basic_info = QLabel("Basic Information")
        basic_info.setFont(StyleSheet.get_font(16, "Medium"))
        form_layout.addWidget(basic_info)
        
        # Form grid for better alignment
        form_grid = QGridLayout()
        form_grid.setColumnStretch(0, 1)
        form_grid.setColumnStretch(1, 1)
        form_grid.setVerticalSpacing(16)
        form_grid.setHorizontalSpacing(16)
        
        # Name
        name_label = QLabel("Full Name")
        name_label.setFont(StyleSheet.get_font(12))
        self.name_input = QLineEdit()
        self.name_input.setMinimumHeight(40)
        self.name_input.setPlaceholderText("Enter your full name")
        self.name_input.setText(self.user_data.get("name", ""))
        self.name_input.setStyleSheet(StyleSheet.input_field())
        form_grid.addWidget(name_label, 0, 0)
        form_grid.addWidget(self.name_input, 1, 0, 1, 2)  # span 2 columns
        
        # Age
        age_label = QLabel("Age")
        age_label.setFont(StyleSheet.get_font(12))
        self.age_input = QLineEdit()
        self.age_input.setMinimumHeight(40)
        self.age_input.setPlaceholderText("Years")
        self.age_input.setText(str(self.user_data.get("age", "")))
        self.age_input.setValidator(QtGui.QIntValidator(1, 120))
        self.age_input.setStyleSheet(StyleSheet.input_field())
        form_grid.addWidget(age_label, 2, 0)
        form_grid.addWidget(self.age_input, 3, 0)
        
        # Gender
        gender_label = QLabel("Gender")
        gender_label.setFont(StyleSheet.get_font(12))
        self.gender_input = QComboBox()
        self.gender_input.setMinimumHeight(40)
        self.gender_input.addItems(["Select", "Male", "Female", "Other"])
        gender_index = self.gender_input.findText(self.user_data.get("gender", "Select"))
        self.gender_input.setCurrentIndex(gender_index if gender_index >= 0 else 0)
        self.gender_input.setStyleSheet(StyleSheet.input_field())
        form_grid.addWidget(gender_label, 2, 1)
        form_grid.addWidget(self.gender_input, 3, 1)
        
        # Health Information Section
        health_info = QLabel("Health Information")
        health_info.setFont(StyleSheet.get_font(16, "Medium"))
        form_grid.addWidget(health_info, 4, 0, 1, 2)
        
        # Height
        height_label = QLabel("Height")
        height_label.setFont(StyleSheet.get_font(12))
        self.height_input = QLineEdit()
        self.height_input.setMinimumHeight(40)
        self.height_input.setPlaceholderText("cm")
        self.height_input.setText(str(self.user_data.get("height", "")))
        self.height_input.setValidator(QtGui.QDoubleValidator(50, 250, 1))
        self.height_input.setStyleSheet(StyleSheet.input_field())
        form_grid.addWidget(height_label, 5, 0)
        form_grid.addWidget(self.height_input, 6, 0)
        
        # Weight
        weight_label = QLabel("Weight")
        weight_label.setFont(StyleSheet.get_font(12))
        self.weight_input = QLineEdit()
        self.weight_input.setMinimumHeight(40)
        self.weight_input.setPlaceholderText("kg")
        self.weight_input.setText(str(self.user_data.get("weight", "")))
        self.weight_input.setValidator(QtGui.QDoubleValidator(1, 500, 1))
        self.weight_input.setStyleSheet(StyleSheet.input_field())
        form_grid.addWidget(weight_label, 5, 1)
        form_grid.addWidget(self.weight_input, 6, 1)
        
        # Fitness Goals
        goals_label = QLabel("Fitness Goals")
        goals_label.setFont(StyleSheet.get_font(12))
        self.goals_input = QTextEdit()
        self.goals_input.setMinimumHeight(80)
        self.goals_input.setPlaceholderText("e.g., Weight loss, Flexibility, Stress reduction")
        self.goals_input.setText(self.user_data.get("goals", ""))
        self.goals_input.setStyleSheet(StyleSheet.input_field())
        form_grid.addWidget(goals_label, 7, 0, 1, 2)
        form_grid.addWidget(self.goals_input, 8, 0, 1, 2)
        
        form_layout.addLayout(form_grid)
        
        # Right side - Profile Summary
        summary_layout = QVBoxLayout()
        
        # Profile Summary Card with gradient background
        profile_summary = QFrame()
        profile_summary.setStyleSheet(StyleSheet.gradient_card())
        profile_summary.setMinimumHeight(200)
        profile_summary.setMaximumWidth(300)
        profile_summary.setGraphicsEffect(StyleSheet.card_shadow())
        
        summary_card_layout = QVBoxLayout(profile_summary)
        
        # Summary header
        summary_header = QLabel("Profile Summary")
        summary_header.setFont(StyleSheet.get_font(16, "Medium"))
        summary_header.setStyleSheet("color: white;")
        summary_card_layout.addWidget(summary_header)
        
        # Summary content
        summary_content = QVBoxLayout()
        summary_content.setSpacing(12)
        
        # Name summary
        name_summary_label = QLabel("Name")
        name_summary_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.name_summary = QLabel(self.user_data.get("name", "Not set"))
        self.name_summary.setStyleSheet("color: white; font-weight: 500;")
        summary_content.addWidget(name_summary_label)
        summary_content.addWidget(self.name_summary)
        
        # Age summary
        age_summary_label = QLabel("Age")
        age_summary_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.age_summary = QLabel(str(self.user_data.get("age", "Not set")))
        self.age_summary.setStyleSheet("color: white; font-weight: 500;")
        summary_content.addWidget(age_summary_label)
        summary_content.addWidget(self.age_summary)
        
        # BMI summary
        bmi_summary_label = QLabel("BMI")
        bmi_summary_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        
        # Calculate BMI if height and weight are available
        bmi_value = "Not calculated"
        if self.user_data.get("height") and self.user_data.get("weight"):
            try:
                height_m = float(self.user_data["height"]) / 100
                weight_kg = float(self.user_data["weight"])
                bmi = weight_kg / (height_m * height_m)
                bmi_value = f"{bmi:.1f}"
            except (ValueError, ZeroDivisionError):
                pass
                
        self.bmi_summary = QLabel(bmi_value)
        self.bmi_summary.setStyleSheet("color: white; font-weight: 500;")
        summary_content.addWidget(bmi_summary_label)
        summary_content.addWidget(self.bmi_summary)
        
        summary_card_layout.addLayout(summary_content)
        summary_layout.addWidget(profile_summary)
        
        # Health Tips Card
        health_tips = QFrame()
        health_tips.setStyleSheet(StyleSheet.card())
        health_tips.setMaximumWidth(300)
        health_tips.setGraphicsEffect(StyleSheet.card_shadow())
        
        tips_layout = QVBoxLayout(health_tips)
        
        tips_header = QLabel("Health Tips")
        tips_header.setFont(StyleSheet.get_font(16, "Medium"))
        tips_layout.addWidget(tips_header)
        
        tips_content = QLabel(
            "• Stay hydrated during your yoga sessions\n"
            "• Maintain consistent practice for best results\n"
            "• Listen to your body and avoid overexertion\n"
            "• Combine yoga with balanced nutrition"
        )
        tips_content.setStyleSheet(StyleSheet.body_text())
        tips_content.setWordWrap(True)
        tips_layout.addWidget(tips_content)
        
        summary_layout.addWidget(health_tips)
        
        # Goals Card
        goals_card = QFrame()
        goals_card.setStyleSheet(StyleSheet.card())
        goals_card.setMaximumWidth(300)
        goals_card.setGraphicsEffect(StyleSheet.card_shadow())
        
        goals_card_layout = QVBoxLayout(goals_card)
        
        goals_header = QLabel("Your Goals")
        goals_header.setFont(StyleSheet.get_font(16, "Medium"))
        goals_card_layout.addWidget(goals_header)
        
        self.goals_summary = QLabel(self.user_data.get("goals", "Set your fitness goals to get personalized recommendations."))
        self.goals_summary.setStyleSheet(StyleSheet.body_text())
        self.goals_summary.setWordWrap(True)
        goals_card_layout.addWidget(self.goals_summary)
        
        summary_layout.addWidget(goals_card)
        
        # Add spacer to push cards to the top
        summary_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Add form and summary to content layout
        content_layout.addWidget(form_card, 2)  # 2/3 of space
        content_layout.addLayout(summary_layout, 1)  # 1/3 of space
        
        main_layout.addLayout(content_layout)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(16)
        
        # Add spacer to push buttons to the right
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedSize(120, 50)
        self.cancel_btn.setFont(StyleSheet.get_font(14))
        self.cancel_btn.setStyleSheet(StyleSheet.button_secondary())
        self.cancel_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.cancel_btn)
        
        # Save button
        self.save_btn = QPushButton("Save Profile")
        self.save_btn.setFixedSize(180, 50)
        self.save_btn.setFont(StyleSheet.get_font(14))
        self.save_btn.setStyleSheet(StyleSheet.button_primary())
        self.save_btn.clicked.connect(self.save_profile)
        buttons_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Connect input fields to update summary in real-time
        self.name_input.textChanged.connect(self.update_summary)
        self.age_input.textChanged.connect(self.update_summary)
        self.height_input.textChanged.connect(self.update_summary)
        self.weight_input.textChanged.connect(self.update_summary)
        self.goals_input.textChanged.connect(self.update_summary)
    
    def update_summary(self):
        """Update the summary cards with current form values"""
        # Update name
        self.name_summary.setText(self.name_input.text() or "Not set")
        
        # Update age
        self.age_summary.setText(self.age_input.text() or "Not set")
        
        # Update BMI
        bmi_value = "Not calculated"
        if self.height_input.text() and self.weight_input.text():
            try:
                height_m = float(self.height_input.text()) / 100
                weight_kg = float(self.weight_input.text())
                bmi = weight_kg / (height_m * height_m)
                bmi_value = f"{bmi:.1f}"
            except (ValueError, ZeroDivisionError):
                pass
        self.bmi_summary.setText(bmi_value)
        
        # Update goals
        self.goals_summary.setText(self.goals_input.toPlainText() or "Set your fitness goals to get personalized recommendations.")
    
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
            "goals": self.goals_input.toPlainText()
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
