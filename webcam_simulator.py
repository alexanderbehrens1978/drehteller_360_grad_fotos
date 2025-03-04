import cv2
import os
import time
import random
import subprocess
import warnings
from datetime import datetime

from webcam_detection_helper import find_working_webcam, test_webcam_capture


class WebcamCaptureSimulator:
    def __init__(self, base_path='static/photos', sample_images_path='static/sample_images'):
        """
        Initialize webcam capture simulator

        :param base_path: Directory to save captured photos
        :param sample_images_path: Directory containing sample images to use
        """
        self.base_path = base_path
        self.sample_images_path = sample_images_path

        # Ensure base and sample image directories exist
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(sample_images_path, exist_ok=True)

        # Find the best webcam device
        self.camera_device = self._find_best_camera_device()

    def _find_best_camera_device(self, preferred_devices=None):
        """
        Find the best camera device to use

        :param preferred_devices: Optional list of preferred device paths
        :return: Best working device path
        """
        # If specific devices are known, try those first
        if preferred_devices is None:
            preferred_devices = ['/dev/video0', '/dev/video1']

        # Find a working webcam
        return find_working_webcam(preferred_devices)

    def capture_photo(self, filename=None):
        """
        Capture a photo - either from a real webcam or simulate with a sample image

        :param filename: Optional custom filename
        :return: Path to the saved image
        """
        # Ensure the base path exists
        os.makedirs(self.base_path, exist_ok=True)

        # If no filename provided, generate a unique one
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'webcam_photo_{timestamp}.jpg'

        # Ensure filename is just the basename
        filename = os.path.basename(filename)

        # Full path for the new image
        full_path = os.path.join(self.base_path, filename)

        # Try to capture from the detected camera device
        if self.camera_device:
            try:
                success, captured_path = test_webcam_capture(self.camera_device)
                if success:
                    # Copy the captured image to the desired filename
                    import shutil
                    shutil.copy(captured_path, full_path)
                    return full_path
            except Exception as e:
                print(f"Camera capture error: {e}")

        # Fallback to sample image simulation
        sample_images = [
            f for f in os.listdir(self.sample_images_path)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]

        if sample_images:
            # Randomly select a sample image
            selected_sample = random.choice(sample_images)
            sample_path = os.path.join(self.sample_images_path, selected_sample)

            # Copy the sample image to the photos directory
            import shutil
            shutil.copy(sample_path, full_path)
            return full_path

        # Last resort - create a blank image
        import numpy as np
        blank_image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank_image, "No Image Available", (50, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imwrite(full_path, blank_image)
        return full_path

    def list_photos(self):
        """
        List all photos in the base path

        :return: List of photo filenames
        """
        return [f for f in os.listdir(self.base_path)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))]


# Standalone usage example
if __name__ == '__main__':
    # Initialize the webcam capture simulator
    webcam_simulator = WebcamCaptureSimulator()

    # Capture 5 photos
    for i in range(5):
        captured_image = webcam_simulator.capture_photo()
        print(f"Captured image: {captured_image}")

    # List captured images
    print("\nCaptured Images:")
    for photo in webcam_simulator.list_photos():
        print(photo)
