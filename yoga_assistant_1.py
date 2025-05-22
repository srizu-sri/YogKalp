import os
import re
import sys
import threading
import time
import json
import webbrowser
from datetime import datetime
import pyttsx3
import speech_recognition as sr
import requests
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QScrollArea, QGroupBox, QTextEdit,
    QSizePolicy, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QGuiApplication

class WebSearchThread(QThread):
    """Thread for performing web searches without blocking the UI"""
    search_complete = pyqtSignal(str)
    
    def __init__(self, query):
        super().__init__()
        self.query = query
        
    def run(self):
        try:
            # Perform a web search
            result = self.search_web(self.query)
            self.search_complete.emit(result)
        except Exception as e:
            self.search_complete.emit(f"Sorry, I encountered an error while searching: {str(e)}")
    
    def search_web(self, query):
        """Search the web for information about the query using Google Custom Search API"""
        try:
            api_key = "AIzaSyCF8eLRxip4jSRKKzdJxGABFLV_l3OwyZ4"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

            prompt = f"""
            As a health and wellness expert, please provide accurate, concise information about the following query:

            Query: {query}

            Focus on providing factual information about:
            - Physical health and fitness
            - Mental wellbeing and mindfulness
            - Nutrition and diet
            - Exercise techniques and benefits
            - Yoga and meditation practices
            - General healthcare information
            - Wellness practices and lifestyle choices
            - General Knowledge and updates about Yoga
            Keep the response under one paragraph.
            Keep the response clear, informative, and focused on evidence-based information.
            If the query is about a medical condition, include a disclaimer that this is general information and not medical advice."""
            
            # Structure the request payload according to Gemini API requirements
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 800,
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Make the API request
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Extract the generated text from the response
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if parts and "text" in parts[0]:
                        result_text = parts[0]["text"]
                        
                        # Format the response
                        formatted_result = f"Here's what I found about '{query}':\n\n{result_text}"
                        return formatted_result
            
            # If we couldn't extract text from the response
            return self.fallback_answers(query)
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return self.fallback_answers(query)
   
    def process_search_results(self, query, items):
        """Process and clean search results to provide more relevant answers"""
        # Extract all snippets
        all_text = ""
        sources = []
        
        for item in items:
            title = item.get("title", "").replace(" - Yoga Journal", "").replace(" - Mayo Clinic", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            
            # Clean snippet (remove ellipses, extra spaces)
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            snippet = snippet.replace("...", "")
            
            all_text += snippet + " "
            sources.append({"title": title, "link": link})
        
        # Remove duplicate sentences and limit length
        sentences = re.split(r'(?<=[.!?])\s+', all_text)
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            # Skip very short sentences or those we've seen
            if len(sentence) < 10 or sentence.lower() in seen:
                continue
            unique_sentences.append(sentence)
            seen.add(sentence.lower())
        
        # Limit to most relevant sentences (first 5-7)
        final_text = " ".join(unique_sentences[:6])
        
        # Format the response
        formatted_results = f"Here's what I found about '{query}':\n\n"
        formatted_results += final_text + "\n\n"
        
        # Add sources
        formatted_results += "Sources:\n"
        for i, source in enumerate(sources, 1):
            if i > 3:  # Limit to 3 sources
                break
            formatted_results += f"{i}. {source['title']}\n   {source['link']}\n"
        
        return formatted_results
    
    def fallback_answers(self, query):
        """Provide fallback answers for common yoga questions"""
        query_lower = query.lower()
        
        # Dictionary of common yoga questions and answers
        yoga_qa = {
            "when was yoga invented": "Yoga has ancient origins dating back to over 5,000 years ago in Northern India. The word 'yoga' was first mentioned in the sacred texts known as the Rig Veda. The systematic development of yoga is often attributed to Patanjali, who compiled the Yoga Sutras around 400 CE, which outlined the eight limbs of yoga.",
            
            "benefits of yoga": "Yoga offers numerous benefits including: improved flexibility, increased muscle strength and tone, enhanced respiratory function, weight reduction, improved cardiovascular health, protection from injury, better posture, stress reduction, improved focus, and better sleep quality. Regular practice can also help manage chronic conditions like depression, pain, anxiety, and insomnia.",
            
            "types of yoga": "There are many types of yoga including: Hatha (basic poses), Vinyasa (flow yoga), Ashtanga (powerful yoga), Bikram (hot yoga), Iyengar (precise alignment), Kundalini (spiritual yoga), Yin (passive poses), Restorative (relaxing yoga), Power Yoga (fitness-based), and Prenatal Yoga (for expectant mothers). Each style offers different benefits and intensity levels.",
            
            "yoga poses for beginners": "Good yoga poses for beginners include: Mountain Pose (Tadasana), Child's Pose (Balasana), Downward-Facing Dog (Adho Mukha Svanasana), Tree Pose (Vrikshasana), Warrior I (Virabhadrasana I), Warrior II (Virabhadrasana II), Triangle Pose (Trikonasana), Bridge Pose (Setu Bandha Sarvangasana), and Corpse Pose (Savasana). Start slowly and focus on proper alignment.",
            
            "yoga breathing": "Pranayama refers to breathing exercises in yoga that control the breath. Common techniques include: Ujjayi (Victorious Breath), Nadi Shodhana (Alternate Nostril Breathing), Kapalabhati (Skull Shining Breath), Bhramari (Bee Breath), and Dirga (Three-Part Breath). These techniques can calm the mind, reduce stress, increase oxygen intake, and prepare the body for meditation.",
            
            "yoga meditation": "Meditation is a key component of yoga practice. It involves focusing the mind and eliminating the stream of thoughts. Yoga meditation techniques include: Trataka (focused gazing), Yoga Nidra (yogic sleep), Chakra meditation (focusing on energy centers), Mantra meditation (repeating sacred sounds), and Mindfulness meditation (present moment awareness)."
        }
        
        # Check if the query matches any of our predefined questions
        for key, answer in yoga_qa.items():
            if key in query_lower or any(word in query_lower for word in key.split()):
                return f"Here's what I found about '{query}':\n\n{answer}"
        
        # If no match, provide a generic response about yoga
        return f"I couldn't find specific information about '{query}', but I can tell you that yoga is an ancient practice originating in India that combines physical postures, breathing techniques, and meditation. It promotes physical and mental wellbeing. Would you like to know about the benefits of yoga, different yoga styles, or beginner poses instead?"

    def format_health_response(self, query, response_text):
        """Format the response with appropriate disclaimers for health topics"""
        formatted_result = f"Here's what I found about '{query}':\n\n{response_text}"
        
        # Add disclaimer for medical topics
        medical_keywords = ["disease", "condition", "syndrome", "disorder", "treatment", 
                        "medication", "symptom", "diagnosis", "cure", "therapy"]
        
        if any(keyword in query.lower() for keyword in medical_keywords):
            formatted_result += "\n\n**Important Disclaimer**: This information is for educational purposes only and is not intended as medical advice. Please consult with a qualified healthcare provider for diagnosis and treatment of any medical conditions."
        
        return formatted_result

    def detect_topic(self, query):
        """Detect the general topic of a query"""
        query_lower = query.lower()
        
        topics = {
            "yoga": ["yoga", "pose", "asana", "stretch", "flexibility"],
            "nutrition": ["food", "diet", "nutrition", "eat", "meal", "vitamin", "mineral"],
            "fitness": ["exercise", "workout", "fitness", "cardio", "strength", "training"],
            "mental_health": ["stress", "anxiety", "depression", "mental", "mindful", "meditation"],
            "sleep": ["sleep", "insomnia", "rest", "tired", "fatigue", "bed"],
            "weight": ["weight", "fat", "slim", "calorie", "metabolism"]
        }
        
        for topic, keywords in topics.items():
            if any(keyword in query_lower for keyword in keywords):
                return topic
        
        return "general_health"

class SpeechRecognitionThread(QThread):
    """Thread for speech recognition without blocking the UI"""
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_ended = pyqtSignal()
    
    def run(self):
        recognizer = sr.Recognizer()
        
        # Emit signal that we've started listening
        self.listening_started.emit()
        
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            # Emit signal that we've stopped listening
            self.listening_ended.emit()
            
            try:
                # Recognize speech using Google Speech Recognition
                text = recognizer.recognize_google(audio)
                self.text_recognized.emit(text)
            except sr.UnknownValueError:
                self.error_occurred.emit("Sorry, I couldn't understand what you said.")
            except sr.RequestError:
                self.error_occurred.emit("Sorry, I couldn't request results from the speech recognition service.")
                
        except Exception as e:
            self.listening_ended.emit()
            self.error_occurred.emit(f"An error occurred: {str(e)}")

class TextToSpeechThread(QThread):
    """Thread for text-to-speech without blocking the UI"""
    speech_complete = pyqtSignal()
    
    def __init__(self, text):
        super().__init__()
        self.text = text
        
    def run(self):
        try:
            engine = pyttsx3.init()
            engine.say(self.text)
            engine.runAndWait()
            self.speech_complete.emit()
        except Exception as e:
            print(f"TTS Error: {e}")
            self.speech_complete.emit()

class YogaAssistant(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yoga Assistant")
        self.setMinimumSize(400, 400)
        
        # Set up the UI
        self.setup_ui()
        
        # Initialize TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_thread = None
        
        # Initialize speech recognition
        self.speech_thread = None
        
        # Initialize web search thread
        self.search_thread = None
        
        # Center the window
        self.center()
        
    def setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header with logo
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1a73e8; border-radius: 10px;")
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("Yoga Assistant")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        main_layout.addWidget(header_frame)
        
        # Description
        desc_label = QLabel("Ask me anything about yoga, health, or fitness!")
        desc_label.setFont(QFont("Arial", 12))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(desc_label)
        
        # Response area (scrollable)
        self.response_area = QScrollArea()
        self.response_area.setWidgetResizable(True)
        self.response_area.setMinimumHeight(400)
        self.response_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #DADCE0;
                border-radius: 10px;
                background-color: white;
            }
        """)
        
        response_widget = QWidget()
        response_layout = QVBoxLayout(response_widget)
        
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        self.response_text.setFont(QFont("Arial", 11))
        self.response_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: white;
            }
        """)
        self.response_text.setText("How can I help you today?")
        
        response_layout.addWidget(self.response_text)
        
        self.response_area.setWidget(response_widget)
        main_layout.addWidget(self.response_area)
        
        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #DADCE0;
                border-radius: 24px;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 5, 10, 5)
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Type your question here...")
        self.query_input.setFont(QFont("Arial", 11))
        self.query_input.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 8px;
            }
        """)
        self.query_input.returnPressed.connect(self.process_query)
        
        # Microphone button
        self.mic_button = QPushButton()
        self.mic_button.setIcon(QIcon("icons/mic.png"))  # Make sure to have this icon
        self.mic_button.setIconSize(QSize(24, 24))
        self.mic_button.setFixedSize(40, 40)
        self.mic_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
        """)
        self.mic_button.clicked.connect(self.start_voice_recognition)
        
        # Send button
        self.send_button = QPushButton("Ask")
        self.send_button.setFont(QFont("Arial", 11))
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border-radius: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1765cc;
            }
        """)
        self.send_button.clicked.connect(self.process_query)
        
        input_layout.addWidget(self.query_input)
        input_layout.addWidget(self.mic_button)
        input_layout.addWidget(self.send_button)
        
        main_layout.addWidget(input_frame)
        
        # Status bar for showing listening status
        self.status_bar = QLabel("")
        font = QFont("Arial", 10)
        font.setItalic(True)
        self.status_bar.setFont(font)
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_bar.setStyleSheet("color: #1a73e8;")
        main_layout.addWidget(self.status_bar)
        
        self.setCentralWidget(main_widget)
    
    def process_query(self):
        query = self.query_input.text().strip()
        if not query:
            return
        
        # Clear input field
        self.query_input.clear()
        
        # Update UI to show the query
        self.response_text.setText(f"You asked: {query}\n\nSearching for an answer...")
        
        # Start web search in a separate thread
        self.search_thread = WebSearchThread(query)
        self.search_thread.search_complete.connect(self.handle_search_result)
        self.search_thread.start()
    
    def handle_search_result(self, result):
        # Update UI with the search result
        self.response_text.setText(result)
        
        # Speak the result (first 100 words or so)
        words = result.split()
        speak_text = " ".join(words[:100])  # Limit to first 100 words
        
        # Clean up the text for speech
        speak_text = re.sub(r'http\S+', 'website link', speak_text)  # Replace URLs
        speak_text = re.sub(r'\s+', ' ', speak_text).strip()  # Remove extra whitespace
        
        self.speak_text(speak_text)
    
    def start_voice_recognition(self):
        if self.speech_thread and self.speech_thread.isRunning():
            return  # Already listening
        
        self.speech_thread = SpeechRecognitionThread()
        self.speech_thread.text_recognized.connect(self.handle_recognized_text)
        self.speech_thread.error_occurred.connect(self.handle_recognition_error)
        self.speech_thread.listening_started.connect(self.handle_listening_started)
        self.speech_thread.listening_ended.connect(self.handle_listening_ended)
        self.speech_thread.start()
    
    def handle_recognized_text(self, text):
        self.query_input.setText(text)
        self.process_query()
    
    def handle_recognition_error(self, error_message):
        self.status_bar.setText("")
        self.response_text.setText(error_message)
        self.speak_text(error_message)
    
    def handle_listening_started(self):
        self.status_bar.setText("Listening... Speak now")
        self.mic_button.setEnabled(False)
    
    def handle_listening_ended(self):
        self.status_bar.setText("")
        self.mic_button.setEnabled(True)
    
    def speak_text(self, text):
        if self.tts_thread and self.tts_thread.isRunning():
            return  # Already speaking
        
        self.tts_thread = TextToSpeechThread(text)
        self.tts_thread.speech_complete.connect(self.handle_speech_complete)
        self.tts_thread.start()
    
    def handle_speech_complete(self):
        pass  # Could add UI updates when speech is complete
    
    def center(self):
        """Center the window on the screen"""
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())