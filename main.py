import sys, os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
sys.path.append(str(BASE_DIR))

from src.engine import start_engine
from src.logger import log

def main():
    os.chdir(BASE_DIR)
    if (BASE_DIR / "stop.flag").exists():
        (BASE_DIR / "stop.flag").unlink()

    log("🚀 Smart Organizer: Background Service Initiated")
    try:
        start_engine()
    except Exception as e:
        log(f"❌ CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()