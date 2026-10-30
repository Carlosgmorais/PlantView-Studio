@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute setup-windows.ps1 primeiro. Para a versao pronta, abra PlantViewStudio.exe no pacote Windows.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" run.py
