from flask import Blueprint, render_template, send_from_directory

main_bp = Blueprint('main',__name__)

@main_bp.route('/')
def index():
    """Hauptseite"""
    return render_template('index.html')

@main_bp.route('/settings')
def settings():
    """Einstellungsseite"""
    return render_template('settings.html')

@main_bp.route('/static/photos/<filename>')
def serve_photo(filename):
    """Liefert ein Foto aus"""
    return send_from_directory('static/photos', filename)

@main_bp.route('/static/test/<filename>')
def serve_test_photo(filename):
    """Liefert ein Testfoto aus"""
    return send_from_directory('static(test',filename)

@main_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Liefert eine statische Datei aus"""
    return send_from_directory('static', filename)
