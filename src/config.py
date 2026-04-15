from pathlib import Path

DOWNLOADS = Path.home() / "Downloads"

# Strictly separate common types
RULES = {
    ".pdf": "PDFs",
    ".docx": "Documents", ".doc": "Documents", ".txt": "Documents",
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    ".exe": "Applications", ".msi": "Applications", ".jar": "Applications",
    ".dll": "System_and_Code", ".sys": "System_and_Code",
    ".py": "Development", ".js": "Development", ".cpp": "Development",
    ".mp4": "Media", ".mp3": "Media", ".jpg": "Media", ".png": "Media"
}