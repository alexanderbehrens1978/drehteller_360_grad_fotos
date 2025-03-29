"""
app/blueprints/viewer/__init__.py
Initialisiert den Viewer-Blueprint
"""

from flask import Blueprint

# Blueprint erstellen
viewer_bp = Blueprint('viewer', __name__, url_prefix='/viewer')

# Routen importieren
from app.blueprints.viewer import routes
