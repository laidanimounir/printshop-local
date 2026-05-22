@echo off
title LAIDANI PHONE - PrintShop Server
color 0A
echo ====================================
echo   LAIDANI PHONE - PrintShop Server
echo ====================================
echo.

echo Starting server...
echo.
echo Upload page: http://localhost:5000/upload/PC1
echo Worker Login: http://localhost:5000/worker/login
echo Manager: http://localhost:5000/manager/dashboard
echo.

python server.py
if %errorlevel% neq 0 (
  echo Server stopped with error code %errorlevel%
  pause
)
