@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" goto run_game

set "PYTHON_EXE=python"
where %PYTHON_EXE% >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python or create a .venv first.
  exit /b 1
)

:run_game
echo Launching Student Budget Wars preview...
"%PYTHON_EXE%" -m budgetwars.main --name PreviewPlayer --difficulty normal %*
