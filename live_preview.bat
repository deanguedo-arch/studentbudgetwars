@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" goto run_game

for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do (
  if exist "%%D\python.exe" (
    set "PYTHON_EXE=%%D\python.exe"
    goto run_game
  )
)

set "PYTHON_EXE=python"
where %PYTHON_EXE% >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python or create a .venv first.
  exit /b 1
)

:run_game
echo Launching After Grad preview...
"%PYTHON_EXE%" -m budgetwars.main --name PreviewPlayer %*
