def setup_profile_summary(self):
    
    self.name_label = QLabel("Name: Not set")
    self.name_label.setFont(QFont("Arial", 12))
    self.name_label.setStyleSheet("color: #333333; margin: 5px 0px;")  # Changed from white to dark
    
    self.age_label = QLabel("Age: Not set")
    self.age_label.setFont(QFont("Arial", 12))
    self.age_label.setStyleSheet("color: #333333; margin: 5px 0px;")  # Changed from white to dark
    
    self.bmi_label = QLabel("BMI: Not calculated")
    self.bmi_label.setFont(QFont("Arial", 12))
    self.bmi_label.setStyleSheet("color: #333333; margin: 5px 0px;")  # Changed from white to dark
