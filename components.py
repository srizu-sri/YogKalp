from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QObject, pyqtProperty # Add pyqtProperty
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPalette, QPixmap

class MetricCard(QFrame):
    def __init__(self, title, value="--", unit="", icon=None, color = None, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.unit = unit
        self.icon = icon
        self.category = ""
        self.category_color = color if color else "#5F6368"
        
        self.setup_ui()
        
    def setup_ui(self):
        # Set frame properties
        self.setObjectName(f"{self.title.lower().replace(' ', '_')}_card")
        self.setMinimumSize(180, 120)
        self.setMaximumSize(300, 150)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #DADCE0;
            }
        """)
        
        # Add shadow effect
        self.setGraphicsEffect(self.create_shadow_effect())
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        if self.icon:
            icon_label = QLabel()
            icon_label.setPixmap(self.icon.pixmap(QSize(20, 20)))
            title_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Value
        value_layout = QHBoxLayout()
        
        self.value_label = QLabel(str(self.value))
        self.value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_layout.addWidget(self.value_label)
        
        if self.unit:
            unit_label = QLabel(self.unit)
            unit_label.setFont(QFont("Arial", 12))
            unit_label.setStyleSheet("color: #5F6368;")
            value_layout.addWidget(unit_label)
            
        value_layout.addStretch()
        layout.addLayout(value_layout)
        
        # Category (initially empty)
        self.category_label = QLabel(self.category)
        self.category_label.setFont(QFont("Arial", 10))
        self.category_label.setStyleSheet(f"color: {self.category_color};")
        layout.addWidget(self.category_label)
        
    def update_value(self, value):
        self.value = value
        self.value_label.setText(str(value))
        
    def update_category(self, category, color):
        self.category = category
        self.category_color = color
        self.category_label.setText(category)
        self.category_label.setStyleSheet(f"color: {color};")
        
    def create_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        return shadow

class ToggleSwitch(QWidget):
    # Signal emitted when the switch is toggled
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set size
        self.setFixedSize(50, 25)
        
        # Initialize state
        self.is_checked = False
        self._handle_position = 0  # 0 = off, 1 = on
        
        # Animation properties
        self.animation = QPropertyAnimation(self, b"handle_position")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)  # 200ms
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw track
        track_color = QColor("#34A853") if self.is_checked else QColor("#DADCE0")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)
        
        # Draw handle
        handle_position = 4 + (self.width() - 29) * self._handle_position
        painter.setPen(QPen(QColor("#DADCE0")))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawEllipse(int(handle_position), 4, self.height() - 8, self.height() - 8)
        
    def mousePressEvent(self, event):
        self.toggle()
        event.accept()
        
    def toggle(self):
        self.is_checked = not self.is_checked
        
        # Animate handle position
        self.animation.setStartValue(self._handle_position)
        self.animation.setEndValue(1 if self.is_checked else 0)
        self.animation.start()
        
        # Emit signal
        self.toggled.emit(self.is_checked)
        
    def setChecked(self, checked):
        if self.is_checked != checked:
            self.is_checked = checked
            self._handle_position = 1 if checked else 0
            self.update()
            
    def isChecked(self):
        return self.is_checked

    @pyqtProperty(float) # Declare as a pyqtProperty of type float
    def handle_position(self):
        return self._handle_position
        
    @handle_position.setter
    def handle_position(self, pos):
        self._handle_position = pos
        self.update() # Trigger a repaint when the position changes
