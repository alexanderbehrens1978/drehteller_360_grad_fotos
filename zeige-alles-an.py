import os

def zeige_dateien_und_inhalt(verzeichnis):
    # Durchlaufe rekursiv alle Unterverzeichnisse und Dateien
    for root, dirs, files in os.walk(verzeichnis):
        # Entferne .git aus der Liste der zu durchsuchenden Verzeichnisse
        if '.git' in dirs:
            dirs.remove('.git')
        if 'bin' in dirs:
            dirs.remove('bin')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        if '.idea' in dirs: 
            dirs.remove('.idea')
        if 'myenv' in dirs:
            dirs.remove('myenv')
        for file in files:
            dateipfad = os.path.join(root, file)
            print(f"\n--- Datei: {dateipfad} ---")
            try:
                # Versuche, die Datei im UTF-8 Format zu öffnen
                with open(dateipfad, 'r', encoding='utf-8') as f:
                    inhalt = f.read()
                    print(inhalt)
            except Exception as e:
                print(f"Fehler beim Lesen der Datei: {e}")

# Beispielnutzung
verzeichnis_pfad = "/home/alex/Dokumente/drehteller_360_grad_fotos"  # Hier den gewünschten Pfad angeben
zeige_dateien_und_inhalt(verzeichnis_pfad)

