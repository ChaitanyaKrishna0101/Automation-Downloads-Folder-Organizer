📂 FileFlow
👉 Let the system do the boring work

Your Downloads folder gets messy very fast.
Files are everywhere. Finding one file becomes difficult.

FileFlow solves this problem.
🧠 What this project actually does:
Think of it like a small system running in the background.
Whenever a file appears:

It checks the file
Understands what type it is
Moves it to the correct folder

That’s it. Simple and useful.

Why this matters:
No need to manually clean folders
You find files faster
Everything stays organized automatically

⚙️ Setup
Step 1: Download the project
Download ZIP from GitHub
Extract it anywhere (Desktop is fine)
Step 2: Install requirements

Open terminal inside the project folder and run:

pip install -r requirements.txt
▶️ Running the project

There are two ways to run this:

✅ Method 1 (Recommended – Full Automation)

👉 Use two terminals (this is how professionals usually run systems like this for better control and stability)

Terminal 1 → Start Background Engine
python src/engine.py

👉 This runs the background system that watches and organizes files continuously
👉 Keeping this separate helps you monitor logs and debug issues easily

Terminal 2 → Start Dashboard
python -m streamlit run ui/app.py

👉 This opens the dashboard in your browser
👉 Separating UI and engine prevents crashes and keeps things clean

⚡ Method 2 (Simple – Manual Control)
python -m streamlit run ui/app.py

👉 Use this if you just want to test quickly
👉 Not recommended for real usage, because automation won’t run in the background

🎮 How to Use (Important)
🚀 Button: Scan & Detect Files

👉 Click this when:

You want a quick cleanup
You just downloaded files

👉 What it does:

Scans only the main folder
Organizes files instantly

👉 Best practice:
Use this for quick checks instead of running full cleanup every time

🧹 Button: Organize & Fix Files

👉 Click this when:

Your folders are messy
Files are inside subfolders

👉 What it does:

Scans all subfolders
Finds misplaced files
Organizes everything properly

👉 Best practice:
Use this occasionally (not every time) because it scans everything and may take longer

📊 Dashboard

After clicking buttons, you will see:

Number of files processed
Logs of what happened
Charts showing file categories

👉 If nothing updates → action didn’t run properly

❗ Common Issues (Fix Fast)

❌ Python not installed

👉 Install from: https://www.python.org

❌ Module error

Run again: pip install -r requirements.txt

❌ Files not moving / buttons not working

Check:

Correct folder path is set in config.json
engine.py is running (for automatic mode)

❌ Streamlit command not working

👉 Use: python -m streamlit run ui/app.py

❌ Database error

👉 Click Scan & Detect Files once
It will be created automatically

📁 Project Files
src/engine.py → runs the main automation and moves files
src/ai_classifier.py → decides file type (image, pdf, doc, etc.)
src/config.py → stores folder paths and rules
src/config_store.py → saves and loads configuration
src/db.py → handles database operations
src/logger.py → logs all actions and events

ui/app.py → dashboard UI (buttons, stats, charts)

automation.db → stores file history and logs
automation.log → stores runtime logs
config.json → user settings (folders, rules)
main.py → entry point (optional runner)
requirements.txt → required libraries
.gitignore → ignores unnecessary files

⚠️ Important (Don’t Skip)
engine.py → required for automatic file movement
app.py → only handles UI and controls

👉 Professional setup always keeps these separate
Mixing both leads to:
UI freezes
Hard debugging
Unstable behavior

💡 Useful Tips (Real-World Usage):

👉 Run the engine in one terminal and leave it running
👉 Use the dashboard only when you need control or insights

👉 Example:

Terminal 1 → running all day (automation)
Terminal 2 → open when needed (UI)

👉 Start small:

Test with a few files first
Then use it on full folders
⚡ Reality Check

Most beginners:

Run everything in one place ❌
Don’t monitor logs ❌

Better approach:

Separate processes ✅
Observe behavior ✅
Control via UI when needed ✅