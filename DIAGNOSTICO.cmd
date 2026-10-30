@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PlantView Studio - Diagnostico
set "LOG=%~dp0diagnostico-cmd.txt"
(
 echo PlantView Studio 0.2 - diagnostico
 echo Diretorio: %CD%
 echo Data: %DATE% %TIME%
 echo.
 echo ==== Sistema ====
 ver
 echo.
 echo ==== Leitor DWG ====
 if exist "engine\plantview-dwg.exe" (echo PRESENTE) else (echo AUSENTE)
 echo.
 echo ==== Python ====
 if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" --version
  ".venv\Scripts\python.exe" -c "import importlib.util; names=['PySide6','pyvista','pyvistaqt','cadquery','ifcopenshell','ezdxf','vtk']; [print(x, 'OK' if importlib.util.find_spec(x) else 'AUSENTE') for x in names]"
 ) else (
  echo Ambiente .venv ausente
  where py
  where python
 )
 echo.
 echo ==== GPU detectada pelo Windows ====
 where powershell >nul 2>&1 && powershell -NoProfile -Command "Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,AdapterRAM | Format-List" 
 echo.
 echo Nota: GPU detectada nao comprova que VTK usara essa GPU.
) > "%LOG%" 2>&1
type "%LOG%"
echo.
echo Relatorio salvo em: "%LOG%"
pause
