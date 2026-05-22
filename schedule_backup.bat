@echo off
title LAIDANI PHONE - Schedule Backup
echo ====================================
echo   Schedule Daily Backup
echo ====================================
echo.
echo Registering daily backup at midnight in Task Scheduler...
schtasks /create /tn "LAIDANI_PrintShop_Backup" /tr "python C:\Users\Mounir\Desktop\printshop-local\backup.py" /sc daily /st 00:00 /f
if %errorlevel% equ 0 (
  echo Done! Backup scheduled daily at midnight.
) else (
  echo Failed to schedule. Run as Administrator and try again.
)
pause
