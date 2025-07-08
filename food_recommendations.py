import sys
import os
import re
import json
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QPixmap, QFont, QDesktopServices, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QGridLayout, QInputDialog
from PyQt6.QtCore import Qt, QUrl
from voice_assistant import VoiceAssistant
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
import google.generativeai as genai


# IndianFoodRecommendations class
class IndianFoodRecommendations(QWidget):
    def __init__(self, bmi=0, health_conditions=None):
        super().__init__()
        self.setWindowTitle("YogKalp - Indian Food Recommendations")
        self.setMinimumSize(800, 600)
        self.bmi = bmi
        self.health_conditions = health_conditions if health_conditions else []
        self.voice_assistant = VoiceAssistant()

        self.recommendations = self.get_gemini_recommendations()
        self.setup_ui()

    def get_gemini_recommendations(self):
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                # Fallback to a hardcoded key if the environment variable is not set
                api_key = "AIzaSyCF8eLRxip4jSRKKzdJxGABFLV_l3OwyZ4" 
                if api_key == "AIzaSyCF8eLRxip4jSRKKzdJxGABFLV_l3OwyZ4":
                    # Prompt user for API key if not set
                    api_key, ok = QInputDialog.getText(self, 'API Key Required', 'Enter your Gemini API Key:')
                    if not ok or not api_key:
                        return {"Error": "API Key is required to get recommendations."}

            genai.configure(api_key=api_key)

            model = genai.GenerativeModel('gemini-pro')

            bmi_category = ""
            if self.bmi < 18.5:
                bmi_category = "Underweight"
            elif self.bmi < 25:
                bmi_category = "Normal"
            elif self.bmi < 30:
                bmi_category = "Overweight"
            else:
                bmi_category = "Obese"

            prompt = (
                f"Based on a BMI of {self.bmi:.1f} ({bmi_category}) and considering the following health conditions: {', '.join(self.health_conditions) if self.health_conditions else 'None'}, "
                f"suggest 2 Indian breakfast and 2 Indian dinner dishes. "
                f"For each dish, provide the name, a brief description, its health benefits. "
                f"Format the output as a JSON object with 'Breakfast' and 'Dinner' as keys. Each key should have a list of dishes."
                f"Each dish object should have 'name', 'description' and 'benefits'."
            )

            response = model.generate_content(prompt)
            
            # Clean the response text
            clean_response = response.text.strip().replace('`', '')
            if clean_response.startswith('json'):
                clean_response = clean_response[4:]

            # Parse the JSON response
            recommendations = json.loads(clean_response)
            return recommendations

        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return {"Error": f"Failed to get recommendations: {e}"}

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Modern container with shadow
        main_container = QFrame()
        main_container.setObjectName("mainContainer")
        main_container.setStyleSheet("""
            #mainContainer {
                background-color: white;
                border-radius: 16px;
            }
        """)
        
        # Apply shadow effect
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 4)
        main_container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(24)
        
        # Header with gradient text
        header = QLabel("Personalized Food Recommendations")
        header.setFont(QFont("Google Sans", 28, QFont.Weight.Bold))
        header.setStyleSheet("""
            QLabel {
                color: #7E22CE;
                padding-bottom: 8px;
            }
        """)
        container_layout.addWidget(header)
        
        # BMI Status Card with color indicator
        bmi_status_card = QFrame()
        bmi_status_card.setObjectName("bmiCard")
        
        # Set card style based on BMI category
        bmi_category = ""
        bmi_color = ""
        if self.bmi < 18.5:
            bmi_category = "Underweight"
            bmi_color = "#3B82F6"  # Blue
        elif self.bmi < 25:
            bmi_category = "Normal"
            bmi_color = "#10B981"  # Green
        elif self.bmi < 30:
            bmi_category = "Overweight"
            bmi_color = "#F59E0B"  # Amber
        else:
            bmi_category = "Obese"
            bmi_color = "#EF4444"  # Red
            
        bmi_status_card.setStyleSheet(f"""
            #bmiCard {{
                background: linear-gradient(135deg, {bmi_color}15, {bmi_color}05);
                border: 1px solid {bmi_color}30;
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        bmi_layout = QHBoxLayout(bmi_status_card)
        
        bmi_info = QVBoxLayout()
        bmi_label = QLabel("Your BMI")
        bmi_label.setFont(QFont("Google Sans", 14))
        bmi_label.setStyleSheet("color: #6B7280;")
        
        bmi_value = QLabel(f"{self.bmi:.1f}")
        bmi_value.setFont(QFont("Google Sans", 32, QFont.Weight.Bold))
        bmi_value.setStyleSheet(f"color: {bmi_color};")
        
        bmi_info.addWidget(bmi_label)
        bmi_info.addWidget(bmi_value)
        bmi_layout.addLayout(bmi_info)
        
        bmi_layout.addStretch()
        
        bmi_category_layout = QVBoxLayout()
        category_label = QLabel("Category")
        category_label.setFont(QFont("Google Sans", 14))
        category_label.setStyleSheet("color: #6B7280;")
        
        category_value = QLabel(bmi_category)
        category_value.setFont(QFont("Google Sans", 20, QFont.Weight.Bold))
        category_value.setStyleSheet(f"color: {bmi_color};")
        
        bmi_category_layout.addWidget(category_label)
        bmi_category_layout.addWidget(category_value)
        bmi_layout.addLayout(bmi_category_layout)
        
        container_layout.addWidget(bmi_status_card)
        
        # Scroll area for recommendations
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
        
        # Get recommendations based on BMI
        recommendations = self.recommendations

        if "Error" in recommendations:
            error_label = QLabel(recommendations["Error"])
            error_label.setFont(QFont("Google Sans", 16, QFont.Weight.Bold))
            error_label.setStyleSheet("color: #EF4444;")
            error_label.setWordWrap(True)
            content_layout.addWidget(error_label)
        else:
            for category, items in recommendations.items():
                # Category header
                category_label = QLabel(category)
                category_label.setFont(QFont("Google Sans", 18, QFont.Weight.Bold))
                category_label.setStyleSheet("color: #1F2937; margin-top: 8px;")
                content_layout.addWidget(category_label)
            
            # Grid layout for food items (2 columns)
            items_grid = QGridLayout()
            items_grid.setSpacing(16)
            
            for i, item in enumerate(items):
                item_card = QFrame()
                item_card.setObjectName(f"itemCard{i}")
                item_card.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border: 1px solid #E5E7EB;
                        border-radius: 12px;
                    }
                    QFrame:hover {
                        border: 1px solid #D1D5DB;
                        background-color: #F9FAFB;
                    }
                """)
                
                # Apply subtle shadow
                card_shadow = QtWidgets.QGraphicsDropShadowEffect()
                card_shadow.setBlurRadius(12)
                card_shadow.setColor(QColor(0, 0, 0, 15))
                card_shadow.setOffset(0, 2)
                item_card.setGraphicsEffect(card_shadow)
                
                item_layout = QVBoxLayout(item_card)
                item_layout.setContentsMargins(20, 20, 20, 20)
                item_layout.setSpacing(12)
                
                # Name with icon
                name_layout = QHBoxLayout()
                name = QLabel(item['name'])
                name.setFont(QFont("Google Sans", 16, QFont.Weight.Bold))
                name.setStyleSheet("color: #111827;")
                name_layout.addWidget(name)
                name_layout.addStretch()
                
                # Add video link button with modern styling
                if 'video_link' in item:
                    video_btn = QPushButton("Watch Recipe")
                    video_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #EF4444;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 8px 16px;
                            font-size: 13px;
                            font-weight: 500;
                        }
                        QPushButton:hover {
                            background-color: #DC2626;
                        }
                    """)
                    video_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    video_btn.clicked.connect(lambda checked, url=item['video_link']: 
                        QDesktopServices.openUrl(QUrl(url)))
                    name_layout.addWidget(video_btn)
                
                item_layout.addLayout(name_layout)
                
                # Description with improved styling
                if 'description' in item:
                    desc = QLabel(item['description'])
                    desc.setWordWrap(True)
                    desc.setStyleSheet("color: #4B5563; font-size: 14px; line-height: 1.4;")
                    item_layout.addWidget(desc)
                
                # Benefits section with card styling
                if 'benefits' in item:
                    benefits_card = QFrame()
                    benefits_card.setStyleSheet("""
                        QFrame {
                            background-color: #F0FDF4;
                            border: 1px solid #DCFCE7;
                            border-radius: 8px;
                            padding: 8px;
                        }
                    """)
                    benefits_layout = QVBoxLayout(benefits_card)
                    benefits_layout.setContentsMargins(12, 12, 12, 12)
                    
                    benefits_title = QLabel("Health Benefits")
                    benefits_title.setFont(QFont("Google Sans", 13, QFont.Weight.Medium))
                    benefits_title.setStyleSheet("color: #166534;")
                    benefits_layout.addWidget(benefits_title)
                    
                    benefits_text = QLabel(item['benefits'])
                    benefits_text.setWordWrap(True)
                    benefits_text.setStyleSheet("color: #166534; font-size: 13px;")
                    benefits_layout.addWidget(benefits_text)
                    
                    item_layout.addWidget(benefits_card)
                
                # Add to grid - 2 columns
                row = i // 2
                col = i % 2
                items_grid.addWidget(item_card, row, col)
            
            content_layout.addLayout(items_grid)
        
        # Add nutrition tips card at the bottom
        tips_card = QFrame()
        tips_card.setStyleSheet("""
            QFrame {
                background: linear-gradient(135deg, #8B5CF6, #6366F1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        tips_layout = QVBoxLayout(tips_card)
        
        tips_title = QLabel("Nutrition Tips")
        tips_title.setFont(QFont("Google Sans", 18, QFont.Weight.Bold))
        tips_title.setStyleSheet("color: white;")
        tips_layout.addWidget(tips_title)
        
        # Tips based on BMI category
        tips_text = ""
        if self.bmi < 18.5:
            tips_text = "Focus on nutrient-dense foods. Include healthy fats like ghee, nuts, and seeds. Eat smaller, more frequent meals throughout the day."
        elif self.bmi < 25:
            tips_text = "Maintain your balanced diet. Include plenty of fruits, vegetables, whole grains, and lean proteins. Stay hydrated and limit processed foods."
        else:
            tips_text = "Focus on portion control. Choose high-fiber foods that keep you full longer. Increase protein intake and reduce refined carbohydrates."
            
        tips_content = QLabel(tips_text)
        tips_content.setWordWrap(True)
        tips_content.setFont(QFont("Google Sans", 14))
        tips_content.setStyleSheet("color: rgba(255, 255, 255, 0.9); line-height: 1.5;")
        tips_layout.addWidget(tips_content)
        
        content_layout.addWidget(tips_card)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        container_layout.addWidget(scroll)
        
        layout.addWidget(main_container)

    def get_recommendations(self):
        # This method is now replaced by get_gemini_recommendations
        pass
