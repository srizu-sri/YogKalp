import os
import sys
import time
import threading
import pyttsx3
import json
import webbrowser
import warnings 
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTimer, QTime, Qt, QSize, QObject
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QWidget, QLabel, QLineEdit, QPushButton, QDialog, QCheckBox, QInputDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout, QSizePolicy, QFrame, QMessageBox
import google.generativeai as genai
from pose_estimator import PoseEstimator
from calorie_calculator import CalorieCalculator
from camera_thread import CameraThread
from esp32_camera import ESP32CameraReceiver
from voice_assistant import VoiceAssistant
from ui.components import MetricCard, ToggleSwitch
from ui.food_recommendations import IndianFoodRecommendations
from ui.profile_dialog import UserProfileDialog
from yoga_assistant_1 import YogaAssistant
from server import esp_data
from health_details import HealthDetailsDialog

class ModernYogaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YogKalp")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8F9FA;
                font-family: 'Google Sans', 'Segoe UI', 'Arial';
            }
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 24px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1765cc;
            }
            QPushButton:pressed {
                background-color: #185abc;
            }
            QLineEdit {
                border: 1px solid #DADCE0;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
            QLabel {
                color: #202124;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        self.resize(1000, 700)
        self.estimator = PoseEstimator()
        self.camera_thread = None
        self.training_images_count = 0
        self.current_accuracy = 0.0
        self.current_pose_name = ""
        self.current_batch_complete = False  # Track if current batch is complete
        
        # Initialize user profile data
        self.calculate_bmi = {}
        
        # Initialize heart rate alert flag
        self.heart_rate_alert_shown = False
        
        # Setup UI only once
        self.setup_ui()
        
        # Load user profile and health conditions after UI setup
        self.load_calculate_bmi()
        self.load_health_conditions()
     
        self.poses_trained_value.setText(str(len(self.estimator.named_poses)))    
        
        # Initialize voice assistant
        self.voice_assistant = VoiceAssistant()
        
        # Welcome message with name if available
        welcome_msg = "Welcome to YogKalp. Your personal yoga and health assistant."
        if "name" in self.calculate_bmi and self.calculate_bmi["name"]:
            welcome_msg = f"Welcome {self.calculate_bmi['name']} to YogKalp. Your personal yoga and health assistant."
        self.voice_assistant.speak(welcome_msg)
            
        # Update Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)
        
        # Calorie calcuation timer
        self.calorie_timer = QTimer()
        self.calorie_timer.timeout.connect(self.update_calories_burned)
        self.calorie_timer.start(3000)  # Updates every 3 seconds
        
    def speak_text(self, text):
        """Use text-to-speech to speak the given text"""
        # Create a separate thread for TTS to avoid UI freezing
        def tts_thread_func(text_to_speak):
            try:
                engine = pyttsx3.init()
                engine.say(text_to_speak)
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
                
        # Start TTS in a separate thread
        tts_thread = threading.Thread(target=tts_thread_func, args=(text,))
        tts_thread.daemon = True  # Thread will exit when main program exits
        tts_thread.start()
        
    def setup_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Replace text title with logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("c:/Users/sriva/OneDrive/Desktop/YogKalp/YogKalp_logo.jpg")
        logo_label.setPixmap(logo_pixmap.scaled(180, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        header_layout.addWidget(logo_label)
        
        header_layout.addStretch()
        
        # Health Details Button
        self.health_details_btn = QPushButton("Health Details")
        self.health_details_btn.setFixedSize(QSize(150, 40))
        self.health_details_btn.clicked.connect(self.show_health_details)
        header_layout.addWidget(self.health_details_btn)
        self.health_details_btn.setStyleSheet("""
            QPushButton {
                border-radius: 20px}""")
        
        # Yoga Assistant Button 
        self.yoga_assistant_btn = QPushButton("Yoga Assistant")
        self.yoga_assistant_btn.setFixedSize(QSize(150, 40))
        self.yoga_assistant_btn.clicked.connect(self.open_yoga_assistant)
        header_layout.addWidget(self.yoga_assistant_btn)
        self.yoga_assistant_btn.setStyleSheet("""
            QPushButton {
                border-radius: 20px}""")        
        
        # Profile section
        profile_btn = QPushButton("Profile")
        profile_btn.setFixedSize(QSize(100, 40))
        profile_btn.clicked.connect(self.show_profile)
        header_layout.addWidget(profile_btn)
        profile_btn.setStyleSheet("""
            QPushButton {
                border-radius: 18px}""")
        
        main_layout.addWidget(header)
        
        # User inputs
        input_card = QFrame()
        input_card.setObjectName("inputCard")
        input_card.setStyleSheet("""
            #inputCard {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        # Apply card shadow effect
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        input_card.setGraphicsEffect(shadow)
        
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 20, 20, 20)
        
        input_title = QLabel("Your Information")
        input_title.setFont(QFont("Google Sans", 16, QFont.Weight.Medium))
        input_layout.addWidget(input_title)
        
        input_fields = QHBoxLayout()
        input_fields.setSpacing(16)
        
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("Weight (kg)")
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("Height (cm)")
        
        # Add food recommendations button
        self.food_rec_btn = QPushButton("View Food Recommendations")
        self.food_rec_btn.clicked.connect(self.show_food_recommendations)
        input_layout.addWidget(self.food_rec_btn)
        food_rec_btn = QFrame()
        food_rec_btn.setObjectName("food_btn")
        self.food_rec_btn.setStyleSheet("""
            QPushButton {
                border-radius: 20px}""")
        
        input_fields.addWidget(self.weight_input)
        input_fields.addWidget(self.height_input)
        input_layout.addLayout(input_fields)
        
        main_layout.addWidget(input_card)
        
        # Scroll area for metrics
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        metrics_layout = QVBoxLayout(scroll_content)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(20)
        
        # Metrics section title
        metrics_title = QLabel("Today's Metrics")
        metrics_title.setFont(QFont("Google Sans", 18, QFont.Weight.Medium))
        metrics_layout.addWidget(metrics_title)
        
        # Metrics cards
        metrics_grid = QGridLayout()
        metrics_grid.setContentsMargins(0, 0, 0, 0)
        metrics_grid.setSpacing(16)
        
        # BMI Card
        self.bmi_card = MetricCard("BMI", "0", "kg/m²", color="#4285F4")
        metrics_grid.addWidget(self.bmi_card, 0, 0)
        
        # Heart Rate Card
        self.heart_card = MetricCard("Heart Rate", "0", "bpm", color="#EA4335")
        metrics_grid.addWidget(self.heart_card, 0, 1)
        
        # Calories burnt Card
        self.calories_card = MetricCard("Calories Burned", "0", "kcal", color="#34A853")
        metrics_grid.addWidget(self.calories_card,0, 2)
        
        # SpO2 Level Card
        self.spo2_card = MetricCard("SpO2 Level", "0", "%", color="#9C27B0")
        metrics_grid.addWidget(self.spo2_card, 1, 0)
        
        # Cardio
        self.strength_card = MetricCard("Cardio/Strength Training", "0", "reps", color="#FF9800")
        metrics_grid.addWidget(self.strength_card, 1, 1)
        
        self.steps_value = self.strength_card
        
        # Temperature Card
        temp_card = QFrame()
        temp_card.setObjectName("metricCard")
        temp_card.setStyleSheet("""
            #metricCard {
                background-color: white;
                border-radius: 12px;
                padding: 12px;
            }
        """)

        # Apply card shadow effect
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        temp_card.setGraphicsEffect(shadow)

        temp_layout = QVBoxLayout(temp_card)
        temp_layout.setContentsMargins(16, 16, 16, 16)

        temp_title = QLabel("Body Temperature")
        temp_title.setFont(QFont("Google Sans", 12))
        temp_title.setStyleSheet("color: #673AB7;")
        temp_layout.addWidget(temp_title)

        temp_values = QHBoxLayout()

        pre_temp_layout = QVBoxLayout()
        pre_temp_label = QLabel("Pre-workout (Body temperature)")
        pre_temp_label.setFont(QFont("Google Sans", 10))
        pre_temp_label.setStyleSheet("color: #5F6368;")
        self.pre_temp_value = QLabel("0.00°C")
        self.pre_temp_value.setFont(QFont("Google Sans", 18, QFont.Weight.Medium))
        pre_temp_layout.addWidget(pre_temp_label)
        pre_temp_layout.addWidget(self.pre_temp_value)

        post_temp_layout = QVBoxLayout()
        post_temp_label = QLabel("Body heat (Post-workout)")
        post_temp_label.setFont(QFont("Google Sans", 10))
        post_temp_label.setStyleSheet("color: #5F6368;")
        self.post_temp_value = QLabel("0.00°C")
        self.post_temp_value.setFont(QFont("Google Sans", 18, QFont.Weight.Medium))
        post_temp_layout.addWidget(post_temp_label)
        post_temp_layout.addWidget(self.post_temp_value)

        temp_values.addLayout(pre_temp_layout)
        temp_values.addLayout(post_temp_layout)

        temp_layout.addLayout(temp_values)
        
        metrics_grid.addWidget(temp_card, 2, 0, 1, 2)
        
        # Add Pose Accuracy Card
        self.accuracy_card = QFrame()
        self.accuracy_card.setObjectName("metricCard")
        self.accuracy_card.setStyleSheet("""
            #metricCard {
                background-color: white;
                border-radius: 12px;
                padding: 12px;
            }
        """)
        
        # Apply card shadow effect
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.accuracy_card.setGraphicsEffect(shadow)
        
        accuracy_layout = QVBoxLayout(self.accuracy_card)
        accuracy_layout.setContentsMargins(16, 16, 16, 16)
        
        # Create header with title and toggle switch
        accuracy_header = QHBoxLayout()
        
        accuracy_title = QLabel("Pose Accuracy")
        accuracy_title.setFont(QFont("Google Sans", 12))
        accuracy_title.setStyleSheet("color: #7B1FA2;")  # Purple color
        accuracy_header.addWidget(accuracy_title)
        
        accuracy_header.addStretch()
        
         # Variables to track feedback counts
        self.low_accuracy_feedback_count = 0
        self.medium_accuracy_feedback_count = 0
        self.last_accuracy_level = "high"  # Track the last accuracy level
        
        # Add palm detection toggle with label
        palm_toggle_layout = QHBoxLayout()
        palm_toggle_label = QLabel("Palm Detection:")
        palm_toggle_label.setFont(QFont("Google Sans", 10))
        palm_toggle_label.setStyleSheet("color: #5F6368;")
        palm_toggle_layout.addWidget(palm_toggle_label)
        
        self.palm_toggle = ToggleSwitch()
        self.palm_toggle.setChecked(False)
        self.palm_toggle.toggled.connect(self.toggle_palm_detection)
        palm_toggle_layout.addWidget(self.palm_toggle)
        
        accuracy_header.addLayout(palm_toggle_layout)

        # ESP32-CAM controls
        esp32_cam_layout = QHBoxLayout()
        esp32_cam_label = QLabel("Use YogKalp Cam")
        esp32_cam_label.setFont(QFont("Google Sans", 10))
        esp32_cam_layout.addWidget(esp32_cam_label)

        self.esp32_cam_toggle = ToggleSwitch()
        self.esp32_cam_toggle.setChecked(False)
        esp32_cam_layout.addWidget(self.esp32_cam_toggle)
        accuracy_header.addLayout(esp32_cam_layout) # Add to accuracy_header
        
        accuracy_layout.addLayout(accuracy_header)
        
        # Current accuracy value with pose name
        self.pose_accuracy_value = QLabel("Training required")
        self.pose_accuracy_value.setFont(QFont("Google Sans", 22, QFont.Weight.Medium))
        accuracy_layout.addWidget(self.pose_accuracy_value)
        
        # explanation text
        self.accuracy_info = QLabel("Capture at least 5 training images to see pose accuracy")
        self.accuracy_info.setFont(QFont("Google Sans", 10))
        self.accuracy_info.setStyleSheet("color: #5F6368;")
        self.accuracy_info.setWordWrap(True)
        accuracy_layout.addWidget(self.accuracy_info)

        # Start Camera button
        self.start_btn = QPushButton("Start Camera")
        self.start_btn.clicked.connect(self.toggle_camera)
        self.start_btn.setFixedHeight(50)
        self.start_btn.setFont(QFont("Google Sans", 14))
        accuracy_layout.addWidget(self.start_btn) # Add to accuracy_layout
        
        metrics_grid.addWidget(self.accuracy_card, 3, 0, 1, 2)
        
        metrics_layout.addLayout(metrics_grid)
        
        # Training Images Card
        training_card = QFrame()
        training_card.setObjectName("metricCard")
        training_card.setStyleSheet("""
            #metricCard {
                background-color: white;
                border-radius: 12px;
                padding: 12px;
            }
        """)
        
        # Apply card shadow effect
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        training_card.setGraphicsEffect(shadow)
        
        training_layout = QVBoxLayout(training_card)
        training_layout.setContentsMargins(16, 16, 16, 16)
        
        training_title = QLabel("Training Progress")
        training_title.setFont(QFont("Google Sans", 12))
        training_title.setStyleSheet("color: #00897B;")
        training_layout.addWidget(training_title)
        
        training_info = QHBoxLayout()
        
        # voice assistant toggle to header
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("YogKalp")
        title.setFont(QFont("Google Sans", 24, QFont.Weight.Medium))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # voice assistant toggle
        voice_toggle_layout = QHBoxLayout()
        voice_toggle_label = QLabel("Voice Assistant:")
        voice_toggle_label.setFont(QFont("Google Sans", 10))
        voice_toggle_layout.addWidget(voice_toggle_label)
        
        self.voice_toggle = ToggleSwitch()
        self.voice_toggle.setChecked(True)  # Voice enabled by default
        self.voice_toggle.toggled.connect(self.toggle_voice_assistant)
        voice_toggle_layout.addWidget(self.voice_toggle)
        
        header_layout.addLayout(voice_toggle_layout)
        
        # Profile section placeholder
        profile_btn = QPushButton("Profile")
        profile_btn.setFixedSize(QSize(100, 40))
        header_layout.addWidget(profile_btn)
        
        # Training images count
        training_count_layout = QVBoxLayout()
        training_count_label = QLabel("Captured Images")
        training_count_label.setFont(QFont("Google Sans", 10))
        training_count_label.setStyleSheet("color: #5F6368;")
        self.training_count_value = QLabel("0")
        self.training_count_value.setFont(QFont("Google Sans", 22, QFont.Weight.Medium))
        training_count_layout.addWidget(training_count_label)
        training_count_layout.addWidget(self.training_count_value)
        
        # Add poses trained count
        poses_trained_layout = QVBoxLayout()
        poses_trained_label = QLabel("Poses Trained")
        poses_trained_label.setFont(QFont("Google Sans", 10))
        poses_trained_label.setStyleSheet("color: #5F6368;")
        self.poses_trained_value = QLabel("0")
        self.poses_trained_value.setFont(QFont("Google Sans", 22, QFont.Weight.Medium))
        poses_trained_layout.addWidget(poses_trained_label)
        poses_trained_layout.addWidget(self.poses_trained_value)
        
        # Current pose name display
        pose_name_layout = QVBoxLayout()
        pose_name_label = QLabel("Current Pose")
        pose_name_label.setFont(QFont("Google Sans", 10))
        pose_name_label.setStyleSheet("color: #5F6368;")
        self.pose_name_value = QLabel("None")
        self.pose_name_value.setFont(QFont("Google Sans", 18, QFont.Weight.Medium))
        pose_name_layout.addWidget(pose_name_label)
        pose_name_layout.addWidget(self.pose_name_value)
        
        training_info.addLayout(training_count_layout)
        training_info.addLayout(poses_trained_layout)
        training_info.addLayout(pose_name_layout)
        
        # Instructions
        self.training_instructions = QLabel("Press 'T' while camera is active to capture a training image")
        self.training_instructions.setFont(QFont("Google Sans", 10))
        self.training_instructions.setStyleSheet("color: #5F6368;")
        self.training_instructions.setWordWrap(True)
        
        training_info.addLayout(training_count_layout)
        training_info.addLayout(pose_name_layout)
        
        training_layout.addLayout(training_info)
        training_layout.addWidget(self.training_instructions)
        
        metrics_layout.addWidget(training_card)
        
        # Add everything to scroll area
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        self.setCentralWidget(central_widget)
        self.setCentralWidget(central_widget)
    
    def open_yoga_assistant(self):
        """Open the Yoga Assistant window"""
        self.yoga_assistant = YogaAssistant(self)
        self.yoga_assistant.show()
        
    def update_data(self):
        # Initialize variables for later use
        heart_rate = 0
        post_temp = 0
        strength_count = 0
        
        # Update health metrics from ESP32
        try:
            # Update heart rate
            if "heart_rate" in esp_data and esp_data["heart_rate"] > 0:
                heart_rate = esp_data["heart_rate"]  # Store for later use
                self.heart_card.update_value(str(heart_rate))
                
                # Check for high heart rate and show alert if needed
                if heart_rate > 90 and not self.heart_rate_alert_shown:
                    self.heart_rate_alert_shown = True
                    QMessageBox.warning(self, "High Heart Rate", 
                                        f"Your heart rate is {heart_rate} BPM, which is elevated. Consider taking a break.")
                    self.voice_assistant.speak(f"Warning. Your heart rate is {heart_rate} beats per minute, which is elevated. Consider taking a break.")
            
            # Update SpO2
            if "spo2" in esp_data and esp_data["spo2"] > 0:
                self.spo2_card.update_value(str(esp_data["spo2"]))
            
            # Update temperature
            if "body_temp_pre" in esp_data and esp_data["body_temp_pre"] > 0:
                self.pre_temp_value.setText(f"{esp_data['body_temp_pre']:.1f}°C")
                
            # Update post-workout temperature
            if "body_temp_post" in esp_data and esp_data["body_temp_post"] > 0:
                post_temp = esp_data["body_temp_post"]  # Store for later use
                self.post_temp_value.setText(f"{post_temp:.1f}°C")
            
            # Update steps from MPU6050
            if "steps" in esp_data:
                strength_count = esp_data["steps"]  # Store for later use
                self.steps_value.update_value(str(strength_count))
                print(f"Updating steps display to: {strength_count}")
    
            # Update sensor status indicators commented out
            # if "max30102_status" in esp_data:
            #     self.update_sensor_status("MAX30102", esp_data["max30102_status"])
                
        except Exception as e:
            print(f"Error updating data: {e}")
        
        # Calculate BMI if weight and height are provided
        try:
            bmi = 0
            if self.weight_input.text() and self.height_input.text():
                weight = float(self.weight_input.text())
                height = float(self.height_input.text()) / 100  # Convert cm to m
                bmi = weight / (height * height)
                self.bmi_card.update_value(f"{bmi:.1f}")
                
                # Update BMI category
                if bmi < 18.5:
                    self.bmi_card.update_category("Underweight", "#FB8C00")
                elif bmi < 25:
                    self.bmi_card.update_category("Normal", "#4CAF50")
                elif bmi < 30:
                    self.bmi_card.update_category("Overweight", "#FFC107")
                else:
                    self.bmi_card.update_category("Obese", "#F44336")
                
                # Calculate estimated calories burned based on multiple factors
                if heart_rate > 0 and weight > 0:
                    # Base metabolic rate (BMR) factor based on heart rate
                    hr_factor = 1.0
                    if heart_rate > 120:
                        hr_factor = 1.8
                    elif heart_rate > 100:
                        hr_factor = 1.5
                    elif heart_rate > 80:
                        hr_factor = 1.2
                    
                    # BMI factor (higher BMI = more calories burned for same activity)
                    bmi_factor = 1.0
                    if bmi > 30:
                        bmi_factor = 1.2
                    elif bmi > 25:
                        bmi_factor = 1.1
                    elif bmi < 18.5:
                        bmi_factor = 0.9
                    
                    # Temperature factor (higher body heat = more calories burned)
                    temp_factor = 1.0
                    if post_temp > 37.5:
                        temp_factor = 1.15
                    elif post_temp > 37.0:
                        temp_factor = 1.1
                    
                    # Activity factor based on strength training only now
                    activity_factor = 1.0 + (strength_count / 100)
                    
                    # Calculate calories: weight * combined factors * time (30 min)
                    calories = weight * hr_factor * bmi_factor * temp_factor * activity_factor * 0.5
                    self.calorie_card.update_value(f"{int(calories)}")
        except ValueError as e:
            print(f"Error calculating BMI: {e}")
        
        # Update pose accuracy display
        try:
            if self.training_images_count >= 5 and self.current_pose_name:
                self.pose_accuracy_value.setText(f"{self.current_pose_name}: {self.current_accuracy:.1f}%")
                
                # Update accuracy info text based on accuracy level
                if self.current_accuracy > 80:
                    self.accuracy_info.setText("Excellent form! Keep it up.")
                    self.accuracy_info.setStyleSheet("color: #4CAF50;")  # Green
                elif self.current_accuracy > 60:
                    self.accuracy_info.setText("Good form. Minor adjustments needed.")
                    self.accuracy_info.setStyleSheet("color: #FFC107;")  # Yellow/Orange
                else:
                    self.accuracy_info.setText("Form needs improvement. Follow the guide.")
                    self.accuracy_info.setStyleSheet("color: #F44336;")  # Red
            else:
                self.pose_accuracy_value.setText("Training required")
                self.accuracy_info.setText("Capture at least 5 training images to see pose accuracy")
                self.accuracy_info.setStyleSheet("color: #5F6368;")  # Gray
        except Exception as e:
            print(f"Error updating pose accuracy: {e}")

    def update_calories_burned(self):
        """Calculate and update calories burned based on current session data"""
        try:
            # Get current values
            heart_rate = esp_data.get("heart_rate", 0)
            body_temp = max(esp_data.get("body_temp_pre", 37.0), esp_data.get("body_temp_post", 37.0))
            strength_count = esp_data.get("steps", 0)
            
            # Only calculate if we have valid heart rate data and user input
            if heart_rate > 40 and self.weight_input.text():
                # Get user data
                weight = float(self.weight_input.text())
                height = float(self.height_input.text()) if self.height_input.text() else 170
                
                # Calculate BMI
                height_m = height / 100  # Convert cm to m
                bmi = weight / (height_m * height_m)
                
                # Heart rate factor (higher HR = more calories burned)
                hr_factor = 1.0
                if heart_rate > 120:
                    hr_factor = 1.8
                elif heart_rate > 100:
                    hr_factor = 1.5
                elif heart_rate > 80:
                    hr_factor = 1.2
                
                # BMI factor (higher BMI = more calories burned for same activity)
                bmi_factor = 1.0
                if bmi > 30:
                    bmi_factor = 1.2
                elif bmi > 25:
                    bmi_factor = 1.1
                elif bmi < 18.5:
                    bmi_factor = 0.9
                
                # Temperature factor (higher body heat = more calories burned)
                temp_factor = 1.0
                if body_temp > 37.5:
                    temp_factor = 1.15
                elif body_temp > 37.0:
                    temp_factor = 1.1
                
                # Activity factor based on strength training/steps
                activity_factor = 1.0 + (strength_count / 100)
                
                # Calculate calories: weight * combined factors * time (minutes since last update)
                if not hasattr(self, 'last_calorie_update'):
                    self.last_calorie_update = time.time()
                    self.total_calories = 0
                
                current_time = time.time()
                minutes_elapsed = (current_time - self.last_calorie_update) / 60
                
                # MET value for yoga (3-6 depending on intensity)
                yoga_met = 4.0
                
                # Calories burned = MET * weight (kg) * time (hours) * adjustment factors
                calories = yoga_met * weight * (minutes_elapsed / 60) * hr_factor * bmi_factor * temp_factor * activity_factor
                
                # Add to total
                self.total_calories += calories
                
                # Update the calories display
                self.calories_card.update_value(f"{int(self.total_calories)}")
                
                # Update last update time
                self.last_calorie_update = current_time
                
        except Exception as e:
            print(f"Error calculating calories: {e}")
            
    def show_heart_rate_alert(self):
        """Show alert for high heart rate with recommended yoga poses"""
        # Create message box with yoga pose recommendations
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Heart Rate Alert")
        
        # Set message with recommended poses
        message = (
            "<h3>Irregular Heart Rate Detected!</h3>"
            "<p>Your heart rate is elevated. Consider practicing these calming yoga poses:</p>"
            "<ul>"
            "<li><b>Lotus Pose (Padmasana)</b>: Sit cross-legged with feet on opposite thighs</li>"
            "<li><b>Child's Pose (Balasana)</b>: Kneel and bend forward with arms extended</li>"
            "<li><b>Corpse Pose (Savasana)</b>: Lie flat on your back with arms at sides</li>"
            "</ul>"
            "<p>Remember to breathe deeply and slowly while practicing these poses.</p>"
        )
        msg.setText(message)
        
        # Add buttons
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Make the dialog non-modal so it doesn't block the app
        msg.setModal(False)
        
        # Show the message box
        msg.show()
        
    def update_accuracy(self, accuracy, pose_name):
        """Update the pose accuracy display and provide voice feedback"""
        self.current_accuracy = accuracy
        self.current_pose_name = pose_name
        
        # Update accuracy display
        self.pose_accuracy_value.setText(f"{pose_name}: {accuracy:.1f}%")
        
        # Update accuracy info text based on accuracy level
        current_level = ""
        if accuracy > 80:
            self.accuracy_info.setText("Excellent form! Keep it up.")
            self.accuracy_info.setStyleSheet("color: #4CAF50;")  # Green
            current_level = "high"
            
        elif accuracy > 60:
            self.accuracy_info.setText("Good form. Minor adjustments needed.")
            self.accuracy_info.setStyleSheet("color: #FFC107;")  # Yellow/Orange
            current_level = "medium"
            
            # Only provide voice feedback twice for medium accuracy
            if self.last_accuracy_level != "medium" and self.medium_accuracy_feedback_count < 2:
                self.voice_assistant.speak(f"Your {pose_name} form needs minor adjustments.")
                self.medium_accuracy_feedback_count += 1
        else:
            self.accuracy_info.setText("Form needs improvement. Follow the guide.")
            self.accuracy_info.setStyleSheet("color: #F44336;")  # Red
            current_level = "low"
            
            # Only provide voice feedback twice for low accuracy
            if self.last_accuracy_level != "low" and self.low_accuracy_feedback_count < 2:
                self.voice_assistant.speak(f"Your {pose_name} form needs significant improvement. Please check the guide.")
                self.low_accuracy_feedback_count += 1
        
        # Reset counters if level changes
        if current_level != self.last_accuracy_level:
            if current_level == "high":
                # Reset counters when returning to high accuracy
                self.medium_accuracy_feedback_count = 0
                self.low_accuracy_feedback_count = 0
            self.last_accuracy_level = current_level
    
    def toggle_camera(self):
        if self.camera_thread and self.camera_thread.running:
            # Stop camera
            self.camera_thread.stop()
            self.camera_thread.wait()  # Wait for thread to finish
            self.camera_thread = None
            self.start_btn.setText("Start Camera")
            self.start_btn.setStyleSheet("""
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 24px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            """)
        else:
            # Start camera using QThread
            self.camera_thread = CameraThread(self.estimator)
            
            # Set initial palm detection state from toggle
            self.camera_thread.set_palm_detection_enabled(self.palm_toggle.isChecked())
            
            # Set ESP32-CAM options
            use_esp32_cam = self.esp32_cam_toggle.isChecked()
            if use_esp32_cam:
                # Use the hardcoded URL from ESP32CameraReceiver class
                self.camera_thread.set_esp32_cam_enabled(True)
                
            # Connect signals to slots
            self.camera_thread.training_count_updated.connect(self.update_training_count)
            self.camera_thread.accuracy_updated.connect(self.update_accuracy)
            self.camera_thread.model_updated.connect(self.update_pose_list)
            self.camera_thread.pose_count_updated.connect(self.update_poses_trained)
            self.camera_thread.camera_error.connect(self.show_camera_error)  # Connect new signal
            
            # Start the thread
            self.camera_thread.start()
            
            # Update button text
            self.start_btn.setText("Stop Camera")
            self.start_btn.setStyleSheet("""
                background-color: #EA4335;
                color: white;
                border: none;
                border-radius: 24px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            """)
            
    def show_camera_error(self, error_message):
        """Show popup for camera connection errors"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Camera Connection Error")
        msg.setText(error_message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setModal(False)  # Non-modal dialog
        msg.show()
        
        # Also provide voice feedback
        self.voice_assistant.speak("Camera connection error. " + error_message)
            
    def update_pose_list(self):
        """
        Update the UI when the pose list changes
        """
        # Update pose name dropdown or list if we have one
        # For now, just update the current pose name display
        if self.current_pose_name:
            self.pose_name_value.setText(self.current_pose_name)
            
            # Update instructions based on training progress
            if self.training_images_count >= 5:
                self.training_instructions.setText("Continue capturing poses or switch to a new pose")
            else:
                self.training_instructions.setText(f"Capture {5 - self.training_images_count} more images to complete this pose")
    
    def update_training_count(self, count):
        """
        Update the training count and prompt for pose name if needed
        """
        self.training_images_count = count
        self.training_count_value.setText(str(count))
        
        # Check if we've reached a multiple of 5
        if count > 0 and count % 5 == 0:
            # Only prompt for pose name if we haven't already for this batch
            if not hasattr(self, 'current_batch_complete') or not self.current_batch_complete:
                self.current_batch_complete = True
                # Prompt for pose name
                name, ok = QInputDialog.getText(self, "Name Your Pose", 
                                                "Enter a name for this pose batch:", 
                                                QLineEdit.EchoMode.Normal)
                if ok and name:
                    self.current_pose_name = name
                    self.pose_name_value.setText(name)
                    
                    # Save the current batch with this name
                    if self.camera_thread:
                        self.camera_thread.set_pose_name(name)
                        self.camera_thread.save_current_batch(name)
        elif count % 5 != 0:
            # Reset the batch completion flag when not at a multiple of 5
            self.current_batch_complete = False
    
    def update_poses_trained(self, count):
        """Update the poses trained count display"""
        self.poses_trained_value.setText(str(count))
    
    def toggle_palm_detection(self, enabled):
        """Enable or disable palm detection feature"""
        if self.camera_thread and self.camera_thread.running:
            self.camera_thread.set_palm_detection_enabled(enabled)
            
        # Update the instructions text based on the toggle state
        if enabled:
            self.training_instructions.setText("Press 'T' or show open palm to capture training images")
        else:
            self.training_instructions.setText("Press 'T' to capture training images (palm detection disabled)")

    def toggle_voice_assistant(self, enabled):
        """Enable or disable voice assistant"""
        self.voice_assistant.toggle_voice(enabled)
        if enabled:
            self.voice_assistant.speak("Voice assistant enabled")
            
    def get_benefits(self):
        """Return food benefits based on health conditions"""
        benefits = {
            "General": [
                "Whole grains provide sustained energy for yoga practice",
                "Leafy greens help reduce inflammation and improve flexibility",
                "Nuts and seeds offer protein and healthy fats for muscle recovery",
                "Berries contain antioxidants that help with post-workout recovery",
                "Hydration with water and herbal teas improves overall performance"
            ],
            "Diabetes": [
                "Cinnamon may help regulate blood sugar levels",
                "Leafy greens are low in carbs and high in nutrients",
                "Beans and legumes provide protein without raising blood sugar significantly",
                "Berries have a lower glycemic index than other fruits",
                "Nuts provide healthy fats without impacting blood sugar"
            ],
            "High Blood Pressure": [
                "Bananas are high in potassium which helps lower blood pressure",
                "Beets contain nitrates that can help reduce blood pressure",
                "Dark chocolate (70%+ cocoa) may help lower blood pressure",
                "Garlic has compounds that help reduce hypertension",
                "Leafy greens are high in potassium and magnesium"
            ],
            "Heart Disease": [
                "Fatty fish like salmon provide omega-3 fatty acids for heart health",
                "Oats contain beta-glucan fiber that helps lower cholesterol",
                "Berries are rich in antioxidants that benefit heart health",
                "Nuts contain heart-healthy monounsaturated fats",
                "Olive oil helps reduce inflammation and improve cholesterol"
            ],
            "Joint Pain/Arthritis": [
                "Turmeric contains curcumin which has anti-inflammatory properties",
                "Fatty fish provides omega-3s that reduce joint inflammation",
                "Cherries contain antioxidants that may reduce pain and inflammation",
                "Ginger has anti-inflammatory compounds that may reduce joint pain",
                "Walnuts are high in omega-3 fatty acids that help reduce inflammation"
            ]
        }
        
        # Get user's health conditions if available
        relevant_benefits = ["General Benefits:"]
        for item in benefits["General"]:
            relevant_benefits.append("• " + item)
        
        # Add condition-specific benefits if user has those conditions
        if hasattr(self, 'health_conditions'):
            for condition, has_condition in self.health_conditions.items():
                if has_condition and condition in benefits:
                    relevant_benefits.append(f"\n{condition} Benefits:")
                    for item in benefits[condition]:
                        relevant_benefits.append("• " + item)
        
        return "\n".join(relevant_benefits)

    def show_food_recommendations(self):
        try:
            # Initialize Gemini API
            try:
                # Attempt to get the API key from an environment variable
                api_key = os.getenv("GEMINI_API_KEY")
                print(f"Attempt 1: API key from os.getenv(\"GEMINI_API_KEY\"): {api_key}") # DEBUG PRINT

                if not api_key:
                    # Fallback to a hardcoded key if the environment variable is not set
                    api_key = "AIzaSyCF8eLRxip4jSRKKzdJxGABFLV_l3OwyZ4" # Or your actual key
                    print(f"Attempt 2: API key after fallback: {api_key}") # DEBUG PRINT
                    if api_key == "AIzaSyCF8eLRxip4jSRKKzdJxGABFLV_l3OwyZ4": # Check if it's still the placeholder or your actual key
                         QMessageBox.warning(self, "API Key Missing", "GEMINI_API_KEY not found in environment variables and no fallback key is set. Please set the environment variable or update the hardcoded key.")
                         return
                
                print(f"Final API key being used for genai.configure: {api_key}") # DEBUG PRINT
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash') 
                self.gemini_initialized = True
            except Exception as e:
                print(f"Exception during Gemini API initialization: {e}") # DEBUG PRINT
                QMessageBox.critical(self, "Gemini API Error", f"Failed to initialize Gemini API: {e}")
                self.gemini_initialized = False
                return

            #  food dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Personalized Food Recommendations")
            dialog.setMinimumWidth(600)
            dialog.setMinimumHeight(500)
            dialog.setStyleSheet("""
                QDialog { background-color: #f0f0f0; }
                QLabel { font-size: 14px; color: #333; }
                QPushButton {
                    background-color: #1a73e8;
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 8px 16px;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #1765cc; }
                QFrame { background-color: white; border-radius: 8px; margin-bottom: 10px; }
            """)

            # Add minimize and maximize controls
            dialog.setWindowFlags(dialog.windowFlags() |
                                  Qt.WindowType.WindowMinimizeButtonHint |
                                  Qt.WindowType.WindowMaximizeButtonHint)

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            title_label = QLabel("Personalized Indian Dish Recommendations")
            title_label.setFont(QFont("Google Sans", 18, QFont.Weight.Bold))
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)

            # Check if BMI and health conditions are available
            bmi = self.calculate_bmi.get("bmi", None)
            health_conditions_list = [cond for cond, checked in self.health_conditions.items() if checked]

            if bmi and health_conditions_list:
                # Gemini API call
                # model = genai.GenerativeModel('gemini-2.0-flash') # Model is now initialized as self.model
                if not self.gemini_initialized:
                    QMessageBox.critical(self, "API Error", "Gemini API not initialized. Cannot fetch recommendations.")
                    return
                model = self.model
                prompt = (
                    f"Based on a BMI of {bmi:.2f} and health conditions: {', '.join(health_conditions_list)}, "
                    f"recommend 2 Indian dishes for breakfast and 2 Indian dishes for dinner. "
                    f"For each dish, provide its name, a webpage link for its recipe (preferring popular articles), "
                    f"and a brief explanation of its health benefits relevant to the given BMI and health conditions. "
                    f"Format each dish as: 'Dish Name: [Name] | Web Link: [Link] | Benefits: [Benefits]'. "
                    f"Separate each dish recommendation with a newline."
                    # f"Ensure the YouTube links are in the format 'https://www.youtube.com/watch?v=VIDEO_ID'."
                    f"Start by finding the dishes in webpages of 'Nisha Madhulika, Sanjeev Kapoor Khazana, Ranveer Brar, Manjula's Kitchen, Kabita's Kitchen, and Hebbars Kitchen'"
                    f"If dishes not found in the mentioned pages, search for the dishes in youtube channel by 'Indian Food Recipes'"
                )

                try:
                    response = model.generate_content(prompt)
                    recommendations_text = response.text
                except Exception as api_error:
                    QMessageBox.warning(self, "API Error", f"Could not fetch recommendations from Gemini API: {api_error}")
                    # Fallback or default message
                    recommendations_text = "Could not fetch personalized recommendations at this time. Please try again later."
                    error_label = QLabel(recommendations_text)
                    error_label.setWordWrap(True)
                    layout.addWidget(error_label)
                    dialog.exec()
                    return

                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_area.setStyleSheet("QScrollArea { border: none; }")
                scroll_content = QWidget()
                scroll_layout = QVBoxLayout(scroll_content)
                scroll_layout.setSpacing(10)

                dishes_data = []
                for line in recommendations_text.split('\n'):
                    if line.strip():
                        parts = {}
                        current_key = None
                        for item in line.split('|'):
                            if ':' in item:
                                key, value = item.split(':', 1)
                                current_key = key.strip()
                                parts[current_key] = value.strip()
                            elif current_key:
                                parts[current_key] += ' | ' + item.strip() # Handle cases where benefits might have '|'
                        if 'Dish Name' in parts and 'YouTube Link' in parts and 'Benefits' in parts:
                            dishes_data.append(parts)

                if not dishes_data:
                    no_data_label = QLabel("No recommendations could be parsed from the API response. Please try again.")
                    no_data_label.setWordWrap(True)
                    layout.addWidget(no_data_label)
                else:
                    meal_sections = {"Breakfast": [], "Dinner": []}
                    temp_breakfast = []
                    temp_dinner = []

                    for dish_info in dishes_data:
                        dish_name_lower = dish_info.get('Dish Name', '').lower()
                        if any(keyword in dish_name_lower for keyword in ['poha', 'upma', 'idli', 'dosa', 'paratha', 'oats', 'smoothie']) and len(temp_breakfast) < 2:
                            temp_breakfast.append(dish_info)
                        elif len(temp_dinner) < 2:
                            temp_dinner.append(dish_info)

                    idx = 0
                    while len(temp_breakfast) < 2 and idx < len(dishes_data):
                        if dishes_data[idx] not in temp_breakfast and dishes_data[idx] not in temp_dinner:
                            temp_breakfast.append(dishes_data[idx])
                        idx += 1
                    idx = 0
                    while len(temp_dinner) < 2 and idx < len(dishes_data):
                        if dishes_data[idx] not in temp_breakfast and dishes_data[idx] not in temp_dinner:
                            temp_dinner.append(dishes_data[idx])
                        idx += 1

                    meal_sections["Breakfast"] = temp_breakfast[:2]
                    meal_sections["Dinner"] = temp_dinner[:2]

                    for meal_type, dishes in meal_sections.items():
                        if not dishes: continue

                        meal_label = QLabel(f"{meal_type} Recommendations")
                        meal_label.setFont(QFont("Google Sans", 16, QFont.Weight.Medium))
                        scroll_layout.addWidget(meal_label)

                        for dish_info in dishes:
                            dish_name = dish_info.get('Dish Name', 'N/A')
                            link = dish_info.get('YouTube Link', '#')
                            benefits = dish_info.get('Benefits', 'No benefits information available.')

                            dish_frame = QFrame()
                            dish_frame_layout = QVBoxLayout(dish_frame)
                            dish_frame_layout.setContentsMargins(10, 10, 10, 10)

                            dish_header_layout = QHBoxLayout()
                            dish_name_label = QLabel(dish_name)
                            dish_name_label.setFont(QFont("Google Sans", 14, QFont.Weight.Medium))
                            dish_header_layout.addWidget(dish_name_label)
                            dish_header_layout.addStretch()

                            watch_button = QPushButton("Watch Recipe")
                            watch_button.setProperty("link", link)
                            watch_button.clicked.connect(lambda checked, l=link: webbrowser.open(l) if l != '#' else QMessageBox.information(self, "No Link", "Recipe link is not available."))
                            dish_header_layout.addWidget(watch_button)
                            dish_frame_layout.addLayout(dish_header_layout)

                            benefits_label = QLabel(benefits)
                            benefits_label.setWordWrap(True)
                            benefits_label.setStyleSheet("font-size: 11px; color: #555; margin-top: 5px; padding: 5px; background-color: #e9e9e9; border-radius: 4px;")
                            benefits_label.hide() # Initially hidden

                            why_button = QPushButton("Why this dish?")
                            why_button.setStyleSheet("""
                                background-color: #2196F3;
                                color: white;
                                border: none;
                                border-radius: 8px;
                                padding: 6px 10px;
                                font-size: 11px;
                                margin-top: 5px;
                            """)

                            # Use a lambda that captures the current benefits_label
                            why_button.clicked.connect(lambda checked, lbl=benefits_label: lbl.setVisible(not lbl.isVisible()))

                            dish_frame_layout.addWidget(why_button)
                            dish_frame_layout.addWidget(benefits_label)
                            scroll_layout.addWidget(dish_frame)

                scroll_area.setWidget(scroll_content)
                layout.addWidget(scroll_area)

                # Add disclaimer
                disclaimer = QLabel("<i>Disclaimer: Please consult your dietitian for professional advice. "
                                   "These recommendations are for informational purposes only and should not be consumed without professional guidance.</i>")
                disclaimer.setStyleSheet("color: #555; margin-top: 15px; font-size: 10px;")
                disclaimer.setWordWrap(True)
                disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(disclaimer)

            else:
                # Fall back to default implementation with a message
                msg_label = QLabel("Please complete your profile and health details to receive personalized food recommendations.")
                msg_label.setWordWrap(True)
                msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(msg_label)

            dialog.exec()

        except Exception as e:
            print(f"Error in show_food_recommendations: {e}")
            QMessageBox.warning(self, "Error", f"Failed to show recommendations: {str(e)}")

    def update_calories_burned(self):
        """Calculate and update calories burned based on current session data"""
        try:
            # Get current values
            heart_rate = esp_data.get("heart_rate", 0)
            body_temp = max(esp_data.get("body_temp_pre", 37.0), esp_data.get("body_temp_post", 37.0))
            strength_count = esp_data.get("steps", 0)
            
            # Only calculate if we have valid heart rate data and user input
            if heart_rate > 40 and self.weight_input.text():
                # Get user data
                weight = float(self.weight_input.text())
                height = float(self.height_input.text()) if self.height_input.text() else 170
                
                age = 19
                gender_factor = 1
                
                if "age" in self.calculate_bmi and self.calculate_bmi["age"]:
                    try:
                        age = int(self.calculate_bmi["age"])
                    except:
                        pass
                if "gender" in self.calculate_bmi and self.calculate_bmi["gender"]:
                    if self.calculate_bmi["gender"] == "Female":
                        gender_factor = 0  
 
                # Calculate BMI
                height_m = height / 100  # Convert cm to m
                bmi = weight / (height_m * height_m)
                
                # Initialize time tracking if not already done
                if not hasattr(self, 'last_calorie_update'):
                    self.last_calorie_update = time.time()
                    self.total_calories = 0
                
                current_time = time.time()
                minutes_elapsed = (current_time - self.last_calorie_update) / 60
                hours_elapsed = minutes_elapsed / 60
                
                # Use Keytel equation for heart-rate based calculation
                calories_hr = minutes_elapsed * ((0.2017 * age + 0.1988 * weight + 0.6309 * heart_rate - 55.0969) * gender_factor + 
                                               (0.074 * age + 0.1263 * weight + 0.4472 * heart_rate - 20.4022) * (1 - gender_factor)) / 4.184
                
                # IMPROVED: Dynamic MET value based on pose intensity and heart rate
                yoga_intensity = "moderate"  # Default
                if hasattr(self, 'current_pose_name') and self.current_pose_name:
                    # Determine intensity based on pose name
                    intense_poses = ["crow", "headstand", "handstand", "wheel", "side plank"]
                    light_poses = ["child", "corpse", "mountain", "easy", "seated"]
                    
                    if any(pose in self.current_pose_name.lower() for pose in intense_poses):
                        yoga_intensity = "intense"
                    elif any(pose in self.current_pose_name.lower() for pose in light_poses):
                        yoga_intensity = "light"
                
                # Adjust intensity based on heart rate
                if heart_rate > 120:
                    yoga_intensity = "intense"
                elif heart_rate < 80 and yoga_intensity != "light":
                    yoga_intensity = "moderate"
                    
                # Set MET value based on intensity
                met_values = {"light": 2.5, "moderate": 4.0, "intense": 6.0}
                yoga_met = met_values.get(yoga_intensity, 4.0)
                
                temp_adjustment = 1.0 + max(0, (body_temp - 37.0) * 0.13)
                
                # BMI adjustment
                if bmi < 18.5:
                    bmi_adjustment = 0.95  # Underweight
                elif bmi < 25:
                    bmi_adjustment = 1.0   # Normal weight
                elif bmi < 30:
                    bmi_adjustment = 1.05  # Overweight
                else:
                    bmi_adjustment = 1.1   # Obese
                    
                # Calculate MET-based calories
                calories_met = yoga_met * weight * hours_elapsed * temp_adjustment * bmi_adjustment
                
                # Average both methods for better accuracy
                calories = (calories_hr + calories_met) / 2
                
                # Add to total
                self.total_calories += calories
                
                # Update the calories display
                self.calories_card.update_value(f"{int(self.total_calories)}")
                
                # Update last update time
                self.last_calorie_update = current_time
                
        except Exception as e:
            print(f"Error calculating calories: {e}")

    def show_profile(self):
        """Show the user profile dialog"""
        self.profile_dialog = UserProfileDialog(self, self.calculate_bmi)
        self.profile_dialog.profile_updated.connect(self.on_profile_updated)
        # Make the dialog modal to prevent interaction with main window
        self.profile_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.profile_dialog.show()
        
    def on_profile_updated(self, profile_data):
        """Handle updated profile data"""
        self.calculate_bmi = profile_data
        
        # Update weight and height inputs if they exist
        if "weight" in profile_data and profile_data["weight"]:
            self.weight_input.setText(profile_data["weight"])
        
        if "height" in profile_data and profile_data["height"]:
            self.height_input.setText(profile_data["height"])
            
        # Calculate BMI if both weight and height are available
        self.calculate_bmi()
        
    def load_calculate_bmi(self):
        """Load user profile from file if it exists"""
        try:
            if os.path.exists("user_data/profile.json"):
                with open("user_data/profile.json", "r") as f:
                    self.calculate_bmi = json.load(f)
                    
                # Update weight and height inputs if they exist
                if "weight" in self.calculate_bmi and self.calculate_bmi["weight"]:
                    self.weight_input.setText(self.calculate_bmi["weight"])
                
                if "height" in self.calculate_bmi and self.calculate_bmi["height"]:
                    self.height_input.setText(self.calculate_bmi["height"])
                    
                # Load health conditions if they exist
                if "health_conditions" in self.calculate_bmi:
                    self.health_conditions = self.calculate_bmi["health_conditions"]
                    
                # Calculate BMI after loading data
                self.calculate_bmi_value()
        except Exception as e:
            print(f"Error loading user profile: {e}")
            
    def calculate_bmi_value(self):  
        """Calculate BMI based on weight and height"""
        try:
            if self.weight_input.text() and self.height_input.text():
                weight = float(self.weight_input.text())
                height = float(self.height_input.text()) / 100  # Convert cm to m
                
                if weight > 0 and height > 0:
                    bmi = weight / (height * height)
                    self.bmi_card.update_value(f"{bmi:.1f}")
                    
                    # Update BMI category
                    if bmi < 18.5:
                        self.bmi_card.update_category("Underweight", "#FF9800")  # Orange
                    elif bmi < 25:
                        self.bmi_card.update_category("Normal", "#4CAF50")  # Green
                    elif bmi < 30:
                        self.bmi_card.update_category("Overweight", "#FF5722")  # Deep Orange
                    else:
                        self.bmi_card.update_category("Obese", "#F44336")  # Red
                        
                    # Store BMI in the profile data
                    self.calculate_bmi["bmi"] = bmi
                    self.save_profile_data()
        except Exception as e:
            print(f"Error calculating BMI: {e}")

    def show_health_details(self):
        dialog = HealthDetailsDialog(self)
        if dialog.exec():
            self.health_conditions = dialog.get_health_conditions()
            # Save health conditions
            self.save_health_conditions()
            
    def save_profile_data(self):
        """Save all profile data including BMI and health conditions"""
        try:
            # Ensure user_data directory exists
            os.makedirs("user_data", exist_ok=True)
            
            # Update current weight and height
            if self.weight_input.text():
                self.calculate_bmi["weight"] = self.weight_input.text()
            if self.height_input.text():
                self.calculate_bmi["height"] = self.height_input.text()
                
            # Save to file
            with open("user_data/profile.json", "w") as f:
                json.dump(self.calculate_bmi, f)
        except Exception as e:
            print(f"Error saving profile data: {e}")

    def save_health_conditions(self):
        if hasattr(self, 'health_conditions'):
            try:
                # Ensure user_data directory exists
                os.makedirs("user_data", exist_ok=True)
                
                # Save health conditions to a separate file
                health_data = {
                    "health_conditions": self.health_conditions,
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open("user_data/health_details.json", "w") as f:
                    json.dump(health_data, f, indent=4)
                    
                # Also update the profile data
                self.calculate_bmi['health_conditions'] = self.health_conditions
                self.save_profile_data()
                
            except Exception as e:
                print(f"Error saving health conditions: {e}")
                
    def load_health_conditions(self):
        try:
            if os.path.exists("user_data/health_details.json"):
                with open("user_data/health_details.json", "r") as f:
                    health_data = json.load(f)
                    self.health_conditions = health_data.get("health_conditions", {})
        except Exception as e:
            print(f"Error loading health conditions: {e}")
