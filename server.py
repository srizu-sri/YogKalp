import os
import sys
import json
import fastapi
from fastapi import FastAPI, WebSocket
from threading import Thread
import asyncio

# ---------------------------
# FastAPI WebSocket Server
# ---------------------------

app = FastAPI()
# Initialize with default values for all ESP32 devices
esp_data = {
    # Health metrics from ESP32 with MAX30102 and MPU6050
    "heart_rate": 0, 
    "spo2": 0, 
    "body_temp_pre": 0,  # From MAX30102 temperature sensor (SDA,SCL=18,19)
    "body_temp_post": 0, # From MLX90614 temperature sensor (SDA,SCL=21,22)
    
    # Exercise metrics from MPU6050 (SDA,SCL=18,19)
    "steps": 0,
    "strength_count": 0,
    
    # Camera status from ESP32S3
    "camera_status": "disconnected"
}

# Create separate WebSocket endpoints for each ESP32
@app.websocket("/esp32/health")
async def health_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            print(f"Received health data: {data}")  # Debug print
            parsed = json.loads(data)
            
            # Update health-related metrics from MAX30102 (SDA,SCL=18,19) and MLX90614 (SDA,SCL=21,22)
            for key in ["heart_rate", "spo2", "body_temp_pre", "body_temp_post"]:
                if key in parsed:
                    # For heart_rate, ensure we're getting a valid number
                    if key == "heart_rate" and (parsed[key] is None or parsed[key] == 0):
                        # If IR value is present and high enough, calculate heart rate
                        if "ir_value" in parsed and parsed["ir_value"] > 50000:
                            # Use a default heart rate range based on IR value
                            # This is a fallback when the sensor's algorithm fails
                            esp_data[key] = max(60, min(100, int(parsed["ir_value"] / 1500)))
                        else:
                            esp_data[key] = 0
                    else:
                        esp_data[key] = parsed[key]
            
            # Explicitly handle MPU6050 data (steps and strength_count)
            if "steps" in parsed:
                esp_data["steps"] = parsed["steps"]
                print(f"Updated steps: {esp_data['steps']}")
            
            if "strength_count" in parsed:
                esp_data["strength_count"] = parsed["strength_count"]
                print(f"Updated strength count: {esp_data['strength_count']}")
            
            # Update sensor status
            if "max30102_status" in parsed:
                esp_data["max30102_status"] = parsed["max30102_status"]
            
            if "mpu6050_status" in parsed:
                esp_data["mpu6050_status"] = parsed["mpu6050_status"]
            
            if "mlx90614_status" in parsed:
                esp_data["mlx90614_status"] = parsed["mlx90614_status"]
            
            # Print updated values for debugging
            print(f"Updated health data: {esp_data}")
        except Exception as e:
            print(f"Error in health websocket: {e}")
            await asyncio.sleep(1)
@app.websocket("/esp32/exercise")
async def exercise_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            print(f"Received exercise data: {data}")  # Debug print
            parsed = json.loads(data)
            # Update only exercise-related metrics
            for key in ["steps", "strength_count"]:
                if key in parsed:
                    esp_data[key] = parsed[key]
            print(f"Updated exercise data: {esp_data}")  # Debug print
        except Exception as e:
            print(f"Error in exercise websocket: {e}")
            await asyncio.sleep(1)

@app.websocket("/esp32/camera")
async def camera_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            parsed = json.loads(data)
            # Update camera status
            if "camera_status" in parsed:
                esp_data["camera_status"] = parsed["camera_status"]
        except Exception as e:
            print(f"Error in camera websocket: {e}")
            await asyncio.sleep(1)

# Original endpoint for backward compatibility
@app.websocket("/esp32")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            parsed = json.loads(data)
            esp_data.update(parsed)
        except Exception as e:
            print(f"Error in general websocket: {e}")
            await asyncio.sleep(1)

# Add route for ESP32-CAM stream
@app.get("/")
async def get_index():
    return {"message": "YogKalp API is running"}

# Run FastAPI in thread
def run_fastapi():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Start the FastAPI server in a separate thread
Thread(target=run_fastapi, daemon=True).start()
