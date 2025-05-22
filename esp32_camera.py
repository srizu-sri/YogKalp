import os
import cv2
import time



class ESP32CameraReceiver:
    def __init__(self, url=None):
        self.url = url if url else "http://192.168.64.89/stream"  # ESP32-CAM IP
        self.cap = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.connection_timeout = 3  # Timeout in seconds for connection attempts
        
    def connect(self):
        try:
            print(f"Connecting to ESP32-CAM at {self.url}")
            
            # Set a timeout for the connection attempt
            os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '1'  # Limit read attempts
            os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'timeout;3000|rtsp_transport;tcp'
            
            # Try to open the camera with a timeout
            self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
            
            # Check if connection was successful
            start_time = time.time()
            while time.time() - start_time < self.connection_timeout:
                self.connected = self.cap.isOpened()
                if self.connected:
                    # Try to read a frame to confirm connection
                    ret, _ = self.cap.read()
                    if ret:
                        self.reconnect_attempts = 0
                        print("Successfully connected to ESP32-CAM")
                        return True
                time.sleep(0.5)
            
            # If we get here, connection failed
            print("Failed to connect to ESP32-CAM - timeout")
            if self.cap:
                self.cap.release()
                self.cap = None
            self.connected = False
            self.reconnect_attempts += 1
            return False
            
        except Exception as e:
            print(f"Error connecting to ESP32-CAM: {e}")
            if self.cap:
                self.cap.release()
                self.cap = None
            self.connected = False
            self.reconnect_attempts += 1
            return False
            
    def read_frame(self):
        if not self.connected or not self.cap:
            if self.reconnect_attempts < self.max_reconnect_attempts:
                print(f"Attempting to reconnect to ESP32-CAM (attempt {self.reconnect_attempts+1}/{self.max_reconnect_attempts})")
                self.connect()
            return False, None
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame from ESP32-CAM")
                self.connected = False
                return False, None
            return ret, frame
        except Exception as e:
            print(f"Error reading frame from ESP32-CAM: {e}")
            self.connected = False
            return False, None
            
    def release(self):
        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                print(f"Error releasing ESP32-CAM connection: {e}")
        self.connected = False
        self.reconnect_attempts = 0
        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                print(f"Error releasing ESP32-CAM connection: {e}")
        self.connected = False
        self.reconnect_attempts = 0
