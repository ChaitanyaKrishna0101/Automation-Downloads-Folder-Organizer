@echo off
schtasks /create /tn "SmartDownloadsAutomation" /tr "python %cd%\service.py" /sc onlogon /rl highest
echo Installed
pause