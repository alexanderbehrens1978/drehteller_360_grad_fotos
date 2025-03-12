#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/config.py
Konfigurationsklassen für verschiedene Umgebungen
"""

import os
import secrets

class Config:
    """Basis-Konfigurationsklasse"""
    # Grundlegende Konfiguration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    
    # Verzeichnisse
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    PROJECTS_DIR = os.path.join(STATIC_FOLDER, 'projects')
    PHOTOS_DIR = os.path.join(STATIC_FOLDER, 'photos')
    SAMPLE_IMAGES_DIR = os.path.join(STATIC_FOLDER, 'sample_images')
    
    # Drehteller-Standardkonfiguration
    DEFAULT_ROTATION_DEGREES = 15
    DEFAULT_ROTATION_INTERVAL = 5
    
    # Kamera-Standardkonfiguration
    DEFAULT_CAMERA_TYPE = 'webcam'
    DEFAULT_CAMERA_DEVICE = '/dev/video0'
    DEFAULT_RESOLUTION_WIDTH = 1280
    DEFAULT_RESOLUTION_HEIGHT = 720
    
    # Arduino-Standardkonfiguration
    DEFAULT_ARDUINO_PORT = '/dev/ttyACM0'
    DEFAULT_ARDUINO_BAUDRATE = 9600
    
    # Standardeinstellungen für den Simulator
    SIMULATOR_ENABLED = True
    

class DevelopmentConfig(Config):
    """Entwicklungsumgebung-Konfiguration"""
    DEBUG = True
    TESTING = False
    
    # Spezielle Entwicklungseinstellungen
    TEMPLATES_AUTO_RELOAD = True


class ProductionConfig(Config):
    """Produktionsumgebung-Konfiguration"""
    DEBUG = False
    TESTING = False
    
    # Sicherheitseinstellungen für Produktion
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True


class TestingConfig(Config):
    """Testumgebung-Konfiguration"""
    DEBUG = True
    TESTING = True
    
    # Einstellungen für Tests
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    WTF_CSRF_ENABLED = False
