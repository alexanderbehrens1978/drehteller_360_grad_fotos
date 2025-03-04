import cv2
import os
import time
import subprocess
import warnings


def find_working_webcam(preferred_devices=None):
    """
    Find a working webcam device

    :param preferred_devices: List of device paths to try first
    :return: Working device path or None
    """
    # Prioritize video0 for Microsoft LifeCam HD-5000
    if preferred_devices is None:
        preferred_devices = ['/dev/video0', '/dev/video1']

    # First, try fswebcam to check device functionality
    for device in preferred_devices:
        try:
            # Use subprocess to run fswebcam test
            result = subprocess.run([
                'fswebcam',
                '-d', device,
                '--no-banner',
                '/dev/null'  # Discard output
            ], capture_output=True, text=True, timeout=3)

            # If fswebcam succeeds, return this device
            if result.returncode == 0:
                return device
        except subprocess.TimeoutExpired:
            continue
        except Exception:
            continue

    # Fallback to OpenCV detection
    for device in preferred_devices:
        try:
            # Try OpenCV capture
            cap = cv2.VideoCapture(device)
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                cap.release()
                return device
            cap.release()
        except Exception:
            pass

    # Comprehensive search if all else fails
    try:
        # Use v4l2-ctl to list all video devices
        result = subprocess.run(['v4l2-ctl', '--list-devices'],
                                capture_output=True,
                                text=True)

        # Extract all /dev/video* devices
        devices = [
            line.strip()
            for line in result.stdout.split('\n')
            if line.startswith('/dev/video')
        ]

        # Try each discovered device
        for device in devices:
            try:
                # Try fswebcam first
                result = subprocess.run([
                    'fswebcam',
                    '-d', device,
                    '--no-banner',
                    '/dev/null'
                ], capture_output=True, text=True, timeout=3)

                if result.returncode == 0:
                    return device

                # Fallback to OpenCV
                cap = cv2.VideoCapture(device)
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    cap.release()
                    return device
                cap.release()
            except Exception:
                continue
    except Exception:
        pass

    return None


def get_camera_capabilities(device_path):
    """
    Retrieve camera capabilities

    :param device_path: Path to the video device
    :return: Dictionary of camera capabilities
    """
    capabilities = {
        'supported_resolutions': [],
        'max_width': 0,
        'max_height': 0
    }

    try:
        # Use v4l2-ctl to get detailed device information
        result = subprocess.run([
            'v4l2-ctl',
            '-d', device_path,
            '--list-formats-ext'
        ], capture_output=True, text=True, timeout=3)

        # Parse output to extract resolutions
        resolutions = []
        for line in result.stdout.split('\n'):
            if 'Size' in line:
                try:
                    # Extract resolution like '640x480'
                    resolution = line.split(':')[-1].strip()
                    width, height = map(int, resolution.split('x'))
                    resolutions.append((width, height))

                    # Track max resolution
                    capabilities['max_width'] = max(capabilities['max_width'], width)
                    capabilities['max_height'] = max(capabilities['max_height'], height)
                except Exception:
                    pass

        capabilities['supported_resolutions'] = sorted(set(resolutions))
    except Exception as e:
        print(f"Error getting camera capabilities: {e}")

    return capabilities


def test_webcam_capture(device_path, width=None, height=None):
    """
    Attempt to capture an image from the specified device with optional resolution

    :param device_path: Path to the video device
    :param width: Optional desired width
    :param height: Optional desired height
    :return: Tuple (success, captured_image_path)
    """
    try:
        # Ensure output directory exists
        os.makedirs('static/photos', exist_ok=True)

        # Generate unique filename
        filename = f'webcam_test_{int(time.time())}.jpg'
        full_path = os.path.join('static/photos', filename)

        # Prepare fswebcam command
        cmd = ['fswebcam',
               '-d', device_path,
               '--no-banner']

        # Add resolution if specified
        if width and height:
            cmd.extend(['-r', f'{width}x{height}'])

        cmd.append(full_path)

        # Try fswebcam first
        subprocess.run(cmd, check=True, timeout=5)

        # Verify file was created
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            return True, full_path

        # Fallback to OpenCV with resolution
        cap = cv2.VideoCapture(device_path)

        # Set resolution if specified
        if width and height:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        ret, frame = cap.read()
        if ret:
            cv2.imwrite(full_path, frame)
            cap.release()
            return True, full_path
        cap.release()

        return False, None

    except subprocess.TimeoutExpired:
        print(f"Timeout capturing from {device_path}")
        return False, None
    except Exception as e:
        print(f"Webcam capture error: {e}")
        return False, None


# Standalone usage example
if __name__ == '__main__':
    # Find a working webcam
    working_device = find_working_webcam()

    if working_device:
        print(f"Found working webcam at: {working_device}")

        # Get camera capabilities
        capabilities = get_camera_capabilities(working_device)
        print("\nCamera Capabilities:")
        print(f"Supported Resolutions: {capabilities['supported_resolutions']}")
        print(f"Max Resolution: {capabilities['max_width']}x{capabilities['max_height']}")

        # Try capturing at a specific resolution
        success, image_path = test_webcam_capture(working_device, 1280, 720)

        if success:
            print(f"\nTest image captured: {image_path}")
        else:
            print("\nFailed to capture test image")
    else:
        print("No working webcam found")
