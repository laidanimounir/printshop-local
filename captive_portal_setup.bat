@echo off
title LAIDANI PHONE - Captive Portal Setup
echo ================================================
echo   CAPTIVE PORTAL SETUP
echo   LAIDANI PHONE PrintShop
echo ================================================
echo.
echo This script helps configure Windows as a WiFi hotspot.
echo.
echo OPTION 1: Use a physical router
echo   Configure your router with:
echo     SSID: LAIDANI_PRINT
echo     Password: laidani2024
echo     LAN IP: 192.168.1.1
echo.
echo OPTION 2: Use Windows Hotspot (requires WiFi adapter)
echo   Run the following commands manually as Administrator:
echo.
echo   netsh wlan set hostednetwork mode=allow ssid=LAIDANI_PRINT key=laidani2024
echo   netsh wlan start hostednetwork
echo.
echo   Then set the hotspot adapter IP to 192.168.1.1
echo.
echo OPTION 3: Use a WiFi router with OpenWrt
echo   Flash OpenWrt on your router and follow:
echo   https://openwrt.org/docs/guide-user/network/wifi/captive_portal
echo.
echo ================================================
echo.
echo After setting up the network, run setup.bat to install
echo the system, then start.bat to run the server.
echo.
pause
