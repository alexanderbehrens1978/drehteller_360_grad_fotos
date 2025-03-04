#!/bin/bash

# Ensure script is run with bash
if [ -z "$BASH_VERSION" ]
then
    echo "Please run with bash"
    exit 1
fi

# Check for Python 3 and pip
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3."
    exit 1
fi

if ! command -v pip3 &> /dev/null
then
    echo "pip3 is not installed. Installing pip..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# System dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-opencv \
    fswebcam \
    v4l-utils \
    libatlas-base-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    gfortran \
    openexr \
    libopenexr-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv myenv

# Activate virtual environment
source myenv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Additional webcam and camera utilities
pip install v4l2

# Permissions for video devices
echo "Adding user to video group..."
sudo usermod -a -G video $USER

# Finished
echo "Installation complete!"
echo "Activate the virtual environment with: source myenv/bin/activate"
