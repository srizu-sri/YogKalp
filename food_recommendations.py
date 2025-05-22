import sys
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QPixmap, QFont, QDesktopServices
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
from PyQt6.QtCore import Qt, QUrl
from voice_assistant import VoiceAssistant
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget


# IndianFoodRecommendations class
class IndianFoodRecommendations(QWidget):
    def __init__(self, bmi=0):
        super().__init__()
        self.setWindowTitle("YogKalp - Indian Food Recommendations")
        self.setMinimumSize(800, 600)
        self.bmi = bmi
        self.voice_assistant = VoiceAssistant()

        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Personalized Indian Food Recommendations")
        header.setFont(QFont("Google Sans", 24, QFont.Weight.Medium))
        layout.addWidget(header)
        
        # BMI Status
        bmi_status = QLabel(f"Your BMI: {self.bmi:.1f}")
        bmi_status.setFont(QFont("Google Sans", 16))
        layout.addWidget(bmi_status)
        
        # scroll area for recommendations
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Get recommendations based on BMI
        recommendations = self.get_recommendations()

        for category, items in recommendations.items():
            category_frame = QFrame()
            category_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 10px;
                    padding: 10px;
                    margin: 5px;
                }
            """)
            category_layout = QVBoxLayout(category_frame)
            
            category_label = QLabel(category)
            category_label.setFont(QFont("Google Sans", 14, QFont.Weight.Medium))
            category_label.setStyleSheet("color: #1a73e8; padding: 5px;")
            category_layout.addWidget(category_label)
            
            # Food items
            for item in items:
                item_frame = QFrame()
                item_frame.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border-radius: 10px;
                        padding: 15px;
                        margin: 5px;
                    }
                    QFrame:hover {
                        background-color: #f1f3f4;
                    }
                """)
                
                item_layout = QVBoxLayout(item_frame)
                
                # Name and video link in horizontal layout
                name_layout = QHBoxLayout()
                name = QLabel(item['name'])
                name.setFont(QFont("Google Sans", 12, QFont.Weight.Medium))
                name_layout.addWidget(name)
                
                # Add video link button
                if 'video_link' in item:
                    video_btn = QPushButton("Watch Recipe")
                    video_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #FF0000;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 5px 10px;
                            font-size: 11px;
                        }
                        QPushButton:hover {
                            background-color: #CC0000;
                        }
                    """)
                    video_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    video_btn.clicked.connect(lambda checked, url=item['video_link']: 
                        QDesktopServices.openUrl(QUrl(url)))
                    name_layout.addWidget(video_btn)
                
                name_layout.addStretch()
                item_layout.addLayout(name_layout)
                
                # Add description
                if 'description' in item:
                    desc = QLabel(item['description'])
                    desc.setWordWrap(True)
                    desc.setStyleSheet("color: #5F6368; margin-top: 5px;")
                    item_layout.addWidget(desc)
                
                # Add benefits
                if 'benefits' in item:
                    benefits = QLabel(f"Benefits: {item['benefits']}")
                    benefits.setWordWrap(True)
                    benefits.setStyleSheet("color: #34A853; margin-top: 5px;")
                    item_layout.addWidget(benefits)
                
                category_layout.addWidget(item_frame)
            
            content_layout.addWidget(category_frame)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def get_recommendations(self):
        if self.bmi < 18.5:
            return {
                
                "High-Calorie Main Courses": [
                    {
                        "name": "Ghee Rice with Dal Makhani",
                        "description": "Rich in healthy fats and proteins. Made with clarified butter, lentils, and cream.",
                        "benefits": "High in calories, protein, and healthy fats. Helps in weight gain.",
                        "video_link": "https://youtu.be/sOlNWZbcn4M?si=Itaa8AAzFVgQ8Hvy"
                    },
                    {
                        "name": "Shahi Paneer",
                        "description": "Cottage cheese in rich cashew and cream gravy.",
                        "benefits": "Good source of protein and healthy fats.",
                        "video_link": "https://youtu.be/T9hQV22Uezw?si=PbCkLlqeX-pMQDTp"
                    }
                ],
                "Nutritious Snacks": [
                    {
                        "name": "Dry Fruit Ladoo",
                        "description": "Energy-dense balls made with nuts, dates, and ghee.",
                        "benefits": "Rich in healthy fats, proteins, and natural sugars.",
                        "video_link": "https://youtu.be/XehogIkn6TE?si=OEtRPC8R_XXprTNl"
                    },
                    {
                        "name": "Chikki",
                        "description": "Traditional Indian brittle made with jaggery and nuts.",
                        "benefits": "High in calories and essential nutrients.",
                        "video_link": "https://youtu.be/07bpHG1gu_8?si=iGHwTnegiMIyhwyI"
                    }
                ]
            }
        elif self.bmi < 25:
            return {
                "Balanced Main Courses": [
                    {
                        "name": "Dal Tadka with Brown Rice",
                        "description": "Yellow lentils tempered with spices, served with whole grain rice.",
                        "benefits": "Perfect balance of protein and complex carbohydrates.",
                        "video_link": "https://youtu.be/8c_scYUN5uc?si=C2iNprOEj3TvLrmL"
                    },
                    {
                        "name": "Tandoori Roti with Mixed Vegetable Curry",
                        "description": "Whole wheat flatbread with mixed vegetables in a tomato-based gravy.",
                        "benefits": "Rich in fiber and essential nutrients.",
                        "video_link": "https://youtu.be/5Ju3abQS5jY?si=oDqR_D0eIT35e0UH"
                    }
                ],
                "Healthy Snacks": [
                    {
                        "name": "Dhokla",
                        "description": "Steamed fermented rice and chickpea flour cake.",
                        "benefits": "Low in calories, high in protein and probiotics.",
                        "video_link": "https://youtu.be/Vu3HHOfK53A?si=RZjwolVJnXjzdJ_f"
                    },
                    {
                        "name": "Sprouts Bhel",
                        "description": "Mixed sprouts with vegetables and tangy chutneys.",
                        "benefits": "High in protein and fiber, low in calories.",
                        "video_link": "https://youtu.be/OB7tyagqguE?si=b-ntxjXcZb79L8Ti"
                    }
                ]
            }
        else:
            return {
                "Light Main Courses": [
                    {
                        "name": "Vegetable Daliya",
                        "description": "Broken wheat cooked with mixed vegetables and mild spices.",
                        "benefits": "High in fiber, low in calories, keeps you full longer.",
                        "video_link": "https://youtu.be/n4UyBHS1wsk?si=g4H5aWVxvD0TwytS"
                    },
                    {
                        "name": "Moong Dal Khichdi",
                        "description": "Light and digestible rice-lentil preparation with minimal oil.",
                        "benefits": "Easy to digest, protein-rich, low in calories.",
                        "video_link": "https://youtu.be/SYWtizV5oCI?si=ttuuCtebgKFbYQbN"
                    }
                ],
                "Healthy Alternatives": [
                    {
                        "name": "Ragi Dosa",
                        "description": "Crispy crepes made with finger millet flour.",
                        "benefits": "Rich in calcium and fiber, low in calories.",
                        "video_link": "https://youtu.be/I6DgNRcVN84?si=bsTTSc9ItE1pBIpW"
                    },
                    {
                        "name": "Oats Idli",
                        "description": "Steamed savory cakes made with oats and yogurt.",
                        "benefits": "High in fiber and protein, low in calories.",
                        "video_link": "https://youtu.be/OGVcPcfsUPA?si=peim-6cRQvIAvVmD"
                    }
                ]
            }
