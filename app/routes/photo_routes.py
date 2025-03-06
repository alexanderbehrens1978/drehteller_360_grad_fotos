from flask import Blueprint, request, jsonify
from app.services.arduino_service import rotate_teller
from app.services.camera_service import take_photo

photo_bp = Blueprint('photo', __name__)

@photo_bp.route('/rotate', methods=['POST'])
def rotate():
    """Rotiert den Drehteller und macht ein Foto"""
    try:
        # Daten aus der Anfrage holen
        degrees = int(request.form['degrees'])
        
        # Drehteller rotieren
        rotation_success = rotate_teller(degrees)
        if not rotation_success:
            return 'Fehler bei der Rotation', 500
        
        # Foto aufnehmen
        photo = take_photo()
        if not photo:
            return 'Fehler beim Aufnehmen des Fotos', 500
            
        # Erfolg zurückgeben
        return f'/static/photos/{photo}'
    except Exception as e:
        print(f"Fehler bei der Rotation: {e}")
        return str(e), 500
