#!/bin/bash
#
# sh-tracker.sh - Verfolgt alle ausgeführten Dateien, die von einem Shell-Script verwendet werden
#

## Ich habe ein Shell-Script erstellt, das alle Dateien verfolgt, die von einem anderen Shell-Script oder ausführbaren Programm geöffnet oder ausgeführt werden. Es nutzt strace, um alle Systemaufrufe zu überwachen und filtert dann die relevanten Dateizugriffe heraus.
##
## Funktionen des Scripts:
## Verfolgt alle geöffneten und ausgeführten Dateien während der Script-Ausführung
## Erlaubt das Ausschließen bestimmter Verzeichnisse
## Kann die Ergebnisse in eine Datei speichern oder auf dem Terminal ausgeben
## Bietet einen ausführlichen Modus für mehr Informationen während der Ausführung
## Zeigt nur tatsächlich existierende Dateien an
##
## Grundlegende Verwendung
## ./sh-tracker.sh ./run.sh
##
## Mit Ausschluss bestimmter Verzeichnisse
## ./sh-tracker.sh --exclude /usr/lib --exclude /etc ./run.sh
##
## Ausgabe in eine Datei speichern
## ./sh-tracker.sh --output ergebnis.txt ./run.sh
##
## Ausführliche Ausgabe
## ./sh-tracker.sh --verbose ./run.sh
##
## Mit Argumenten für das zu überwachende Script
## ./sh-tracker.sh ./run.sh --parameter wert
## Voraussetzungen:
## Das Script benötigt strace, das auf den meisten Linux-Systemen verfügbar ist
## Unter Ubuntu/Debian kannst du es mit sudo apt-get install strace installieren
## Für andere Distributionen, bitte den entsprechenden Paketmanager verwenden
## So machst du das Script ausführbar:
## chmod +x sh-tracker.sh
## Beachte, dass das Script Systemaufrufe verfolgt und daher einige Systemkenntnisse voraussetzt. Es funktioniert am besten unter Linux. Auf macOS könnte es mit Einschränkungen funktionieren, wenn du strace durch dtruss ersetzt (das erfordert jedoch Root-Rechte).
##
######################################################

set -e

# Funktion für die Ausgabe von Hilfeinformationen
show_help() {
    cat << EOF
Verwendung: $(basename "$0") [OPTIONEN] SCRIPT [SCRIPT_ARGUMENTE]

Verfolgt alle Dateien, die von einem Shell-Script (oder anderen ausführbaren Dateien) 
geöffnet oder ausgeführt werden.

Optionen:
  -h, --help              Diese Hilfe anzeigen
  -e, --exclude ORDNER    Ordner vom Tracking ausschließen (kann mehrfach verwendet werden)
  -o, --output DATEI      Ergebnisse in DATEI speichern (Standard: Ausgabe auf Terminal)
  -v, --verbose           Ausführliche Informationen während des Trackings anzeigen

Beispiel:
  $(basename "$0") --exclude /usr/lib --output ergebnis.txt ./run.sh --parameter wert
EOF
}

# Funktion zum Prüfen, ob ein Pfad in einem der ausgeschlossenen Verzeichnisse liegt
is_excluded() {
    local file_path="$1"
    file_path=$(readlink -f "$file_path" 2>/dev/null || echo "$file_path")
    
    for excluded_dir in "${EXCLUDE_DIRS[@]}"; do
        excluded_dir=$(readlink -f "$excluded_dir" 2>/dev/null || echo "$excluded_dir")
        if [[ "$file_path" == "$excluded_dir"* ]]; then
            return 0  # true, ist ausgeschlossen
        fi
    done
    
    return 1  # false, ist nicht ausgeschlossen
}

# Standard-Werte
SCRIPT=""
OUTPUT=""
VERBOSE=0
EXCLUDE_DIRS=()
SCRIPT_ARGS=()

# Kommandozeilen-Argumente parsen
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--exclude)
            if [[ -z "$2" || "$2" == -* ]]; then
                echo "Fehler: Option $1 erfordert ein Argument." >&2
                exit 1
            fi
            EXCLUDE_DIRS+=("$2")
            shift 2
            ;;
        -o|--output)
            if [[ -z "$2" || "$2" == -* ]]; then
                echo "Fehler: Option $1 erfordert ein Argument." >&2
                exit 1
            fi
            OUTPUT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -*)
            echo "Fehler: Unbekannte Option $1" >&2
            exit 1
            ;;
        *)
            # Erstes Nicht-Option-Argument ist das auszuführende Script
            if [[ -z "$SCRIPT" ]]; then
                SCRIPT="$1"
                shift
            else
                # Alle weiteren Argumente gehören zum Script
                SCRIPT_ARGS+=("$1")
                shift
            fi
            ;;
    esac
done

# Prüfen, ob ein Script angegeben wurde
if [[ -z "$SCRIPT" ]]; then
    echo "Fehler: Kein auszuführendes Script angegeben." >&2
    show_help
    exit 1
fi

# Prüfen, ob das Script existiert und ausführbar ist
if [[ ! -f "$SCRIPT" ]]; then
    echo "Fehler: Die Datei '$SCRIPT' existiert nicht." >&2
    exit 1
fi

if [[ ! -x "$SCRIPT" ]]; then
    echo "Warnung: Die Datei '$SCRIPT' ist nicht als ausführbar markiert." >&2
fi

# Temporäre Datei für die strace-Ausgabe erstellen
STRACE_OUTPUT=$(mktemp)
trap 'rm -f "$STRACE_OUTPUT"' EXIT

# Pfad des Scripts absolut machen
SCRIPT_PATH=$(readlink -f "$SCRIPT")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
SCRIPT_NAME=$(basename "$SCRIPT_PATH")

if [[ $VERBOSE -eq 1 ]]; then
    echo "Starte Tracking für: $SCRIPT_PATH"
    echo "Ausgeschlossene Verzeichnisse:"
    for dir in "${EXCLUDE_DIRS[@]}"; do
        echo "  - $dir"
    done
    echo "Führe Script aus..."
fi

# Script mit strace ausführen, um alle Dateizugriffe zu protokollieren
# Wir erfassen open, openat, execve und stat Systemaufrufe
strace -f -e trace=open,openat,execve,stat -o "$STRACE_OUTPUT" "$SCRIPT_PATH" "${SCRIPT_ARGS[@]}" 2>/dev/null

if [[ $VERBOSE -eq 1 ]]; then
    echo "Script-Ausführung abgeschlossen."
    echo "Verarbeite Dateizugriffe..."
fi

# Die strace-Ausgabe verarbeiten und relevante Dateipfade extrahieren
# Wir suchen nach Mustern wie 'open("pfad/zur/datei", ...' oder 'execve("pfad/zur/datei", ...'
# Wir verwenden ein temporäres assoziatives Array, um Duplikate zu vermeiden
declare -A ACCESSED_FILES

while IFS= read -r line; do
    # Nach Dateipfaden in open/openat/execve/stat-Aufrufen suchen
    if [[ "$line" =~ (open|openat|execve|stat)\(\"([^\"]+)\" ]]; then
        file_path="${BASH_REMATCH[2]}"
        
        # Pfade, die mit / beginnen, sind bereits absolut
        # Andere Pfade sind relativ zum Arbeitsverzeichnis des Prozesses
        if [[ "$file_path" != /* ]]; then
            file_path="$SCRIPT_DIR/$file_path"
        fi
        
        # Nur existierende reguläre Dateien berücksichtigen
        if [[ -f "$file_path" ]]; then
            # Prüfen, ob die Datei in einem ausgeschlossenen Verzeichnis liegt
            if ! is_excluded "$file_path"; then
                ACCESSED_FILES["$file_path"]=1
            fi
        fi
    fi
done < "$STRACE_OUTPUT"

# Ergebnisse sammeln und sortieren
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
RESULTS=("# Dateien verwendet von $SCRIPT_NAME - $TIMESTAMP")
RESULTS+=("# Ausgeführt als: $SCRIPT_PATH ${SCRIPT_ARGS[*]}")
RESULTS+=("")

# Sammle die Dateipfade und sortiere sie
SORTED_FILES=()
for file in "${!ACCESSED_FILES[@]}"; do
    # Konvertiere absolute Pfade zu relativen Pfaden (relativ zum aktuellen Arbeitsverzeichnis)
    rel_path=$(realpath --relative-to="$PWD" "$file" 2>/dev/null || echo "$file")
    SORTED_FILES+=("$rel_path")
done

# Sortiere die Dateien alphabetisch
IFS=$'\n' SORTED_FILES=($(sort <<<"${SORTED_FILES[*]}"))
unset IFS

# Füge die sortierten Dateien zu den Ergebnissen hinzu
for file in "${SORTED_FILES[@]}"; do
    RESULTS+=("$file")
done

# Anzahl der Dateien anhängen
RESULTS+=("")
RESULTS+=("# Insgesamt ${#SORTED_FILES[@]} Dateien gefunden.")

# Ausgabe der Ergebnisse
if [[ -n "$OUTPUT" ]]; then
    # In Datei schreiben
    printf "%s\n" "${RESULTS[@]}" > "$OUTPUT"
    if [[ $VERBOSE -eq 1 ]]; then
        echo "Ergebnisse wurden in '$OUTPUT' gespeichert."
    fi
else
    # Auf Konsole ausgeben
    printf "%s\n" "${RESULTS[@]}"
fi

if [[ $VERBOSE -eq 1 ]]; then
    echo "Tracking abgeschlossen."
fi

exit 0
