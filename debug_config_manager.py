#!/usr/bin/env python3
"""
Debug script to test the configuration manager and diagnose saving issues
"""

import os
import json
import sys

# Import the config manager from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_manager import config_manager

def print_section_header(title):
    """Print a section header for better readability"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50)

def check_file_permissions(filepath):
    """Check permissions for a file or its directory if it doesn't exist"""
    if os.path.exists(filepath):
        # Check if the file is readable
        readable = os.access(filepath, os.R_OK)
        # Check if the file is writable
        writable = os.access(filepath, os.W_OK)
        
        print(f"File: {filepath}")
        print(f"  Exists: Yes")
        print(f"  Readable: {'Yes' if readable else 'No'}")
        print(f"  Writable: {'Yes' if writable else 'No'}")
        
        # Get file permissions in octal format
        permissions = oct(os.stat(filepath).st_mode)[-3:]
        print(f"  Permissions: {permissions}")
        
        # Get owner info
        import pwd
        import grp
        stat_info = os.stat(filepath)
        uid = stat_info.st_uid
        gid = stat_info.st_gid
        
        try:
            user = pwd.getpwuid(uid)[0]
            group = grp.getgrgid(gid)[0]
            print(f"  Owner: {user}:{group}")
        except KeyError:
            print(f"  Owner: {uid}:{gid}")
    else:
        # File doesn't exist, check directory
        dirpath = os.path.dirname(filepath)
        
        if not os.path.exists(dirpath):
            print(f"File: {filepath}")
            print(f"  Directory {dirpath} does not exist!")
            return
        
        # Check if the directory is writable
        writable = os.access(dirpath, os.W_OK)
        
        print(f"File: {filepath}")
        print(f"  Exists: No")
        print(f"  Directory writable: {'Yes' if writable else 'No'}")
        
        # Get directory permissions
        permissions = oct(os.stat(dirpath).st_mode)[-3:]
        print(f"  Directory permissions: {permissions}")
        
        # Get owner info
        import pwd
        import grp
        stat_info = os.stat(dirpath)
        uid = stat_info.st_uid
        gid = stat_info.st_gid
        
        try:
            user = pwd.getpwuid(uid)[0]
            group = grp.getgrgid(gid)[0]
            print(f"  Directory owner: {user}:{group}")
        except KeyError:
            print(f"  Directory owner: {uid}:{gid}")

def test_config_manager():
    """Test the configuration manager's functionality"""
    print_section_header("CONFIG MANAGER INFO")
    print(f"Config path: {config_manager.config_path}")
    print(f"Project directory: {config_manager.project_dir}")
    
    print_section_header("FILE PERMISSIONS")
    check_file_permissions(config_manager.config_path)
    
    print_section_header("CURRENT CONFIG")
    print(json.dumps(config_manager.config, indent=2))
    
    print_section_header("TESTING CONFIG SAVE")
    # Create a test config (same as current, but with a test flag)
    test_config = config_manager.config.copy()
    test_config['_test_flag'] = True
    
    # Try to save
    try:
        success = config_manager.save_config(test_config)
        print(f"Save result: {'Success' if success else 'Failure'}")
    except Exception as e:
        print(f"Save exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if file exists after save attempt
    if os.path.exists(config_manager.config_path):
        print("\nReading saved config file content:")
        try:
            with open(config_manager.config_path, 'r') as f:
                saved_content = f.read()
            
            # Check if content is valid JSON
            try:
                saved_json = json.loads(saved_content)
                print("Content is valid JSON.")
                
                # Check if test flag is present
                if '_test_flag' in saved_json:
                    print("Test flag found - save was successful!")
                else:
                    print("Test flag not found - save might have failed or used wrong file.")
            except json.JSONDecodeError:
                print("Content is not valid JSON!")
                print(f"File content (first 500 chars): {saved_content[:500]}")
        except Exception as e:
            print(f"Error reading saved file: {e}")
    else:
        print("\nConfig file still doesn't exist after save attempt!")

def test_direct_write():
    """Test direct file writing without using config_manager"""
    print_section_header("TESTING DIRECT FILE WRITE")
    test_filename = os.path.join(os.path.dirname(config_manager.config_path), 'test_write.json')
    
    test_data = {"test": "data", "number": 123}
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(test_filename), exist_ok=True)
        
        # Try to write directly
        with open(test_filename, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        print(f"Successfully wrote test file: {test_filename}")
        
        # Verify content
        with open(test_filename, 'r') as f:
            read_content = json.load(f)
        
        if read_content == test_data:
            print("File contents match expected data.")
        else:
            print(f"File contents don't match! Content: {read_content}")
    except Exception as e:
        print(f"Direct write failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up test file
    try:
        if os.path.exists(test_filename):
            os.remove(test_filename)
            print(f"Test file removed: {test_filename}")
    except Exception as e:
        print(f"Could not remove test file: {e}")

def main():
    """Run all tests"""
    print_section_header("SYSTEM INFO")
    import platform
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"User: {os.getlogin()}")
    print(f"Current directory: {os.getcwd()}")
    
    # Run tests
    test_config_manager()
    test_direct_write()
    
    print_section_header("DONE")

if __name__ == "__main__":
    main()
