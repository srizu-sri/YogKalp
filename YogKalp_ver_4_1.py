import sys
import asyncio
import uvicorn
import time
import json
import math
import numpy as np
import os
from PyQt6 import QtWidgets, QtGui, QtCore
from fastapi import FastAPI, WebSocket
from threading import Thread
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from functools import partial
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QGridLayout,
    QSizePolicy, QSpacerItem, QTabWidget, QComboBox, QCheckBox,
    QSlider, QFileDialog, QMessageBox, QGroupBox, QRadioButton,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QPixmap, QDesktopServices, QGuiApplication
import cv2
import mediapipe as mp
from datetime import datetime
import pyttsx3
import threading
import queue
import random
import requests
from bs4 import BeautifulSoup
# from pose_estimator import PoseEstimator
# from calorie_calculator import CalorieCalculator
# from camera_thread import CameraThread
# from esp32_camera import ESP32CameraReceiver
# from voice_assistant import VoiceAssistant
# from ui.components import MetricCard, ToggleSwitch
# from ui.food_recommendations import IndianFoodRecommendations
# from ui.profile_dialog import UserProfileDialog
# from yoga_assistant_1 import YogaAssistant
        
