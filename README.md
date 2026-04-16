📂 FileFlow: Automated Downloads Organizer
FileFlow is a robust Python-based background utility that monitors your system's Downloads folder in real-time. It leverages an intelligent classification engine to automatically sort incoming files into structured directories (Images, Documents, Videos, etc.), eliminating digital clutter without manual intervention.

"Let the system do the boring work!"

📺 Visual Comparison
Before: Files are messy and scattered.

<p align="left">
<img src="https://github.com/user-attachments/assets/1750e68a-3258-4889-b99f-c936e3825cde" width="600" alt="Before">
</p>

After: Files are sorted into clean folders.

<p align="left">
<img src="https://github.com/user-attachments/assets/2fa5015d-950d-41f5-ab06-185c7223c298" width="600" alt="After">
</p>

The Workflow:
1. The system operates through a decoupled architecture to ensure stability and performance. Follow these points strictly for the intended experience:
2. Monitoring: The engine.py process initializes a file system observer that watches for FileCreated or FileMoved events.
3. Classification: Upon detection, the ai_classifier.py analyzes the file extension and metadata to determine its target category.
4. Execution: The engine moves the file to the designated subfolder defined in config.json.
5. Logging: Every transaction is recorded in automation.db and appended to automation.log for audit trails.
6. Visualization: The Streamlit dashboard (app.py) queries the database to display real-time statistics and historical charts.

🛠️ Setup & Installation
Step 1: Clone Repository

Bash
git clone https://github.com/your-username/fileflow.git
cd fileflow
Step 2: Install Requirements

Bash
pip install -r requirements.txt
▶️ Execution Modes
Method 1: Full Automation (Recommended)
Terminal 1: Start Engine

Bash
python src/engine.py
Goal: Runs the background service for real-time monitoring.

Terminal 2: Start Dashboard

Bash
python -m streamlit run ui/app.py
Goal: Launches the UI for manual control and analytics.

Method 2: Manual Control
Single Command:

Bash
python -m streamlit run ui/app.py
Goal: Fast testing without background automation.

✅ Setup Complete: All steps are finished. Your FileFlow organizer is now active and ready to keep your system clean.

Sidebar Controls:
After opening the Streamlit dashboard, look at the left sidebar where you will find the two primary action buttons:

1. Scan & Detect Files
Purpose: It identifies and categorizes files only in the main directory.
Speed: Very fast; ideal for organizing your most recent downloads immediately.

2. Organize & Fix Files
Purpose: It scans through every subfolder to find and fix misplaced files.
Speed: Slower; used for periodic maintenance to ensure no file is left in the wrong place.

📁 Project Structure:
1. src/engine.py       : The core automation engine (File Watchdog).
2. src/ai_classifier.py: Logic for file type determination.
3. src/config.json     : User-defined settings and folder paths.
4. ui/app.py           : Streamlit-based graphical user interface.
5. automation.db       : SQLite database for file history and logs.

Troubleshooting:
1. Service Unresponsive: Ensure engine.py is running in a separate terminal if you expect real-time movement.
2. Module Not Found    : Re-run pip install -r requirements.txt to ensure all libraries are in your environment.
3. Permission Denied   : Ensure the application has read/write access to your designated Downloads folder.
4. Database Error      : Trigger a "Scan & Detect" action via the UI to re-initialize the automation.db file.
