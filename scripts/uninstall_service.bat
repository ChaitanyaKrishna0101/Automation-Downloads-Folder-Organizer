@echo off
schtasks /delete /tn "SmartDownloadsAutomation" /f
echo Removed
pause