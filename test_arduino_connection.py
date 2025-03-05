#!/usr/bin/env python3
# test_arduino_connection.py - Simple script to test Arduino connection

import os
import sys
import time
import serial
from serial.tools import list_ports

def find_arduino_ports():
    """Find all potential Arduino ports"""
    arduino_ports = []
    
    for port in list_ports.comports():
        # Arduino typically shows up with Arduino in description or ACM in port name
        if "Arduino" in port.description or "ACM" in port.device:
            arduino_ports.append({
                'port': port.device,
                'description': port.description
            })
        # Also add USB Serial ports as possible Arduino devices
        elif "USB" in port.description and "Serial" in port.description:
            arduino_ports.append({
                'port': port.device,
                'description': port.description + " (Possible Arduino)"
            })
    
    return arduino_ports

def test_serial_connection(port, baudrate=9600, timeout=2):
    """Test if we can open a serial connection to the port"""
    try:
        # Try to open serial connection
        ser = serial.Serial(port, baudrate, timeout=timeout)
        
        # If we can open it, it's accessible but we don't know if it's an Arduino
        is_open = ser.is_open
        
        # Close the connection
        ser.close()
        
        return is_open
    except Exception as e:
        print(f"Error testing {port}: {str(e)}")
        return False

def test_arduino_communication(port, baudrate=9600, timeout=2):
    """Test if we can communicate with an Arduino on this port"""
    try:
        # Open connection
        ser = serial.Serial(port, baudrate, timeout=timeout)
        
        # Arduino resets when serial connection opens, wait a bit
        time.sleep(2)
        
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Send test command - if it's the Arduino with our sketch, 
        # it should respond to command '1' to turn on the motor
        ser.write(b'1')
        time.sleep(0.5)
        
        # Now turn it off
        ser.write(b'0')
        
        # Try to read response
        response = ser.read(100)
        
        # Close connection
        ser.close()
        
        # If we received any data, assume it's an Arduino
        return len(response) > 0, response
    except Exception as e:
        print(f"Communication error on {port}: {str(e)}")
        return False, str(e)

def rotate_test(port, baudrate=9600, duration=2):
    """Test by actually rotating the motor for a short time"""
    try:
        # Open connection
        ser = serial.Serial(port, baudrate, timeout=2)
        
        # Arduino resets when serial connection opens, wait a bit
        time.sleep(2)
        
        print(f"Turning motor ON for {duration} seconds...")
        
        # Send '1' to turn on
        ser.write(b'1')
        
        # Wait for specified duration
        time.sleep(duration)
        
        print("Turning motor OFF...")
        
        # Send '0' to turn off
        ser.write(b'0')
        
        # Close connection
        time.sleep(0.5)
        ser.close()
        
        return True
    except Exception as e:
        print(f"Rotation test error: {str(e)}")
        return False

def run_comprehensive_test():
    """Run a comprehensive Arduino detection and test"""
    print("Arduino Connection Test")
    print("======================")
    
    # Find potential Arduino ports
    print("\nScanning for Arduino devices...")
    arduino_ports = find_arduino_ports()
    
    if not arduino_ports:
        print("No potential Arduino devices found.")
        print("Is your Arduino connected? Check with 'ls /dev/tty*' or 'dmesg | grep tty'")
        return
    
    print(f"Found {len(arduino_ports)} potential Arduino devices:")
    
    for i, port_info in enumerate(arduino_ports):
        print(f"{i+1}. {port_info['port']} - {port_info['description']}")
        
        # Test if port is accessible
        is_accessible = test_serial_connection(port_info['port'])
        print(f"   - Port accessible: {'Yes' if is_accessible else 'No'}")
        
        if is_accessible:
            # Test if it responds to Arduino communications
            can_communicate, response = test_arduino_communication(port_info['port'])
            print(f"   - Communication test: {'Passed' if can_communicate else 'Failed'}")
            if can_communicate:
                print(f"   - Response received: {response}")
    
    # Ask user which port to test with rotation
    if arduino_ports:
        try:
            choice = input("\nSelect a port to test with motor rotation (enter number, or 'q' to quit): ")
            
            if choice.lower() == 'q':
                return
            
            idx = int(choice) - 1
            if idx >= 0 and idx < len(arduino_ports):
                port = arduino_ports[idx]['port']
                print(f"\nRunning rotation test on {port}...")
                
                duration = float(input("Enter rotation duration in seconds (default: 2): ") or 2)
                success = rotate_test(port, duration=duration)
                
                if success:
                    print(f"\nRotation test successful! Arduino is working correctly on {port}")
                else:
                    print("\nRotation test failed. Check connections and Arduino sketch.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")
        except KeyboardInterrupt:
            print("\nTest aborted.")

if __name__ == "__main__":
    run_comprehensive_test()
