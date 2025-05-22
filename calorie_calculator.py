class CalorieCalculator:
    def __init__(self):
        # MET values for different yoga intensities
        self.yoga_met_values = {
            "light": 2.5,       # Light/Hatha yoga
            "moderate": 3.5,    # Moderate/Vinyasa flow
            "intense": 4.5      # Power yoga/Ashtanga
        }
        
    def calculate_calories_from_heart_rate(self, heart_rate, weight_kg, age, gender, duration_minutes):
        """
        Calculate calories burned based on heart rate using the Keytel equation
        
        Parameters:
        - heart_rate: Average heart rate during exercise (BPM)
        - weight_kg: Weight in kilograms
        - age: Age in years
        - gender: 'male' or 'female'
        - duration_minutes: Exercise duration in minutes
        
        Returns:
        - Calories burned
        """
        if heart_rate < 40 or heart_rate > 220:
            return 0  # Invalid heart rate
            
        gender_factor = 1 if gender.lower() == 'male' else 0
        
        # Keytel equation (2005)
        calories = duration_minutes * ((0.2017 * age + 0.1988 * weight_kg + 0.6309 * heart_rate - 55.0969) * gender_factor + 
                                      (0.074 * age + 0.1263 * weight_kg + 0.4472 * heart_rate - 20.4022) * (1 - gender_factor)) / 4.184
        
        return max(0, calories)
    
    def calculate_calories_from_met(self, weight_kg, duration_hours, yoga_intensity="moderate", body_temp=37.0, bmi=22.0):
        """
        Calculate calories burned based on MET value, adjusted for body temperature and BMI
        
        Parameters:
        - weight_kg: Weight in kilograms
        - duration_hours: Exercise duration in hours
        - yoga_intensity: 'light', 'moderate', or 'intense'
        - body_temp: Body temperature in Celsius
        - bmi: Body Mass Index
        
        Returns:
        - Calories burned
        """
        # Get base MET value for the yoga intensity
        base_met = self.yoga_met_values.get(yoga_intensity.lower(), 3.0)
        
        # Adjust MET based on body temperature (higher temp = higher metabolism)
        # Normal body temp is ~37°C, each degree above increases metabolism by ~13%
        temp_adjustment = 1.0 + max(0, (body_temp - 37.0) * 0.13)
        
        # Adjust MET based on BMI (higher BMI = more effort for same activity)
        # Normal BMI is 18.5-24.9, we'll use 22 as baseline
        if bmi < 18.5:
            bmi_adjustment = 0.95  # Underweight: slightly less calories burned
        elif bmi < 25:
            bmi_adjustment = 1.0   # Normal weight
        elif bmi < 30:
            bmi_adjustment = 1.05  # Overweight: slightly more calories burned
        else:
            bmi_adjustment = 1.1   # Obese: more calories burned
            
        # Calculate adjusted MET
        adjusted_met = base_met * temp_adjustment * bmi_adjustment
        
        # Calculate calories: MET × weight (kg) × duration (hours)
        calories = adjusted_met * weight_kg * duration_hours
        
        return calories
    
    def get_yoga_intensity(self, pose_name):
        """
        Determine the intensity level of a yoga pose
        
        Parameters:
        - pose_name: Name of the yoga pose
        
        Returns:
        - Intensity level: 'light', 'moderate', or 'intense'
        """
        # Dictionary of common yoga poses and their intensities
        pose_intensities = {
            # Light intensity poses
            "mountain pose": "light",
            "child's pose": "light",
            "corpse pose": "light",
            "easy pose": "light",
            "seated forward bend": "light",
            
            # Moderate intensity poses
            "downward dog": "moderate",
            "warrior i": "moderate",
            "warrior ii": "moderate",
            "triangle pose": "moderate",
            "tree pose": "moderate",
            
            # High intensity poses
            "crow pose": "intense",
            "handstand": "intense",
            "headstand": "intense",
            "wheel pose": "intense",
            "side plank": "intense"
        }
        
        # Check if the pose is in our dictionary
        pose_lower = pose_name.lower()
        for pose_key, intensity in pose_intensities.items():
            if pose_key in pose_lower:
                return intensity
                
        # Default to moderate if pose not found
        return "moderate"
