#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/settings/__init__.py
Initialisiert den Settings-Blueprint
"""

from flask import Blueprint

# Blueprint erstellen
settings_bp = Blueprint('settings', __name__)

# Routen importieren
from app.blueprints.settings import routes
