#!/usr/bin/env python3
"""
Diagnose-Skript für Module-Probleme im 360° Drehteller-System
"""
import sys
import importlib
import traceback
import subprocess

def test_import(module_name):
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unbekannt")
        print(f"✅ {module_name} erfolgreich importiert (Version: {version})")
        return True
    except ImportError as e:
        print(f"❌ {module_name} konnte nicht importiert werden.")
        print(f"   Fehler: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"⚠️ {module_name} verursacht einen Fehler:")
        print(f"   Fehler: {e}")
        traceback.print_exc()
        return False

def check_libgphoto2():
    try:
        result = subprocess.run(['pkg-config', '--modversion', 'libgphoto2'], 
                                capture_output=True, text=True, check=True)
        print(f"✅ libgphoto2 installiert (Version: {result.stdout.strip()})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ libgphoto2 nicht richtig installiert.")
        print(f"   Fehler: {e}")
        print("   Tipp: Installiere mit 'sudo apt-get install -y libgphoto2-dev pkg-config'")
        return False

def main():
    print(f"Python Version: {sys.version}")
    
    # Prüfe kritische Systembibliotheken
    print("-" * 40)
    print("Prüfe Systembibliotheken...")
    check_libgphoto2()
    print("-" * 40)
    
    modules_to_check = [
        "numpy", 
        "cv2", 
        "flask", 
        "werkzeug", 
        "PIL", 
        "gphoto2"
    ]
    
    for module in modules_to_check:
        test_import(module)
        print("-" * 40)
    
    # Überprüfe OpenCV mit NumPy Interaktion
    try:
        import numpy as np
        import cv2
        # Teste eine einfache Operation mit beiden Modulen
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print("✅ OpenCV kann erfolgreich mit NumPy arbeiten")
    except Exception as e:
        print("❌ OpenCV kann nicht mit NumPy arbeiten")
        print(f"   Fehler: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
