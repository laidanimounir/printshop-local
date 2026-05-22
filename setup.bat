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

echo [2/5] Initializing database and creating accounts...
python -c "from app import app; from database import init_db, create_default_workers; from auth import login_manager; login_manager.init_app(app); init_db(app); create_default_workers(); print('Database initialized with default accounts')"
if %errorlevel% neq 0 (
  echo ERROR: Failed to initialize database
  pause
  exit /b 1
)
echo Done.
echo.

echo [3/5] Generating QR Codes...
python qr_generator.py
echo Done.
echo.

echo [4/5] Generating Logo...
python generate_logo.py
echo Done.
echo.

echo [5/5] Setup complete!
echo.
echo ====================================
echo   Default accounts:
echo   Manager: admin / admin123
echo   Workers: worker1/pass1 ... worker4/pass4
echo.
echo   Run start.bat to launch the server
echo ====================================
pause
