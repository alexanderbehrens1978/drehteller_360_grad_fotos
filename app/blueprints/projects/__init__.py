#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/projects/__init__.py
Initialisiert den Projekte-Blueprint
"""

from flask import Blueprint

# Blueprint erstellen
projects_bp = Blueprint('projects', __name__)

# Routen importieren
from app.blueprints.projects import routes
