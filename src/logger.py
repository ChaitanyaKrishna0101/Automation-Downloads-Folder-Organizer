from datetime import datetime

LOG_FILE = "automation.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"

    print(line)  # show in terminal

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")