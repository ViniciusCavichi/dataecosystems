@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 iniciar_windows.py
    pause
    exit /b
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    python iniciar_windows.py
    pause
    exit /b
)
echo Instale o Python 3.10 ou superior em https://www.python.org/downloads/windows/
echo Durante a instalacao, marque "Add python.exe to PATH".
echo Depois feche esta janela e abra INICIAR.bat novamente.
pause
