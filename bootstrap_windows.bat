@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "PYTHON_EXE="

if exist ".venv\Scripts\python.exe" (
  set "PYTHON_EXE=.venv\Scripts\python.exe"
  goto python_found
)

for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do (
  if exist "%%D\python.exe" (
    set "PYTHON_EXE=%%D\python.exe"
    goto python_found
  )
)

where python >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_EXE=python"
  goto python_found
)

echo Python was not found. Attempting per-user Python 3.11 install...
where winget >nul 2>nul
if errorlevel 1 (
  echo winget is not available. Install Python 3.11 manually, then rerun this script.
  exit /b 1
)

winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements --disable-interactivity --override "InstallAllUsers=0 Include_launcher=0 InstallLauncherAllUsers=0 PrependPath=1 Include_test=0 /quiet"

for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do (
  if exist "%%D\python.exe" (
    set "PYTHON_EXE=%%D\python.exe"
    goto python_found
  )
)

where python >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_EXE=python"
  goto python_found
)

echo Python install did not complete. Install Python 3.11 and rerun bootstrap_windows.bat.
exit /b 1

:python_found
echo Using Python: %PYTHON_EXE%

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  "%PYTHON_EXE%" -m venv .venv
  if errorlevel 1 (
    echo Failed to create .venv
    exit /b 1
  )
)

set "VENV_PY=.venv\Scripts\python.exe"

echo Upgrading packaging tooling...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
  echo Failed to upgrade pip/setuptools/wheel.
  exit /b 1
)

echo Installing project dependencies...
"%VENV_PY%" -m pip install -e .[dev]
if errorlevel 1 (
  echo Failed to install project dependencies.
  exit /b 1
)

where cursor >nul 2>nul
if errorlevel 1 goto bootstrap_done

echo Installing Cursor extensions...
cursor --install-extension openai.chatgpt >nul 2>nul
cursor --install-extension ms-python.python >nul 2>nul
cursor --install-extension ms-python.vscode-pylance >nul 2>nul

:bootstrap_done
echo Bootstrap complete.
echo Run the game with live_preview.bat or .venv\Scripts\python.exe -m budgetwars.main --mode classic
exit /b 0
