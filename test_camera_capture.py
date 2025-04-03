#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_camera_capture.py
Tests the camera capture functionality directly with the configured camera
"""

import os
import sys
import json
import time
import cv2
import logging
from app.utils.config_manager import config_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_camera_capture():
    """Test the camera capture functionality with the configured camera"""
    
    # Read camera configuration
    camera_type = config_manager.get('camera.type', 'webcam')
    device_path = config_manager.get('camera.device_path', '/dev/video0')
    
    print(f"Testing camera capture with:")
    print(f"  Type: {camera_type}")
    print(f"  Device: {device_path}")
    
    # Create output directory
    output_dir = os.path.join(os.getcwd(), "test_images")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"camera_test_{int(time.time())}.jpg")
    
    if camera_type == 'webcam':
        success = capture_webcam(device_path, output_path)
    elif camera_type == 'gphoto2':
        success = capture_gphoto2(device_path, output_path)
    else:
        print(f"Unknown camera type: {camera_type}")
        return False
    
    if success:
        print(f"Successfully captured and saved image to: {output_path}")
        print(f"Image size: {os.path.getsize(output_path)} bytes")
        return True
    else:
        print("Failed to capture image")
        return False

def capture_webcam(device_path, output_path):
    """Capture an image from a webcam"""
    
    print(f"Opening webcam at {device_path}...")
    
    # For numbered device indices
    if device_path.isdigit():
        device_id = int(device_path)
    # For index from path like /dev/videoX
    elif device_path.startswith('/dev/video'):
        try:
            device_id = int(device_path.split('video')[1])
        except Exception:
            device_id = device_path
    else:
        device_id = device_path
    
    try:
        # Try opening with cv2.VideoCapture
        cap = cv2.VideoCapture(device_id)
        
        if not cap.isOpened():
            print(f"Error: Could not open camera at {device_path}")
            return False
        
        print("Camera opened successfully")
        print("Waiting for camera to adjust...")
        
        # Read multiple frames to let the camera adjust
        for i in range(5):
            ret, frame = cap.read()
            if not ret:
                print(f"Error: Failed to read frame {i+1}")
                cap.release()
                return False
            print(f"Read frame {i+1} successfully")
            time.sleep(0.5)
        
        # Capture the final frame for saving
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read final frame")
            cap.release()
            return False
        
        print(f"Got frame with shape: {frame.shape}")
        print(f"Saving image to {output_path}...")
        
        # Save the image
        result = cv2.imwrite(output_path, frame)
        if not result:
            print(f"Error: Failed to save image to {output_path}")
            cap.release()
            return False
        
        # Release the camera
        cap.release()
        return True
        
    except Exception as e:
        print(f"Exception during webcam capture: {str(e)}")
        return False

def capture_gphoto2(device_path, output_path):
    """Capture an image using gphoto2"""
    
    import subprocess
    
    try:
        # Check if gphoto2 is installed
        result = subprocess.run(['which', 'gphoto2'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            print("Error: gphoto2 is not installed")
            return False
        
        # Execute gphoto2 command to capture image
        print(f"Capturing image with gphoto2 from {device_path}...")
        
        cmd = [
            'gphoto2',
            '--capture-image-and-download',
            '--filename', output_path
        ]
        
        # Add port if specified
        if device_path and device_path != 'auto':
            cmd.extend(['--port', device_path])
        
        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"Error executing gphoto2: {result.stderr}")
            return False
        
        print(f"gphoto2 output: {result.stdout}")
        
        # Check if the file was created
        if os.path.exists(output_path):
            return True
        else:
            print(f"Error: Output file was not created at {output_path}")
            return False
            
    except Exception as e:
        print(f"Exception during gphoto2 capture: {str(e)}")
        return False

if __name__ == "__main__":
    test_camera_capture()
