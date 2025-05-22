import os
import cv2
from datetime import datetime
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame 
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QThread
import time
import mediapipe as mp
from esp32_camera import ESP32CameraReceiver

class CameraThread(QThread):
    # Define signals for thread-safe communication
    training_count_updated = pyqtSignal(int)
    accuracy_updated = pyqtSignal(float, str)
    model_updated = pyqtSignal()
    pose_count_updated = pyqtSignal(int)  # New signal for pose count
    camera_error = pyqtSignal(str)
    def __init__(self, pose_estimator):
        super().__init__()
        self.estimator = pose_estimator
        self.running = False
        self.training_images_count = 0
        # Initialize poses_trained based on loaded poses
        self.poses_trained = len(self.estimator.named_poses)
        self.current_pose_name = ""
        self.current_batch = []  # Current batch of pose angles
        self.palm_detected_time = None
        self.image_captured = False
        self.timer_active = False  # Flag to track if timer is active
        self.palm_detection_enabled = True  # Flag to enable/disable palm detection
        self.use_esp32_cam = False  # Flag to use ESP32-CAM instead of local camera
        self.esp32_cam = ESP32CameraReceiver()
        # Counters for voice feedback
        self.low_accuracy_feedback_count = 0
        self.medium_accuracy_feedback_count = 0
        self.last_accuracy_level = "high"  # Track the last accuracy level
        
    def set_pose_name(self, name):
        self.current_pose_name = name
        
    def save_current_batch(self, name):
        """Average the angles in the current batch and save as a named pose"""
        if self.current_batch:
            # Calculate average angles for each joint
            avg_angles = {}
            for key in self.current_batch[0].keys():
                avg_angles[key] = sum(batch[key] for batch in self.current_batch) / len(self.current_batch)
            
            # Save to estimator
            self.estimator.add_named_pose(name, avg_angles)
            # Reset batch
            self.current_batch = []
            
            # Update poses trained count
            self.poses_trained += 1
            self.pose_count_updated.emit(self.poses_trained)
            
            # Emit signal that model was updated
            self.model_updated.emit()
        
    def set_palm_detection_enabled(self, enabled):
        """Enable or disable palm detection feature"""
        self.palm_detection_enabled = enabled
    
    def set_esp32_cam_enabled(self, enabled, url=None):
        
        """Enable or disable ESP32-CAM stream"""
        self.use_esp32_cam = enabled
        if url:
            self.esp32_cam.url = url       
            
    def run(self):
        self.running = True
        
        # Create training images directory if it doesn't exist
        training_dir = "training_images"
        os.makedirs(training_dir, exist_ok=True)
        
        # Initialize camera source
        cap = None
        
        # Create modern-looking window
        cv2.namedWindow("Yoga Pose Analysis", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Yoga Pose Analysis", 640, 480)
        
        while self.running:
            # Try to initialize or check camera if not already done
            if self.use_esp32_cam and (not hasattr(self, 'esp32_cam_initialized') or not self.esp32_cam_initialized):
                # Try to connect to ESP32-CAM
                print("Attempting to connect to YogKalp-CAM...")
                if not self.esp32_cam.connect():
                    print("Failed to connect to YogKalp-CAM, falling back to local camera")
                    # Emit signal for camera error
                    self.camera_error.emit("YogKalp-CAM not available. Falling back to local camera.")
                    
                    # Try to use local camera instead
                    if cap is None or not cap.isOpened():
                        cap = cv2.VideoCapture(0)
                        if not cap.isOpened():
                            self.camera_error.emit("Local camera also not available. Please check your camera connections.")
                            time.sleep(2)  # Wait before retrying
                            continue
                    self.use_esp32_cam = False
                else:
                    print(f"Connected to YogKalp-CAM at {self.esp32_cam.url}")
                    self.esp32_cam_initialized = True
            elif not self.use_esp32_cam and (cap is None or not cap.isOpened()):
                # Initialize local camera if not already done
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    self.camera_error.emit("Local camera not available. Please check your camera connection.")
                    time.sleep(2)  # Wait before retrying
                    continue
            
            # Get frame from appropriate source
            if self.use_esp32_cam:
                ret, frame = self.esp32_cam.read_frame()
                if not ret:
                    print("Failed to get frame from YogKalp-CAM")
                    # Reset connection flag to force reconnection attempt
                    self.esp32_cam_initialized = False
                    time.sleep(1)
                    continue
            else:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to get frame from local camera")
                    # Reset cap to force reconnection
                    if cap is not None:
                        cap.release()
                    cap = None
                    time.sleep(1)
                    continue
            
            # Process image for pose detection
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results_pose = self.estimator.pose.process(image)
            
            # Process image for hand detection (for gesture control)
            results_hands = self.estimator.hands.process(image)
            
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Add fancy header
            cv2.rectangle(image, (0, 0), (image.shape[1], 60), (26, 115, 232), -1)
            cv2.putText(image, "Yoga Pose Analysis", (20, 40), 
                         cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        
            # Add camera source indicator
            source_text = "ESP32-CAM" if self.use_esp32_cam else "Local Camera"
            cv2.putText(image, f"Source: {source_text}", (image.shape[1]-250, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (26, 115, 232), 2)
            
            # Add training images count
            cv2.putText(image, f"Training Images: {self.training_images_count}", 
                        (image.shape[1] - 250, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add instructions for training image capture
            instruction_text = "Press 'T' to capture training image"
            if self.palm_detection_enabled:
                instruction_text += " or show open palm to start 5s timer"
            
            cv2.putText(image, instruction_text, 
                        (20, image.shape[0] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (26, 115, 232), 2)
            
            # Check for open palm gesture - only if timer is not already active AND palm detection is enabled
            if not self.timer_active and self.palm_detection_enabled and results_hands and results_hands.multi_hand_landmarks:
                for hand_landmarks in results_hands.multi_hand_landmarks:
                    if self.estimator.detect_open_palm(hand_landmarks):
                        # Start the timer but don't save the frame yet
                        self.palm_detected_time = time.time()
                        self.image_captured = False
                        self.timer_active = True  # Set timer as active
                        break
            
            # If timer is active, show countdown regardless of hand presence
            if self.timer_active and self.palm_detected_time is not None:
                elapsed = time.time() - self.palm_detected_time
                if elapsed < 5:
                    # Draw a countdown timer on screen
                    cv2.putText(image, f"Capturing in: {5-int(elapsed)}s", 
                                (image.shape[1]//2 - 100, image.shape[0]//2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    # Timer completed, capture the CURRENT frame instead of the initial one
                    if not self.image_captured and results_pose.pose_landmarks:
                        # Save the current frame instead of the initial one
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{training_dir}/training_pose_{timestamp}.jpg"
                        cv2.imwrite(filename, frame)  # Using current frame
                        self.training_images_count += 1
                        
                        # Extract angles and add to batch
                        angles = self.estimator.extract_joint_angles(results_pose.pose_landmarks.landmark)
                        self.current_batch.append(angles)
                        
                        # Emit signal that training count was updated
                        self.training_count_updated.emit(self.training_images_count)
                        
                        # Show feedback that image was saved
                        save_feedback = frame.copy()  # Using current frame for feedback
                        cv2.putText(save_feedback, "Image Saved!", (frame.shape[1]//2 - 100, frame.shape[0]//2), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                        cv2.imshow("Yoga Pose Analysis", save_feedback)
                        cv2.waitKey(500)  # Show feedback for half a second
                        
                        self.image_captured = True
                    
                    # Reset timer state
                    self.palm_detected_time = None
                    self.timer_active = False  # Reset timer active flag
            
            # In the CameraThread's run method, update the pose detection logic
            # Find the section where it processes pose landmarks and emits accuracy

            # Draw pose landmarks with custom style
            if results_pose.pose_landmarks:
                mp_drawing = mp.solutions.drawing_utils
                mp_drawing_styles = mp.solutions.drawing_styles
                
                # Extract joint angles
                angles = self.estimator.extract_joint_angles(results_pose.pose_landmarks.landmark)
                
                # Check if full body is visible before calculating accuracy
                full_body_visible = self.estimator.is_full_body_visible(results_pose.pose_landmarks.landmark)
                
                # Find the best matching pose from all trained poses
                best_pose = None
                best_accuracy = 0
                
                # Only proceed with pose matching if full body is visible
                if full_body_visible:
                    for pose_name, pose_angles in self.estimator.named_poses.items():
                        # Calculate accuracy for this pose
                        accuracy = self.estimator.calculate_pose_accuracy(angles, pose_name)
                        
                        # If this is the best match so far, update
                        if accuracy > best_accuracy:
                            best_accuracy = accuracy
                            best_pose = pose_name
                    
                    # If we found a good match, emit the signal with the best pose
                    if best_pose and best_accuracy > 40:  # Threshold to avoid false positives
                        self.accuracy_updated.emit(best_accuracy, best_pose)
                
                # Draw skeleton in Google blue color
                mp_drawing.draw_landmarks(
                    image, 
                    results_pose.pose_landmarks, 
                    self.estimator.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing.DrawingSpec(color=(232, 115, 26), thickness=2, circle_radius=2),
                    connection_drawing_spec=mp_drawing.DrawingSpec(color=(26, 115, 232), thickness=2)
                )
                
                # Add accuracy text to the frame if we have enough training images and full body is visible
                if self.training_images_count >= 5 and self.current_pose_name and full_body_visible:
                    # Calculate accuracy for current pose
                    accuracy = self.estimator.calculate_pose_accuracy(angles, self.current_pose_name)
                    
                    # Color-coded accuracy display
                    if accuracy > 80:
                        color = (0, 255, 0)  # Green for high accuracy
                    elif accuracy > 60:
                        color = (0, 255, 255)  # Yellow for medium accuracy
                    else:
                        color = (0, 0, 255)  # Red for low accuracy
                        
                    cv2.putText(image, f"{self.current_pose_name} Accuracy: {accuracy:.1f}%", 
                                (20, image.shape[0] - 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                elif not full_body_visible:
                    # Display a message when full body is not visible
                    cv2.putText(image, "Please show full body for pose detection", 
                                (20, image.shape[0] - 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                else:
                    # Display a message when full body is not visible
                    cv2.putText(image, "Please show full body for pose detection", 
                                (20, image.shape[0] - 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Display the image
            cv2.imshow("Yoga Pose Analysis", image)
            
            # Initialize key variable before using it
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('t'):
                # Save training image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{training_dir}/training_pose_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                self.training_images_count += 1
                
                # If we have pose landmarks, add them to the current batch
                if results_pose.pose_landmarks:
                    angles = self.estimator.extract_joint_angles(results_pose.pose_landmarks.landmark)
                    self.current_batch.append(angles)
                
                # Emit signal that training count was updated
                self.training_count_updated.emit(self.training_images_count)
                
                # Show feedback that image was saved
                save_feedback = frame.copy()
                cv2.putText(save_feedback, "Image Saved!", (frame.shape[1]//2 - 100, frame.shape[0]//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                cv2.imshow("Yoga Pose Analysis", save_feedback)
                cv2.waitKey(500)  # Show feedback for half a second
        
        # Clean up resources
        if self.use_esp32_cam:
            self.esp32_cam.release()
        elif cap is not None:
            cap.release()
            
        cv2.destroyAllWindows()
        self.running = False
                
    def stop(self):
        self.running = False
