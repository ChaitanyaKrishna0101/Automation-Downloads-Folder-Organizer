from pathlib import Path

CATEGORIES = {
    "WordDocs": [".docx", ".doc", ".txt", ".rtf", ".dotx"],
    "PDFs": [".pdf"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi"],
    "Audio": [".mp3", ".wav", ".aac"],
    "Archives": [".zip", ".rar", ".7z"],
    "Data": [".csv", ".xlsx", ".xls", ".json", ".sql"],
    "Applications": [".exe", ".msi", ".dmg", ".pkg"],
    "System_and_Code": [".py", ".js", ".cpp", ".c", ".h", ".java", ".class", ".html", ".css", ".dll", ".sys"]
}

IGNORE_EXTS = [".tmp", ".crdownload", ".part", ".opdownload"]

def classify_item(item: Path):
    if item.suffix.lower() in IGNORE_EXTS:
        return None 

    if item.is_dir():
        return "Applications"

    ext = item.suffix.lower()
    name = item.name.lower()

    if any(k in name for k in ["invoice", "bill", "report", "resume"]) and ext in [".docx", ".doc"]:
        return "WordDocs"

    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category

    return "Others"