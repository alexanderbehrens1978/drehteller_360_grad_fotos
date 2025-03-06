from flask import Flask, send_from_directory
import os
import logging

logger = logging.getLogger("drehteller360")

def create_app():
    """
    Erstellt und konfiguriert die Flask-App
    """
    # Bestimme den Basispfad für statische Dateien und Templates
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_folder = os.path.join(base_dir, 'static')
    template_folder = os.path.join(base_dir, 'templates')
    
    logger.info(f"Base Dir: {base_dir}")
    logger.info(f"Static Folder: {static_folder}")
    logger.info(f"Template Folder: {template_folder}")
    
    # Erstelle die Flask-App mit absoluten Pfaden
    app = Flask(__name__, 
                static_folder=static_folder, 
                template_folder=template_folder)
    
    # Stelle sicher, dass die erforderlichen Verzeichnisse existieren
    photos_dir = os.path.join(static_folder, 'photos')
    test_dir = os.path.join(static_folder, 'test')
    
    os.makedirs(photos_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)
    
    logger.info(f"Photos Dir: {photos_dir}")
    
    # Registriere die Blueprints (Routen) mit den korrekten URL-Präfixen
    from app.routes import main_bp, api_bp, device_bp, photo_bp, diagnostic_bp
    
    # Registriere die Blueprints mit korrekten URL-Präfixen
    app.register_blueprint(main_bp)
    
    # Entferne die URL-Präfixe, um mit den bestehenden API-Aufrufen kompatibel zu sein
    app.register_blueprint(api_bp)          # war '/api'
    app.register_blueprint(device_bp)       # war '/devices'
    app.register_blueprint(photo_bp)        # war '/photos'
    app.register_blueprint(diagnostic_bp, url_prefix='/diagnostics')
    
    # Zusätzliche Route für statische Dateien, falls Flask sie nicht korrekt serviert
    @app.route('/static/<path:filename>')
    def custom_static(filename):
        """
        Dient direkt statische Dateien, falls die eingebaute Funktion nicht funktioniert
        """
        logger.info(f"Serving static file: {filename}")
        return send_from_directory(static_folder, filename)
    
    @app.route('/static/photos/<path:filename>')
    def serve_photo(filename):
        """
        Dient speziell Fotos aus dem photos-Unterverzeichnis
        """
        logger.info(f"Serving photo: {filename}")
        return send_from_directory(os.path.join(static_folder, 'photos'), filename)
    
    # Log alle registrierten Routen
    logger.info("Registrierte Routen:")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule}")
    
    return app
