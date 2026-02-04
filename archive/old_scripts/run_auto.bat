@echo off
chcp 65001 >nul
echo ==========================================
echo Job Hunter - Full Auto Mode
echo ==========================================
echo.

set PYTHON=C:\Users\huang\AppData\Local\Programs\Python\Python312\python.exe
set SCRIPT=%~dp0scripts\full_auto_pipeline.py

echo [1/4] Starting auto job hunter...
echo [2/4] Python: %PYTHON%
echo [3/4] Script: %SCRIPT%
echo [4/4] Running...
echo.

%PYTHON% %SCRIPT%

echo.
echo ==========================================
echo Done! Check data/ folder for results.
echo ==========================================
pause
