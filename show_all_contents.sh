#!/bin/bash

DIRECTORY=${1:-.}

# Hier Ordner und Dateien definieren, die ausgeschlossen werden sollen
EXCLUDE_DIRS=(".idea" "venv" ".git" "__pycache__" "bin" "myenv")
EXCLUDE_FILES=("*.log" "*.bin" "*.tmp" "secret.txt" "bootcamp*.*")

# find-Befehl zusammenstellen
FIND_CMD=(find "$DIRECTORY")

# Ordner ausschließen
for dir in "${EXCLUDE_DIRS[@]}"; do
    FIND_CMD+=(-path "*/$dir" -prune -o)
done

# Nur Dateien auswählen
FIND_CMD+=(-type f)

# Dateien ausschließen
for file in "${EXCLUDE_FILES[@]}"; do
    FIND_CMD+=(! -name "$file")
done

# Dateien ausgeben mit absolutem Pfad
"${FIND_CMD[@]}" -print | while read -r file; do
    abs_path=$(realpath "$file")
    echo -e "\n===== Datei: $(basename "$file") ====="
    echo "Pfad: $abs_path"
    echo "===================================\n"
    cat "$file"
done

