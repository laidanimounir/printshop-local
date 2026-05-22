@echo off
title LAIDANI PHONE - PrintShop Setup
color 0E
echo ====================================
echo   LAIDANI PHONE - PrintShop Setup
echo ====================================
echo.

echo [1/5] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo ERROR: Failed to install dependencies
  pause
  exit /b 1
)
echo Done.
echo.

echo [2/5] Initializing database...
python -c "from app import app; from database import init_db; init_db(app); print('Database created successfully')"
if %errorlevel% neq 0 (
  echo ERROR: Failed to initialize database
  pause
  exit /b 1
)
echo Done.
echo.

echo [3/5] Creating default accounts...
python -c "from app import app; from database import init_db; init_db(app); from database import create_default_workers; create_default_workers(); print('Accounts created')"
echo Done.
echo.

echo [4/5] Generating QR Codes...
python qr_generator.py
echo Done.
echo.

echo [5/5] Generating Logo...
python generate_logo.py
echo Done.
echo.

echo ====================================
echo   Setup Complete!
echo.
echo   Default accounts:
echo   Manager: admin / admin123
echo   Workers: worker1/pass1 ... worker4/pass4
echo.
echo   Run start.bat to launch the server
echo ====================================
pause
