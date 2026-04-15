import time, shutil, os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.config import DOWNLOADS
from src.db import log_event
from src.ai_classifier import classify_item
from src.logger import log

ROOT_DIR = Path(__file__).parent.parent.resolve()
SCAN_FLAG, RESCUE_FLAG, STOP_FILE = ROOT_DIR/"scan.flag", ROOT_DIR/"rescue.flag", ROOT_DIR/"stop.flag"

PROTECTED = ["PDFs", "WordDocs", "Applications", "Videos", "Audio", "Images", "Archives", "Others", "System_and_Code", "Data"]

def move_logic(item: Path, is_rescue=False):
    if not item.exists() or item.name.startswith(".") or "venv" in item.parts:
        return

    dest_folder = classify_item(item)
    if not dest_folder: return
    
    if item.name in PROTECTED and item.parent == DOWNLOADS: return
    if not is_rescue and item.parent.name == dest_folder: return

    target_dir = (DOWNLOADS / dest_folder).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    
    dest = target_dir / item.name
    if dest.exists() and dest != item:
        dest = target_dir / f"{item.stem}_{int(time.time())}{item.suffix}"

    # RETRY LOGIC: Try 3 times if file is busy (OneDrive sync)
    for attempt in range(3):
        try:
            shutil.move(str(item), str(dest))
            log_event(item.name, str(item.parent), str(dest_folder))
            log(f"✅ Organized: {item.name} -> {dest_folder}")
            return # Success!
        except PermissionError:
            if attempt < 2:
                time.sleep(2) # Wait 2 seconds for OneDrive to finish
                continue
            log(f"⚠️ Skipped: {item.name} is currently in use or syncing.")
        except Exception as e:
            log(f"❌ Error: {e}")
            break

def run_surface():
    log("🔎 Scanning root...")
    try:
        for item in DOWNLOADS.iterdir(): move_logic(item)
    except Exception as e:
        log(f"❌ Scan interrupted: {e}")

def run_rescue():
    log("🚜 Deep Rescue started...")
    for folder in PROTECTED:
        if folder == "Applications": continue
        p = DOWNLOADS/folder
        if p.exists():
            try:
                for f in [x for x in p.iterdir() if x.is_file()]:
                    move_logic(f, True)
            except Exception: continue
    run_surface()
    log("✨ Scan Complete.")

def start_engine():
    observer = Observer()
    handler = type('H', (FileSystemEventHandler,), {'on_created': lambda s, e: move_logic(Path(e.src_path))})()
    observer.schedule(handler, str(DOWNLOADS), recursive=False)
    observer.start()
    
    run_rescue() 
    
    log("📡 Monitoring for new downloads...")
    try:
        while not STOP_FILE.exists():
            if SCAN_FLAG.exists(): run_surface(); SCAN_FLAG.unlink()
            if RESCUE_FLAG.exists(): run_rescue(); RESCUE_FLAG.unlink()
            time.sleep(1)
    except KeyboardInterrupt:
        log("Manual stop.")
    finally:
        observer.stop(); observer.join()