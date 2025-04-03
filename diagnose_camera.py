#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_camera.py
Script to diagnose camera issues.
"""

import os
import sys
import cv2
import subprocess
import logging
import time
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_video_devices():
    """Check available video devices on Linux"""
    print("\n=== Checking Video Devices ===")
    if os.path.exists("/dev"):
        video_devices = [d for d in os.listdir("/dev") if d.startswith("video")]
        if video_devices:
            print(f"Found {len(video_devices)} video devices:")
            for device in sorted(video_devices):
                device_path = f"/dev/{device}"
                permissions = subprocess.run(
                    ["ls", "-l", device_path], 
                    capture_output=True, 
                    text=True
                ).stdout.strip()
                print(f"  {device_path} - {permissions}")
                
                # Check if current user has read/write access
                access = os.access(device_path, os.R_OK | os.W_OK)
                print(f"  Can access: {access}")
        else:
            print("No video devices found in /dev/")
    else:
        print("Cannot check video devices (not a Linux system or /dev not accessible)")

def test_webcam_capture(device_path, test_frames=3, save_image=True):
    """Test capturing from webcam"""
    print(f"\n=== Testing Webcam Capture ({device_path}) ===")
    
    # Try to interpret numeric device paths
    if device_path.isdigit():
        device_id = int(device_path)
    else:
        device_id = device_path
    
    # Try to open the camera
    cap = cv2.VideoCapture(device_id)
    
    if not cap.isOpened():
        print(f"ERROR: Could not open camera: {device_path}")
        return False
    
    print("Camera opened successfully")
    
    # Print camera properties
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Camera properties:")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps}")
    
    # Try to read frames
    success = False
    frame = None
    
    try:
        print(f"Attempting to read {test_frames} test frames...")
        for i in range(test_frames):
            ret, frame = cap.read()
            if not ret:
                print(f"  Frame {i+1}: Failed to read frame")
                break
            print(f"  Frame {i+1}: Successfully read frame of shape {frame.shape}")
            time.sleep(0.5)
            success = True
    except Exception as e:
        print(f"ERROR reading frames: {str(e)}")
    
    # Try to save a test image if we have a valid frame
    if success and save_image and frame is not None:
        test_dir = Path("./test_images")
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / f"test_camera_{int(time.time())}.jpg"
        print(f"Saving test image to: {test_file}")
        
        try:
            save_result = cv2.imwrite(str(test_file), frame)
            if save_result:
                print(f"Successfully saved test image: {test_file}")
                print(f"Image size: {os.path.getsize(test_file)} bytes")
            else:
                print(f"FAILED to save test image (cv2.imwrite returned False)")
        except Exception as e:
            print(f"ERROR saving test image: {str(e)}")
    
    # Release the camera
    cap.release()
    return success

def main():
    """Main diagnostic function"""
    print("=== Camera Diagnostics ===")
    print(f"Python version: {sys.version}")
    print(f"OpenCV version: {cv2.__version__}")
    
    # Check system camera devices
    check_video_devices()
    
    # Test default camera (device 0)
    test_webcam_capture("0")
    
    # Test first /dev/video device if available
    video_devices = [d for d in os.listdir("/dev") if d.startswith("video")]
    if video_devices:
        test_webcam_capture(f"/dev/{sorted(video_devices)[0]}")

if __name__ == "__main__":
    main()
