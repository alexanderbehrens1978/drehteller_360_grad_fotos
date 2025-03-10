#!/usr/bin/env python3
"""
Diagnose-Skript für Module-Probleme im 360° Drehteller-System
"""
import sys
import importlib
import traceback

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

def main():
    print(f"Python Version: {sys.version}")
    
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
