#!/bin/bash
# Dieses Skript ersetzt alle "viewer?" durch "viewer/cloudimage?" im gesamten Projektverzeichnis

PROJECT_DIR="/home/alex/development/drehteller_360_grad_fotos"

echo "=== 360° Viewer URL Korrektur ==="
echo "Suche und ersetze alle 'viewer?' durch 'viewer/cloudimage?' im Projektverzeichnis"

# Backup des gesamten Projekts erstellen
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${PROJECT_DIR}_backup_${TIMESTAMP}"
echo "Erstelle Backup des Projekts: $BACKUP_DIR"
cp -r "$PROJECT_DIR" "$BACKUP_DIR"

# Liste aller Python, HTML und JavaScript Dateien
FILES=$(find "$PROJECT_DIR" -type f \( -name "*.py" -o -name "*.html" -o -name "*.js" \) -not -path "*/\.*" -not -path "*/myenv/*" -not -path "*/backup_*/*")

# Finden und Ersetzen
MODIFIED_COUNT=0
MATCH_COUNT=0

for FILE in $FILES; do
    # Prüfe, ob die Datei das Muster "viewer?" enthält
    if grep -q "viewer?" "$FILE"; then
        MATCH_COUNT=$((MATCH_COUNT+1))
        
        # Backup-Status speichern
        FILE_BEFORE_HASH=$(md5sum "$FILE" | awk '{print $1}')
        
        # Ersetzen durchführen
        sed -i 's|viewer?|viewer/cloudimage?|g' "$FILE"
        
        # Prüfen, ob die Datei geändert wurde
        FILE_AFTER_HASH=$(md5sum "$FILE" | awk '{print $1}')
        if [ "$FILE_BEFORE_HASH" != "$FILE_AFTER_HASH" ]; then
            MODIFIED_COUNT=$((MODIFIED_COUNT+1))
            echo "✅ Geändert: $FILE"
        else
            echo "❌ Keine Änderung in: $FILE (obwohl 'viewer?' gefunden wurde)"
        fi
    fi
done

echo ""
echo "=== Ersetzung abgeschlossen ==="
echo "$MATCH_COUNT Dateien enthielten 'viewer?'"
echo "$MODIFIED_COUNT Dateien wurden geändert"
echo "Backup des kompletten Projekts gespeichert in: $BACKUP_DIR"
echo ""
echo "WICHTIG: Starte den Webserver neu, damit die Änderungen wirksam werden!"
echo "Befehl zum Neustart des Servers:"
echo "----------------------------------------"
echo "cd $PROJECT_DIR"
echo "kill \$(ps aux | grep flask | grep -v grep | awk '{print \$2}')"
echo "FLASK_APP=run.py flask run --host=0.0.0.0"
echo "----------------------------------------"
