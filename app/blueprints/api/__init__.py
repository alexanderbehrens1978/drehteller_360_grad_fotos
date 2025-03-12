#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/api/__init__.py
Initialisiert den API-Blueprint
"""

from flask import Blueprint

# Blueprint erstellen
api_bp = Blueprint('api', __name__)

# Routen importieren
from app.blueprints.api import routes
