@echo off
echo ==========================================
echo      Pivot - Build Standalone EXE
echo ==========================================

echo [1/2] Checking/Installing build dependencies...
call uv add --dev pyinstaller pillow

echo.
echo [2/2] Packing application...
call uv run flet pack src/main.py --name pivot --icon src/assets/icon.png --add-data "src/assets;assets" -y

echo.
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b %errorlevel%
)

echo [SUCCESS] Build finished! 
echo The executable is located at: dist\pivot.exe
echo.
