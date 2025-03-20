import os
import re
from collections import defaultdict

def get_file_extension_mapping():
    return {
        ".py": r"(^\s*#)",
        ".c": r"(^\s*//)|(/\*.*\*/)",
        ".cpp": r"(^\s*//)|(/\*.*\*/)",
        ".java": r"(^\s*//)|(/\*.*\*/)",
        ".js": r"(^\s*//)|(/\*.*\*/)",
        ".php": r"(^\s*//)|(/\*.*\*/)|(^\s*#)"
    }

def count_lines_in_file(file_path, comment_pattern):
    code_lines = 0
    comment_lines = 0
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                if re.match(comment_pattern, stripped_line):
                    comment_lines += 1
                else:
                    code_lines += 1
    except Exception as e:
        print(f"Fehler beim Lesen von {file_path}: {e}")
    return code_lines, comment_lines

def count_lines_in_project(directory, excluded_dirs):
    file_mapping = get_file_extension_mapping()
    total_code_lines = 0
    total_comment_lines = 0
    language_counts = defaultdict(lambda: {"code": 0, "comments": 0})

    for root, _, files in os.walk(directory):
        if any(excluded in root for excluded in excluded_dirs):
            continue
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in file_mapping:
                file_path = os.path.join(root, file)
                code_lines, comment_lines = count_lines_in_file(file_path, file_mapping[ext])
                total_code_lines += code_lines
                total_comment_lines += comment_lines
                language_counts[ext]["code"] += code_lines
                language_counts[ext]["comments"] += comment_lines
    
    print(f"Gesamte Codezeilen: {total_code_lines}")
    print(f"Gesamte Kommentarzeilen: {total_comment_lines}")
    print("\nDetaillierte Übersicht nach Dateityp:")
    for ext, counts in language_counts.items():
        print(f"{ext}: Codezeilen: {counts['code']}, Kommentarzeilen: {counts['comments']}")

if __name__ == "__main__":
    project_directory = input("Gib das Projektverzeichnis an: ")
    excluded_dirs = input("Gib die auszuschließenden Ordner an (kommagetrennt): ").split(',')
    excluded_dirs = [dir.strip() for dir in excluded_dirs]
    count_lines_in_project(project_directory, excluded_dirs)

