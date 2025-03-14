import os
print("utility/dateien-verzeichnisse-auflisten.py")
print("Die Datei Dateien-Verzeichnisse.md wurde erstellt")

# Pfad des aktuellen Verzeichnisses
current_dir = os.getcwd()

# Datei, in die geschrieben wird
output_file = 'Dateien-Verzeichnisse.md'

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('# Verzeichnisstruktur\n\n')

    for root, dirs, files in os.walk(current_dir):
        # Relativen Pfad erstellen
        rel_path = os.path.relpath(root, current_dir)
        indent_level = rel_path.count(os.sep)
        indent = '  ' * indent_level

        # Verzeichnisse schreiben
        if rel_path != '.':
            f.write(f'{indent}- **{os.path.basename(root)}/**\n')

        # Dateien schreiben
        sub_indent = '  ' * (indent_level + 1)
        for file in files:
            if file != output_file:  # README.md nicht auflisten
                f.write(f'{sub_indent}- {file}\n')
