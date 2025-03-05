# git_uploader.py
import os
import subprocess
import argparse
from datetime import datetime


def check_git_installed():
    """Überprüft, ob Git installiert ist"""
    try:
        subprocess.run(['git', '--version'], check=True, stdout=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def init_git_repo(repo_path='.'):
    """Initialisiert ein Git-Repository, falls noch nicht vorhanden"""
    if not os.path.exists(os.path.join(repo_path, '.git')):
        subprocess.run(['git', 'init'], cwd=repo_path, check=True)
        print(f"Git-Repository in {os.path.abspath(repo_path)} initialisiert")
    else:
        print("Git-Repository bereits vorhanden")


def add_remote(repo_path='.', remote_url=None):
    """Fügt eine Remote-URL hinzu, falls noch nicht vorhanden"""
    if not remote_url:
        remote_url = input("Bitte gib die Git-Repository-URL ein: ")

    try:
        # Prüfe, ob origin bereits existiert
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            print(f"Remote 'origin' bereits konfiguriert: {result.stdout.decode().strip()}")
            change = input("Möchtest du die Remote-URL ändern? (j/n): ")
            if change.lower() == 'j':
                subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url], cwd=repo_path, check=True)
                print(f"Remote-URL geändert zu: {remote_url}")
        else:
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url], cwd=repo_path, check=True)
            print(f"Remote 'origin' hinzugefügt: {remote_url}")
    except subprocess.SubprocessError as e:
        print(f"Fehler beim Konfigurieren der Remote-URL: {e}")


def commit_changes(repo_path='.', message=None):
    """Fügt Änderungen hinzu und erstellt einen Commit"""
    if not message:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Automatischer Commit vom {timestamp}"

    # Füge alle Änderungen hinzu
    subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)

    # Erstelle einen Commit
    subprocess.run(['git', 'commit', '-m', message], cwd=repo_path, check=True)
    print(f"Änderungen committed mit Nachricht: '{message}'")


def push_to_remote(repo_path='.', branch='main'):
    """Pusht Änderungen zum Remote-Repository"""
    try:
        subprocess.run(['git', 'push', '-u', 'origin', branch], cwd=repo_path, check=True)
        print(f"Änderungen erfolgreich zu 'origin/{branch}' gepusht")
    except subprocess.SubprocessError as e:
        print(f"Fehler beim Pushen: {e}")
        print("Versuche es mit 'master' statt 'main'...")
        try:
            subprocess.run(['git', 'push', '-u', 'origin', 'master'], cwd=repo_path, check=True)
            print("Änderungen erfolgreich zu 'origin/master' gepusht")
        except subprocess.SubprocessError as e2:
            print(f"Fehler beim Pushen zu 'master': {e2}")
            print("Bitte überprüfe deine Git-Konfiguration und Berechtigungen")


def create_gitignore(repo_path='.'):
    """Erstellt eine .gitignore Datei mit sinnvollen Einträgen"""
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
myenv/
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Flask
instance/
.webassets-cache

# Captured Images and Generated Files
static/photos/*
static/sample_images/*
!static/photos/.gitkeep
!static/sample_images/.gitkeep

# Environment
.env
.venv
env/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS specific
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""

    gitignore_path = os.path.join(repo_path, '.gitignore')

    # Nur erstellen, wenn noch nicht vorhanden
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content.strip())
        print(".gitignore Datei erstellt")
    else:
        print(".gitignore Datei bereits vorhanden")


def main():
    parser = argparse.ArgumentParser(description='Git-Upload für Drehteller-Projekt')
    parser.add_argument('--path', help='Pfad zum Repository', default='.')
    parser.add_argument('--remote', help='Git-Remote-URL')
    parser.add_argument('--message', help='Commit-Nachricht')
    parser.add_argument('--branch', help='Branch zum Pushen', default='main')
    args = parser.parse_args()

    if not check_git_installed():
        print("Git ist nicht installiert. Bitte installiere Git zuerst.")
        return

    # Verzeichnisstruktur sicherstellen
    for directory in ['static/photos', 'static/sample_images']:
        os.makedirs(os.path.join(args.path, directory), exist_ok=True)
        # Leere .gitkeep Dateien erstellen, damit Git leere Verzeichnisse beibehält
        with open(os.path.join(args.path, directory, '.gitkeep'), 'w') as f:
            pass

    init_git_repo(args.path)
    create_gitignore(args.path)
    add_remote(args.path, args.remote)

    try:
        commit_changes(args.path, args.message)
        push_to_remote(args.path, args.branch)
        print("Git-Upload erfolgreich abgeschlossen!")
    except subprocess.SubprocessError as e:
        print(f"Fehler beim Git-Upload: {e}")


if __name__ == "__main__":
    main()