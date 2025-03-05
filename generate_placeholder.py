from PIL import Image, ImageDraw, ImageFont
import os

def generate_placeholder(output_path='static/placeholder.jpg', width=640, height=480):
    """
    Generiert ein Platzhalter-Bild mit Text

    :param output_path: Pfad zum Speichern des Bildes
    :param width: Bildbreite in Pixeln
    :param height: Bildhöhe in Pixeln
    """
    # Stelle sicher, dass der Zielordner existiert
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Erstelle ein neues Bild mit grauem Hintergrund
    image = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)

    # Zeichne Rahmen
    draw.rectangle((0, 0, width-1, height-1), outline=(200, 200, 200), width=2)

    # Füge Text hinzu
    try:
        # Versuche, einen Standardschriftsatz zu laden
        font = ImageFont.load_default()
    except IOError:
        # Fallback auf Standardschriftart
        font = ImageFont.load_default()

    text = "Kein Bild verfügbar"
    text_width = 200  # Ungefähre Textbreite
    text_position = ((width - text_width) // 2, height // 2 - 15)
    draw.text(text_position, text, fill=(100, 100, 100), font=font)

    # Speichere das Bild
    image.save(output_path)
    print(f"Platzhalter-Bild erstellt: {output_path}")

    return output_path

if __name__ == "__main__":
    generate_placeholder()
