#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/main/__init__.py
Initialisiert den Haupt-Blueprint
"""

from flask import Blueprint

# Blueprint erstellen
main_bp = Blueprint('main', __name__)

# Routen importieren (nach Blueprint-Erstellung, um Zirkelbezüge zu vermeiden)
from app.blueprints.main import routes
