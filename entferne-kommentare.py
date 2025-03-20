import os
import re
import argparse
import shutil

# Unterstützte Dateitypen und ihre Kommentar-Syntax
COMMENT_PATTERNS = {
    ".py": [r"#.*"],  # Python: Einzeilige Kommentare
    ".js": [r"//.*", r"/\*[\s\S]*?\*/"],  # JavaScript: Einzeilige und mehrzeilige Kommentare
    ".java": [r"//.*", r"/\*[\s\S]*?\*/"],  # Java: Einzeilige und mehrzeilige Kommentare
    ".cpp": [r"//.*", r"/\*[\s\S]*?\*/"],  # C++: Einzeilige und mehrzeilige Kommentare
    ".c": [r"//.*", r"/\*[\s\S]*?\*/"],  # C: Einzeilige und mehrzeilige Kommentare
    ".php": [r"//.*", r"/\*[\s\S]*?\*/", r"#.*"],  # PHP: Einzeilige und mehrzeilige Kommentare
}

def remove_comments_from_code(code, file_extension):
    """Entfernt Kommentare aus Code basierend auf der Dateiendung"""
    if file_extension not in COMMENT_PATTERNS:
        return code  # Falls die Datei nicht unterstützt wird, bleibt sie unverändert

    for pattern in COMMENT_PATTERNS[file_extension]:
        code = re.sub(pattern, "", code, flags=re.MULTILINE)

    return code

def process_file(file_path, backup=True):
    """Verarbeitet eine einzelne Datei und entfernt Kommentare"""
    file_extension = os.path.splitext(file_path)[1]
    
    if file_extension not in COMMENT_PATTERNS:
        return  # Nicht unterstützte Datei überspringen

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    new_content = remove_comments_from_code(content, file_extension)

    if backup:
        shutil.copy(file_path, file_path + ".bak")  # Backup erstellen

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✔ Kommentare entfernt: {file_path}")

def process_directory(directory, backup=True):
    """Durchläuft rekursiv alle Dateien in einem Verzeichnis"""
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            process_file(file_path, backup)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entfernt alle Kommentare aus Code-Dateien")
    parser.add_argument("path", help="Dateipfad oder Ordner")
    parser.add_argument("--no-backup", action="store_true", help="Kein Backup erstellen")

    args = parser.parse_args()
    path = args.path
    backup = not args.no_backup

    if os.path.isfile(path):
        process_file(path, backup)
    elif os.path.isdir(path):
        process_directory(path, backup)
    else:
        print("❌ Fehler: Ungültiger Pfad")

