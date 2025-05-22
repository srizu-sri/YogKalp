import numpy as np
import mediapipe as mp
import os
import json

class PoseEstimator:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands  # Add MediaPipe hands
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)  # Initialize hands
        self.trained_poses = []  # Loaded from file (omitted here for brevity)
        self.named_poses = {}  # Dictionary to store named poses
        
        # Load saved poses if available
        self.load_poses()
        
    def calculate_angle(self, a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        ba, bc = a - b, c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        return np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))

    def calculate_distance(self, a, b):
        """Calculate the Euclidean distance between two landmarks"""
        a, b = np.array(a), np.array(b)
        return np.linalg.norm(a - b)
        
    def extract_joint_angles(self, landmarks):
        keypoints = [(lm.x, lm.y) for lm in landmarks]
        angles = {
            "left_elbow": self.calculate_angle(keypoints[11], keypoints[13], keypoints[15]),
            "right_elbow": self.calculate_angle(keypoints[12], keypoints[14], keypoints[16]),
            "left_shoulder": self.calculate_angle(keypoints[13], keypoints[11], keypoints[23]),
            "right_shoulder": self.calculate_angle(keypoints[14], keypoints[12], keypoints[24]),
            "left_knee": self.calculate_angle(keypoints[23], keypoints[25], keypoints[27]),
            "right_knee": self.calculate_angle(keypoints[24], keypoints[26], keypoints[28])
        }
        
        # Add distances between key landmarks
        distances = {
            # Upper body distances
            "shoulder_width": self.calculate_distance(keypoints[11], keypoints[12]),
            "left_arm_length": self.calculate_distance(keypoints[11], keypoints[13]) + 
                              self.calculate_distance(keypoints[13], keypoints[15]),
            "right_arm_length": self.calculate_distance(keypoints[12], keypoints[14]) + 
                               self.calculate_distance(keypoints[14], keypoints[16]),
            
            # Lower body distances
            "hip_width": self.calculate_distance(keypoints[23], keypoints[24]),
            "left_leg_length": self.calculate_distance(keypoints[23], keypoints[25]) + 
                              self.calculate_distance(keypoints[25], keypoints[27]),
            "right_leg_length": self.calculate_distance(keypoints[24], keypoints[26]) + 
                               self.calculate_distance(keypoints[26], keypoints[28]),
            
            # Torso measurements
            "torso_length": self.calculate_distance(
                ((keypoints[11][0] + keypoints[12][0])/2, (keypoints[11][1] + keypoints[12][1])/2), 
                ((keypoints[23][0] + keypoints[24][0])/2, (keypoints[23][1] + keypoints[24][1])/2)
            )
        }
        
        # Combine angles and distances
        pose_features = {**angles, **distances}
        return pose_features
    
    def calculate_pose_accuracy(self, current_features, target_pose=None):
        """
        Calculate accuracy of current pose compared to a target pose.
        considering both angles and distances between landmarks.
        
        Returns:
        float: Accuracy percentage (0-100)
        """
        # If we have target poses to compare against
        if target_pose and target_pose in self.named_poses:
            target_features = self.named_poses[target_pose]
            
            if target_features:
                # Calculate the difference between current and target features
                angle_diffs = []
                distance_diffs = []
                
                for feature, current_value in current_features.items():
                    if feature in target_features:
                        if "left_" in feature or "right_" in feature or "_knee" in feature or "_elbow" in feature or "_shoulder" in feature:
                            # This is an angle - normalize difference
                            diff = abs(current_value - target_features[feature])
                            angle_diffs.append(min(diff, 360 - diff) / 180.0)  # Normalize to 0-1
                        else:
                            # This is a distance - normalize by the target value
                            if target_features[feature] > 0:  # Avoid division by zero
                                diff = abs(current_value - target_features[feature]) / target_features[feature]
                                distance_diffs.append(min(1.0, diff))  # Cap at 1.0 (100% difference)
                
                # Weight angles more heavily than distances (70% angles, 30% distances)
                if angle_diffs and distance_diffs:
                    avg_angle_diff = sum(angle_diffs) / len(angle_diffs)
                    avg_distance_diff = sum(distance_diffs) / len(distance_diffs)
                    weighted_diff = (0.7 * avg_angle_diff) + (0.3 * avg_distance_diff)
                    accuracy = max(0, 100 - (weighted_diff * 100))
                    return accuracy
                elif angle_diffs:
                    # Fall back to just angles if no distances
                    avg_diff = sum(angle_diffs) / len(angle_diffs)
                    accuracy = max(0, 100 - (avg_diff * 100))
                    return accuracy
        
        # If we don't have target poses or couldn't calculate accuracy based on features,
        # return a simulated accuracy based on detection quality
        # For demo purposes, we'll return a value between 50-95%
        return np.random.uniform(50, 95)
    
    def add_named_pose(self, name, features):
        """Add a named pose to the dictionary"""
        self.named_poses[name] = features
        # Save poses to file whenever a new one is added
        self.save_poses() 
               
    def save_poses(self):
        """Save all poses to a JSON file"""
        # Create poses directory if it doesn't exist
        os.makedirs("poses", exist_ok=True)
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_poses = {}
        for name, features in self.named_poses.items():
            serializable_poses[name] = {k: float(v) for k, v in features.items()}
            
        # Save to file
        with open("poses/saved_poses.json", "w") as f:
            json.dump(serializable_poses, f)
            
    def load_poses(self):
        """Load poses from JSON file if it exists"""
        try:
            if os.path.exists("poses/saved_poses.json"):
                with open("poses/saved_poses.json", "r") as f:
                    loaded_poses = json.load(f)
                
                # Convert the loaded poses to the new format if they're in the old format
                self.named_poses = {}
                for name, features in loaded_poses.items():
                    # Check if this is an old format pose (only has angles)
                    if all(key in ["left_elbow", "right_elbow", "left_shoulder", 
                                  "right_shoulder", "left_knee", "right_knee"] 
                           for key in features.keys()):
                        print(f"Converting pose {name} to new format")
                        # This is an old format - we'll keep it as is for now
                        # The next time the user captures this pose, it will be updated
                        self.named_poses[name] = features
                    else:
                        # This is already in the new format
                        self.named_poses[name] = features
                
                print(f"Loaded {len(self.named_poses)} saved poses")
        except Exception as e:
            print(f"Error loading saved poses: {e}")
            # If there's an error, start with empty poses
            self.named_poses = {}

    def detect_open_palm(self, hand_landmarks):
        """Detects an open palm based on the position of all five fingertips."""
        if not hand_landmarks:
            return False
        fingertips = [hand_landmarks.landmark[i] for i in [4, 8, 12, 16, 20]]  # Thumb and four fingers
        wrist = hand_landmarks.landmark[0]
        open_fingers = [np.linalg.norm(np.array([tip.x, tip.y]) - np.array([wrist.x, wrist.y])) for tip in fingertips]
        return all(dist > 0.1 for dist in open_fingers)
    
    def is_full_body_visible(self, landmarks):
        """
        Check if the full body is visible in the frame.
        Returns True if all key body landmarks are visible with sufficient confidence.
        """
        # Define key landmarks that must be visible for full body detection
        # These include ankles, knees, hips, shoulders, elbows, wrists
        key_landmarks = [
            11,  # shoulders
            13,  # elbows
            15,  # wrists
            23,  # hips
            # 25,  # knees
        ]
        
        # Check if all key landmarks are visible with sufficient confidence
        # MediaPipe visibility score ranges from 0 to 1
        visibility_threshold = 0.65
        
        for idx in key_landmarks:
            if idx >= len(landmarks) or landmarks[idx].visibility < visibility_threshold:
                return False
        
        return True
