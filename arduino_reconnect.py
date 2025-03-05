#!/usr/bin/env python3
# arduino_reconnect.py - Utility for handling Arduino disconnection/reconnection

import serial
import time
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arduino_reconnect.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("arduino_reconnect")

class ArduinoReconnectManager:
    """Manages reconnection to Arduino after disconnection"""
    
    def __init__(self, port=None, baudrate=9600, timeout=2):
        """Initialize with port and connection parameters"""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.connected = False
        self.last_error_time = 0
        self.error_cooldown = 5  # seconds to wait before retrying after error
        
        # If port is provided, attempt initial connection
        if port:
            self.connect()
    
    def connect(self):
        """Attempt to connect to the Arduino"""
        # Check if enough time has passed since last error
        current_time = time.time()
        if current_time - self.last_error_time < self.error_cooldown:
            logger.debug(f"Still in error cooldown period, not attempting reconnection yet.")
            return False
            
        try:
            # If we already have a connection, close it first
            if self.serial is not None:
                try:
                    self.serial.close()
                except Exception:
                    pass
                self.serial = None
            
            # Create a new serial connection
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Arduino resets when serial connection opens, need to wait
            
            # Test the connection with a ping
            result = self.ping()
            if result:
                logger.info(f"Successfully connected to Arduino on {self.port}")
                self.connected = True
                return True
            else:
                self.disconnect("Ping test failed")
                return False
                
        except Exception as e:
            self.last_error_time = time.time()
            logger.error(f"Connection error: {str(e)}")
            self.connected = False
            self.serial = None
            return False
    
    def ping(self):
        """Send a ping to check if Arduino is responding"""
        if self.serial is None:
            return False
            
        try:
            # Clear any pending data
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Arduino sketch should respond to 'S' command
            self.serial.write(b'S\n')
            time.sleep(0.5)
            
            # Read response (up to 100 bytes to prevent blocking)
            response = self.serial.read(100)
            
            # Check if response contains 'STATUS' which the Arduino sketch sends back
            return b'STATUS' in response
            
        except Exception as e:
            logger.error(f"Ping error: {str(e)}")
            return False
    
    def disconnect(self, reason="User requested"):
        """Disconnect from Arduino"""
        logger.info(f"Disconnecting: {reason}")
        if self.serial:
            try:
                self.serial.close()
            except Exception as e:
                logger.error(f"Error closing serial port: {str(e)}")
            
        self.serial = None
        self.connected = False
    
    def ensure_connection(self):
        """Ensure we have a working connection, try to reconnect if not"""
        if self.connected and self.serial:
            # Test if connection is still valid
            if not self.ping():
                logger.warning("Connection test failed, attempting to reconnect")
                return self.connect()
            return True
        else:
            # Not connected, attempt connection
            return self.connect()
    
    def send_command(self, command):
        """Send a command to the Arduino, ensuring connection first"""
        # First make sure we're connected
        if not self.ensure_connection():
            logger.error("Cannot send command: not connected")
            return False
        
        try:
            # Send the command
            self.serial.write(f"{command}\n".encode())
            
            # Wait for response
            time.sleep(0.5)
            
            # Read response
            response = self.serial.read(100)
            
            # Check for success response
            logger.debug(f"Command response: {response}")
            return b'OK' in response
            
        except Exception as e:
            self.last_error_time = time.time()
            logger.error(f"Error sending command: {str(e)}")
            self.disconnect(f"Error during command: {str(e)}")
            return False
    
    def turn_motor_on(self):
        """Turn motor on (send '1' command)"""
        return self.send_command('1')
    
    def turn_motor_off(self):
        """Turn motor off (send '0' command)"""
        return self.send_command('0')
    
    def rotate_for_duration(self, duration_ms):
        """Rotate the motor for specified duration in milliseconds"""
        if not self.turn_motor_on():
            return False
        
        # Wait for the duration
        time.sleep(duration_ms / 1000.0)
        
        # Turn motor off
        return self.turn_motor_off()


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Arduino reconnection utility')
    parser.add_argument('--port', help='Serial port (e.g., /dev/ttyACM0)', required=True)
    parser.add_argument('--baudrate', type=int, default=9600, help='Baud rate (default: 9600)')
    parser.add_argument('--command', choices=['on', 'off', 'test'], default='test', 
                        help='Command to send (on, off, or test)')
    parser.add_argument('--duration', type=float, default=1.0,
                        help='Duration to run motor in seconds (for test command)')
    
    args = parser.parse_args()
    
    arduino = ArduinoReconnectManager(args.port, args.baudrate)
    
    if args.command == 'on':
        result = arduino.turn_motor_on()
        print(f"Motor on command {'succeeded' if result else 'failed'}")
    elif args.command == 'off':
        result = arduino.turn_motor_off()
        print(f"Motor off command {'succeeded' if result else 'failed'}")
    elif args.command == 'test':
        duration_ms = int(args.duration * 1000)
        print(f"Testing motor rotation for {args.duration} seconds...")
        result = arduino.rotate_for_duration(duration_ms)
        print(f"Test {'succeeded' if result else 'failed'}")
    
    arduino.disconnect()
